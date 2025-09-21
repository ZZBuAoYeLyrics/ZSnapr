import os
import ctypes
import sys

# Set process DPI awareness as early as possible (Per-Monitor V2), with fallbacks
try:
    # PER_MONITOR_AWARE_V2 = -4 on Windows 10+
    if hasattr(ctypes.windll, "user32"):
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# Normalize Qt scale environment to avoid mismatched coordinates
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
os.environ['QT_SCALE_FACTOR'] = '1'
os.environ['QT_SCREEN_SCALE_FACTORS'] = '1'
os.environ['QT_DEVICE_PIXEL_RATIO'] = '1'

import flet as ft
import threading
import keyboard
from screenshot_engine import ScreenshotEngine
from config import APP_NAME, APP_VERSION, DEFAULT_SETTINGS, HOTKEYS, SUPPORTED_FORMATS, save_hotkeys
from modules.copy_legacy import ClipboardManager
from modules.save_legacy import SaveManager
import pystray
from PIL import Image, ImageDraw
import queue
from ui.pages import capture_page, settings_page, about_page, home_page
from core.hotkeys import register as register_hotkeys, re_register as re_register_hotkeys
from core.tray import TrayManager
from core.log_sys import get_logger, LogOperation, auto_cleanup_logs, CleanupStrategy


class ZSnaprApp:
    def __init__(self):
        # Initialize logger first
        self.logger = get_logger()
        self.logger.info("Initializing ZSnaprApp")
        
        # Silent automatic log cleanup on startup
        self._silent_log_cleanup()
        
        self.engine = ScreenshotEngine()
        self.clipboard_manager = ClipboardManager()
        self.save_manager = SaveManager(DEFAULT_SETTINGS["save_directory"])
        
        self.page = None
        self.status_text = None
        self.preview_image = None
        self.last_screenshot = None
        self.last_filepath = None
        
        # UI components
        self.save_dir_field = None
        self.format_dropdown = None
        self.delay_field = None
        self.auto_save_checkbox = None
        self.tabs = None
        self.tray_manager = TrayManager(self)
        self.is_compact = False
        
        self.logger.info("ZSnaprApp initialization completed")
    
    def _silent_log_cleanup(self):
        # Automatic log cleanup with informative logging
        try:
            import threading
            import time
            
            def cleanup_worker():
                try:
                    # Wait a moment for app to fully initialize
                    time.sleep(0.5)
                    
                    # Perform cleanup with detailed logging (AGGRESSIVE mode)
                    result = auto_cleanup_logs(CleanupStrategy.AGGRESSIVE)
                    
                    if result.get("status") == "success":
                        deleted_count = len(result.get("deleted_files", []))
                        files_before = result.get("files_before", 0)
                        files_after = result.get("files_after", 0)
                        mb_freed = result.get("mb_freed", 0)
                        
                        if deleted_count > 0:
                            self.logger.info(f"日志清理完成: 删除了 {deleted_count} 个旧日志文件")
                            self.logger.info(f"清理前: {files_before} 个文件, 清理后: {files_after} 个文件")
                            if mb_freed > 0:
                                self.logger.info(f"释放空间: {mb_freed:.2f} MB")
                        else:
                            self.logger.info("日志清理检查完成: 无需删除文件")
                    elif result.get("status") == "no_cleanup_needed":
                        self.logger.info("日志清理检查: 当前日志文件数量正常，无需清理")
                    else:
                        self.logger.warning(f"日志清理状态: {result.get('status', 'unknown')}")
                    
                except Exception as e:
                    self.logger.error(f"日志清理失败: {e}")
            
            # Run cleanup in background thread to avoid blocking startup
            cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            cleanup_thread.start()
            
        except Exception as e:
            self.logger.error(f"启动日志清理线程失败: {e}")
        
    def main(self, page: ft.Page):
        self.page = page
        page.title = f"{APP_NAME} v{APP_VERSION}"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window.width = 939
        page.window.height = 597
        page.window.min_width = 500
        page.window.min_height = 350
        page.window.center()
        page.window.visible = True
        page.window_resizable = True
        page.scroll = ft.ScrollMode.HIDDEN
        page.window.title_bar_hidden = True
        page.window.title_bar_buttons_hidden = True
        
        # Use built-in Flet Material icons (no external font needed)
        
        # Set up cleanup on window close
        page.window.on_window_event = self._on_window_event
        
        # Initialize UI
        self._setup_ui()

        # Responsive handler
        self.page.on_resize = self._on_resize
        
        # Setup global hotkeys
        self._setup_hotkeys()
        
        # Start tray action checker
        self._start_tray_checker()
        
        page.update()
    
    def _setup_ui(self):
        """Setup the user interface with tabs"""
        compact = (self.page.width or 0) < 560 if self.page else False
        self.is_compact = compact
        header_icon_size = 18 if compact else 20
        header_text_size = 13 if compact else 14
        header_spacing = 8 if compact else 10
        header_padding_v = 6 if compact else 8
        header_padding_h = 8 if compact else 10
        # Create tabs with controlled scrolling and responsive width
        tabs_height = max(250, (self.page.height or 411) - 150) if self.page else 250
        self.tabs = ft.Container(
            content=ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        text="Home",
                        icon=ft.Icons.HOME,
                        content=ft.ListView(
                            controls=[home_page.build(self)],
                            expand=True,
                            auto_scroll=False
                        )
                    ),
                    ft.Tab(
                        text="Capture",
                        icon=ft.Icons.CAMERA_ALT,
                        content=ft.ListView(
                            controls=[capture_page.build(self)],
                            expand=True,
                            auto_scroll=False
                        )
                    ),
                    ft.Tab(
                        text="Settings",
                        icon=ft.Icons.SETTINGS,
                        content=ft.ListView(
                            controls=[settings_page.build(self)],
                            expand=True,
                            auto_scroll=False
                        )
                    ),
                    ft.Tab(
                        text="About",
                        icon=ft.Icons.INFO,
                        content=ft.ListView(
                            controls=[about_page.build(self)],
                            expand=True,
                            auto_scroll=False
                        )
                    ),
                ]
            ),
            height=tabs_height,
            expand=False
        )
        
        # Status bar
        self.status_text = ft.Text("Ready to capture", color=ft.Colors.GREEN_700, size=12, weight=ft.FontWeight.W_500)
        status_bar = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.GREEN_500),
                    margin=ft.margin.only(right=8)
                ),
                self.status_text
            ], spacing=0),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200)
        )
        
        # Enhanced Header with Material Design
        header = ft.Container(
            content=ft.Row([
                ft.WindowDragArea(
                    content=ft.Row([
                        # App icon with gradient effect
                        ft.Container(
                            content=ft.Stack([
                                ft.Container(
                                    width=32,
                                    height=32,
                                    bgcolor=ft.Colors.BLUE_600,
                                    border_radius=8,
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CAMERA_ALT, size=header_icon_size, color=ft.Colors.WHITE),
                                    alignment=ft.alignment.center,
                                    width=32,
                                    height=32,
                                )
                            ]),
                        ),
                        # App title with enhanced typography
                        ft.Column([
                            ft.Text(f"{APP_NAME}", size=header_text_size + 1, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                            ft.Text(f"v{APP_VERSION}", size=header_text_size - 2, color=ft.Colors.BLUE_600, weight=ft.FontWeight.W_400),
                        ], spacing=0, tight=True),
                    ], spacing=header_spacing + 2, alignment=ft.MainAxisAlignment.START),
                    expand=True
                ),
                # Enhanced toolbar with Material Design buttons - Fixed alignment
                ft.Row([
                    # Quick capture buttons with Material Design icons - Improved alignment
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.FULLSCREEN, size=16, color=ft.Colors.BLUE_600),
                                    ft.Text("Full", size=9, color=ft.Colors.BLUE_600, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                                tooltip="Fullscreen Capture (Ctrl+Shift+F)",
                                on_click=self._capture_fullscreen,
                                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                                border_radius=8,
                                bgcolor=ft.Colors.TRANSPARENT,
                                ink=True,
                                on_hover=lambda e: self._on_toolbar_hover(e, ft.Colors.BLUE_50)
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.CROP_FREE, size=16, color=ft.Colors.GREEN_600),
                                    ft.Text("Region", size=9, color=ft.Colors.GREEN_600, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                                tooltip="Region Capture (Ctrl+Shift+R)",
                                on_click=self._capture_region,
                                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                                border_radius=8,
                                bgcolor=ft.Colors.TRANSPARENT,
                                ink=True,
                                on_hover=lambda e: self._on_toolbar_hover(e, ft.Colors.GREEN_50)
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.WINDOW, size=16, color=ft.Colors.PURPLE_600),
                                    ft.Text("Window", size=9, color=ft.Colors.PURPLE_600, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                                tooltip="Window Capture (Ctrl+Shift+W)",
                                on_click=self._capture_window,
                                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                                border_radius=8,
                                bgcolor=ft.Colors.TRANSPARENT,
                                ink=True,
                                on_hover=lambda e: self._on_toolbar_hover(e, ft.Colors.PURPLE_50)
                            ),
                        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=10,
                        border=ft.border.all(1, ft.Colors.GREY_200)
                    ),
                    # Separator
                    ft.Container(
                        width=1,
                        height=24,
                        bgcolor=ft.Colors.GREY_300,
                        margin=ft.margin.symmetric(horizontal=8)
                    ),
                    # Window controls
                    ft.IconButton(
                        icon=ft.Icons.AUTO_AWESOME,
                        icon_color=ft.Colors.RED_600,
                        icon_size=18,
                        tooltip="Minimize to Tray",
                        on_click=self._minimize_to_tray,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            bgcolor={
                                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                                ft.ControlState.HOVERED: ft.Colors.RED_50
                            },
                            overlay_color={
                                ft.ControlState.PRESSED: ft.Colors.RED_100
                            }
                        )
                    ),
                ], spacing=4, alignment=ft.MainAxisAlignment.END)
            ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=header_padding_v + 2, horizontal=header_padding_h + 2),
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLUE_300),
                offset=ft.Offset(0, 3)
            )
        )
        
        # Main layout with controlled scrolling
        main_content = ft.ListView(
            controls=[
                header,
                ft.Container(height=12),  # spacing
                self.tabs,
                ft.Container(height=12),  # spacing
                status_bar
            ],
            expand=True,
            spacing=0,
            auto_scroll=False
        )
        
        self.page.add(
            ft.Container(
                content=main_content,
                padding=15
            )
        )
    
    def _setup_hotkeys(self):
        # Delegate to core.hotkeys
        register_hotkeys(self)
    
    def _on_resize(self, e):
        try:
            new_compact = (self.page.width or 0) < 560
            if new_compact != getattr(self, "is_compact", False):
                sel = self.tabs.selected_index if self.tabs else 0
                self.page.controls.clear()
                self._setup_ui()
                if self.tabs:
                    self.tabs.selected_index = sel
                self.page.update()
        except Exception:
            pass

    def _update_status(self, message, color=ft.Colors.BLACK):
        """Update status message"""
        if self.status_text:
            self.status_text.value = message
            self.status_text.color = color
            self.page.update()
    
    def _capture_fullscreen(self, e=None):
        """Capture full screen"""
        self._update_status("Capturing full screen...", ft.Colors.BLUE)
        
        def capture():
            try:
                screenshot = self.engine.capture_fullscreen()
                self._process_screenshot(screenshot, "fullscreen")
            except Exception as ex:
                self._update_status(f"Error: {str(ex)}", ft.Colors.RED)
        
        threading.Thread(target=capture, daemon=True).start()
    
    def _capture_region(self, e=None):
        """Capture selected region"""
        with LogOperation("Region Capture"):
            self.logger.log_screenshot_event("REGION_CAPTURE_START")
            self._update_status("Select region on screen...", ft.Colors.BLUE)
            
            def capture():
                self.logger.log_thread_info("Region capture thread started")
                try:
                    self.logger.debug("Calling engine.capture_region()")
                    result = self.engine.capture_region()
                    self.logger.debug(f"Engine returned: {type(result)} - {result is not None}")
                    
                    if result:
                        self.logger.log_screenshot_event("REGION_CAPTURE_SUCCESS", f"Result type: {type(result)}")
                        self._process_screenshot(result, "region")
                    else:
                        self.logger.log_screenshot_event("REGION_CAPTURE_CANCELLED")
                        self._update_status("Region selection cancelled", ft.Colors.ORANGE)
                except Exception as ex:
                    self.logger.log_screenshot_event("REGION_CAPTURE_ERROR", str(ex))
                    self.logger.exception("Region capture exception:")
                    self._update_status(f"Error: {str(ex)}", ft.Colors.RED)
                finally:
                    self.logger.log_thread_info("Region capture thread finished")
            
            self.logger.debug("Starting region capture thread")
            threading.Thread(target=capture, daemon=True).start()
    
    def _capture_window(self, e=None):
        """Capture active window"""
        self._update_status("Capturing active window...", ft.Colors.BLUE)
        
        def capture():
            try:
                screenshot = self.engine.capture_window()
                self._process_screenshot(screenshot, "window")
            except Exception as ex:
                self._update_status(f"Error: {str(ex)}", ft.Colors.RED)
        
        threading.Thread(target=capture, daemon=True).start()
    
    def _process_screenshot(self, screenshot, capture_type):
        """Process captured screenshot"""
        if screenshot is None:
            self._update_status("Screenshot capture failed", ft.Colors.RED)
            return
            
        action = None
        if isinstance(screenshot, tuple) and len(screenshot) == 2 and isinstance(screenshot[1], str):
            screenshot, action = screenshot
        
        self.last_screenshot = screenshot
        
        if capture_type == "region" and action == "copy":
            try:
                ok = self.clipboard_manager.copy_image_to_clipboard(screenshot)
                if ok:
                    self._update_status("Region copied to clipboard", ft.Colors.GREEN)
                else:
                    self._update_status("Failed to copy to clipboard", ft.Colors.RED)
            except Exception as e:
                self._update_status(f"Clipboard error: {str(e)}", ft.Colors.RED)
            if self.page:
                self.page.update()
            return
        
        if capture_type == "region" and action == "save":
            try:
                filepath = self.save_manager.save_as_dialog(self.last_screenshot)
                if filepath:
                    self.last_filepath = filepath
                    self._update_status(f"Screenshot saved: {os.path.basename(filepath)}", ft.Colors.GREEN)
                else:
                    self._update_status("Save cancelled", ft.Colors.ORANGE)
            except Exception as e:
                self._update_status(f"Save error: {str(e)}", ft.Colors.RED)
            if self.page:
                self.page.update()
            return
        
        # Check for auto-copy settings
        should_auto_copy = False
        if capture_type == "fullscreen" and hasattr(self, 'auto_copy_fullscreen_checkbox') and self.auto_copy_fullscreen_checkbox.value:
            should_auto_copy = True
        elif capture_type == "window" and hasattr(self, 'auto_copy_window_checkbox') and self.auto_copy_window_checkbox.value:
            should_auto_copy = True
        
        # Auto-copy if enabled
        if should_auto_copy:
            try:
                ok = self.clipboard_manager.copy_image_to_clipboard(screenshot)
                if ok:
                    self._update_status(f"{capture_type.title()} screenshot copied to clipboard", ft.Colors.GREEN)
                else:
                    self._update_status("Failed to copy to clipboard", ft.Colors.RED)
            except Exception as e:
                self._update_status(f"Clipboard error: {str(e)}", ft.Colors.RED)
        
        # Auto-save if enabled
        if self.auto_save_checkbox and self.auto_save_checkbox.value:
            try:
                filepath = self.save_manager.quick_save(
                    screenshot, 
                    self.save_dir_field.value if self.save_dir_field else DEFAULT_SETTINGS["save_directory"],
                    self.format_dropdown.value if self.format_dropdown else DEFAULT_SETTINGS["image_format"]
                )
                if filepath:
                    self.last_filepath = filepath
                    status_msg = f"Screenshot saved: {os.path.basename(filepath)}"
                    if should_auto_copy:
                        status_msg += " and copied to clipboard"
                    self._update_status(status_msg, ft.Colors.GREEN)
                else:
                    self._update_status("Failed to save screenshot", ft.Colors.RED)
            except Exception as e:
                self._update_status(f"Save error: {str(e)}", ft.Colors.RED)
        elif not should_auto_copy:
            self._update_status("Screenshot captured (not saved)", ft.Colors.BLUE)
        
        if self.page:
            self.page.update()
    
    def _apply_settings(self, e):
        """Apply current settings"""
        try:
            # Update engine settings
            self.engine.set_save_directory(self.save_dir_field.value)
            self.engine.set_image_format(self.format_dropdown.value)
            self.engine.set_delay(float(self.delay_field.value or 0))
            self.engine.auto_save = self.auto_save_checkbox.value

            # Update save manager
            self.save_manager.default_directory = self.save_dir_field.value

            # Apply hotkeys if fields exist
            new_hotkeys = None
            if hasattr(self, "fullscreen_hotkey_field") and hasattr(self, "region_hotkey_field") and hasattr(self, "window_hotkey_field"):
                f = (self.fullscreen_hotkey_field.value or "").strip()
                r = (self.region_hotkey_field.value or "").strip()
                w = (self.window_hotkey_field.value or "").strip()
                if f and r and w:
                    new_hotkeys = {"fullscreen": f, "region": r, "window": w}

            if new_hotkeys:
                save_hotkeys(new_hotkeys)
                re_register_hotkeys(self, new_hotkeys)
                self._refresh_hotkey_labels()

            self._update_status("Settings applied successfully", ft.Colors.GREEN)
            self._show_snackbar("Settings applied successfully", ft.Colors.GREEN_600)
            self._show_dialog("Settings", "Settings applied successfully", modal=False)
            try:
                if self.tabs and self.tabs.tabs and len(self.tabs.tabs) > 0:
                    self.tabs.tabs[0].content = home_page.build(self)
            except Exception:
                pass
            if self.page:
                self.page.update()
        except Exception as ex:
            self._update_status(f"Settings error: {str(ex)}", ft.Colors.RED)
            self._show_snackbar(f"Settings error: {str(ex)}", ft.Colors.RED_600)
            if self.page:
                self.page.update()
    
    def _browse_directory(self, e):
        """Browse for save directory"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            
            directory = filedialog.askdirectory(
                initialdir=self.save_dir_field.value,
                title="Select Save Directory"
            )
            
            root.destroy()
            
            if directory:
                self.save_dir_field.value = directory
                self.page.update()
                self._update_status("Directory updated", ft.Colors.GREEN)
                
        except Exception as ex:
            self._update_status(f"Directory selection error: {str(ex)}", ft.Colors.RED)
    
    def _save_as(self, e):
        """Save screenshot with custom name"""
        if self.last_screenshot:
            try:
                filepath = self.save_manager.save_as_dialog(self.last_screenshot)
                if filepath:
                    self.last_filepath = filepath
                    self._update_status(f"Screenshot saved as: {os.path.basename(filepath)}", ft.Colors.GREEN)
                else:
                    self._update_status("Save cancelled", ft.Colors.ORANGE)
            except Exception as ex:
                self._update_status(f"Save error: {str(ex)}", ft.Colors.RED)
        else:
            self._update_status("No screenshot to save", ft.Colors.ORANGE)
    
    def _copy_to_clipboard(self, e):
        """Copy screenshot to clipboard"""
        if self.last_screenshot:
            try:
                success = self.clipboard_manager.copy_image_to_clipboard(self.last_screenshot)
                if success:
                    self._update_status("Screenshot copied to clipboard", ft.Colors.GREEN)
                else:
                    self._update_status("Failed to copy to clipboard", ft.Colors.RED)
            except Exception as ex:
                self._update_status(f"Clipboard error: {str(ex)}", ft.Colors.RED)
        else:
            self._update_status("No screenshot to copy", ft.Colors.ORANGE)
    
    def _open_folder(self, e):
        """Open save folder"""
        try:
            folder_path = self.save_dir_field.value
            if self.last_filepath:
                folder_path = os.path.dirname(self.last_filepath)
            
            os.startfile(folder_path)
            self._update_status("Opened save folder", ft.Colors.GREEN)
        except Exception as ex:
            self._update_status(f"Error opening folder: {str(ex)}", ft.Colors.RED)
    
    # Hotkey handlers
    def _hotkey_fullscreen(self):
        """Hotkey handler for fullscreen capture"""
        if self.page:
            self._capture_fullscreen()
    
    def _hotkey_region(self):
        """Hotkey handler for region capture"""
        self.logger.log_hotkey_event("ctrl+shift+r", "region_capture")
        if self.page:
            self.logger.debug("Page exists, calling _capture_region")
            self._capture_region()
        else:
            self.logger.warning("Page is None, cannot capture region")
    
    def _hotkey_window(self):
        """Hotkey handler for window capture"""
        if self.page:
            self._capture_window()

    def _refresh_hotkey_labels(self):
        # Rebuild capture page to reflect latest hotkeys
        try:
            if self.tabs and self.tabs.tabs and len(self.tabs.tabs) > 1:
                self.tabs.tabs[1].content = capture_page.build(self)
                if self.page:
                    self.page.update()
        except Exception:
            pass

    def _record_hotkey(self, target):
        # Capture a hotkey combo and put it into corresponding field
        self._update_status("Press the desired hotkey...", ft.Colors.BLUE)
        def worker():
            try:
                combo = keyboard.read_hotkey(suppress=True)
                if target == "fullscreen" and hasattr(self, "fullscreen_hotkey_field"):
                    self.fullscreen_hotkey_field.value = combo
                elif target == "region" and hasattr(self, "region_hotkey_field"):
                    self.region_hotkey_field.value = combo
                elif target == "window" and hasattr(self, "window_hotkey_field"):
                    self.window_hotkey_field.value = combo
                if self.page:
                    self.page.update()
                self._update_status("Hotkey captured", ft.Colors.GREEN)
            except Exception as ex:
                self._update_status(f"Hotkey capture failed: {str(ex)}", ft.Colors.RED)
        threading.Thread(target=worker, daemon=True).start()

    def _show_snackbar(self, message, bgcolor=ft.Colors.BLUE_600):
        try:
            if not self.page:
                return
            
            # Simple responsive configuration
            is_compact = getattr(self, 'is_compact', False)
            text_size = 12 if is_compact else 13
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    message, 
                    color=ft.Colors.WHITE,
                    size=text_size,
                    weight=ft.FontWeight.W_500
                ),
                bgcolor=bgcolor,
                behavior=ft.SnackBarBehavior.FLOATING
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass

    def _show_dialog(self, title, message, modal=False):
        try:
            if not self.page:
                return
            dlg = ft.AlertDialog(
                modal=modal,
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda e: self.page.close(dlg))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.open(dlg)
        except Exception:
            pass

    # Delegate all tray operations to TrayManager
    def _minimize_to_tray(self, e=None):
        self.tray_manager.minimize_to_tray()
    def _start_tray_checker(self):
        self.tray_manager.start_checker()
    def _restore_from_tray(self):
        self.tray_manager.restore_from_tray()
    def _on_tray_click(self):
        self.tray_manager.on_tray_click()
    def _on_tray_restore(self):
        self.tray_manager.on_tray_restore()
    def _on_tray_exit(self):
        self.tray_manager.on_tray_exit()
    
    def _on_toolbar_hover(self, e, hover_color):
        # Handle toolbar button hover effects
        try:
            if hasattr(e, 'control') and e.control:
                if e.data == "true":  # Mouse enter
                    e.control.bgcolor = hover_color
                else:  # Mouse leave
                    e.control.bgcolor = ft.Colors.TRANSPARENT
                if self.page:
                    self.page.update()
        except Exception:
            pass

    def _on_window_event(self, e):
        # Handle window events for proper cleanup
        if e.event_type == ft.WindowEventType.CLOSE:
            try:
                # Clean up tray resources
                self.tray_manager.cleanup()
            except Exception:
                pass

def main():
    app = ZSnaprApp()
    ft.app(target=app.main)

if __name__ == "__main__":
    main()