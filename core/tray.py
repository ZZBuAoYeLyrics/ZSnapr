import threading
import os
import time
import pystray
from PIL import Image, ImageDraw
import queue

class TrayManager:
    def __init__(self, app):
        self.app = app
        self.tray_icon = None
        self.tray_thread = None
        self.action_queue = queue.Queue()
        self.checker_running = False
        self.checker_thread = None
        self._stop_event = threading.Event()

    def _create_tray_image(self):
        # Create tray icon image
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((4, 4, 60, 60), fill=(30, 136, 229, 255))
        d.ellipse((22, 22, 42, 42), fill=(255, 255, 255, 255))
        return img

    def _show_tray(self):
        # Show system tray icon with proper error handling
        try:
            def on_restore(icon, item):
                self.action_queue.put("restore")
            
            def on_exit(icon, item):
                self.action_queue.put("exit")
            
            def on_capture(icon, item):
                self.action_queue.put("capture_region")
            
            def on_click(icon):
                self.action_queue.put("capture_region")

            image = self._create_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Capture Region", on_capture, default=True),
                pystray.MenuItem("Restore Window", on_restore),
                pystray.MenuItem("Exit", on_exit)
            )
            
            self.tray_icon = pystray.Icon("ZSnapr", image, "ZSnapr", menu)
            self.tray_icon.on_click = on_click
            
            # Run tray icon (blocking call)
            self.tray_icon.run()
            
        except Exception as e:
            print(f"Tray icon error: {e}")
        finally:
            self.tray_icon = None

    def minimize_to_tray(self):
        # Minimize window to system tray
        try:
            # Hide the main window
            self._hide_window()
            
            # Start tray icon if not already running
            if not self.tray_thread or not self.tray_thread.is_alive():
                self._stop_event.clear()
                self.tray_thread = threading.Thread(target=self._show_tray, daemon=True)
                self.tray_thread.start()
            
            # Update status
            if hasattr(self.app, '_update_status'):
                self.app._update_status("Minimized to tray")
                
        except Exception as e:
            print(f"Minimize to tray error: {e}")

    def _hide_window(self):
        # Hide the main window with multiple fallback methods
        try:
            if not self.app.page:
                return
                
            # Try different methods to hide window
            window = self.app.page.window
            
            # Method 1: Direct hide
            try:
                if hasattr(window, 'hide'):
                    window.hide()
                    return
            except Exception:
                pass
            
            # Method 2: Set visible to False
            try:
                if hasattr(window, 'visible'):
                    window.visible = False
                    return
            except Exception:
                pass
            
            # Method 3: Minimize
            try:
                if hasattr(window, 'minimized'):
                    window.minimized = True
            except Exception:
                pass
                
        except Exception as e:
            print(f"Hide window error: {e}")

    def start_checker(self):
        # Start action queue checker with improved stability
        if self.checker_running:
            return
            
        self.checker_running = True
        self.checker_thread = threading.Thread(target=self._action_checker, daemon=True)
        self.checker_thread.start()

    def _action_checker(self):
        # Process tray actions in a stable loop
        while self.checker_running and not self._stop_event.is_set():
            try:
                # Check for actions with timeout
                try:
                    action = self.action_queue.get(timeout=0.1)
                    self._process_action(action)
                except queue.Empty:
                    continue
                    
            except Exception as e:
                print(f"Action checker error: {e}")
                
            # Small delay to prevent CPU spinning
            time.sleep(0.05)

    def _process_action(self, action):
        # Process individual tray actions safely
        try:
            if action == "capture_region":
                if hasattr(self.app, '_capture_region'):
                    # Use threading to avoid blocking
                    threading.Thread(target=self.app._capture_region, daemon=True).start()
                    
            elif action == "restore":
                self.restore_from_tray()
                
            elif action == "exit":
                self._exit_application()
                
        except Exception as e:
            print(f"Process action error: {e}")

    def restore_from_tray(self):
        # Restore window from tray with proper cleanup
        try:
            # Stop tray icon first
            self._stop_tray_icon()
            
            # Restore window
            self._show_window()
            
            # Update page
            if self.app.page:
                self.app.page.update()
                
        except Exception as e:
            print(f"Restore from tray error: {e}")

    def _show_window(self):
        # Show the main window with multiple methods
        try:
            if not self.app.page:
                return
                
            window = self.app.page.window
            
            # Method 1: Direct show
            try:
                if hasattr(window, 'show'):
                    window.show()
                    return
            except Exception:
                pass
            
            # Method 2: Set visible to True
            try:
                if hasattr(window, 'visible'):
                    window.visible = True
            except Exception:
                pass
            
            # Method 3: Un-minimize
            try:
                if hasattr(window, 'minimized'):
                    window.minimized = False
            except Exception:
                pass
            
            # Method 4: Bring to front
            try:
                if hasattr(window, 'to_front'):
                    window.to_front = True
            except Exception:
                pass
                
        except Exception as e:
            print(f"Show window error: {e}")

    def _stop_tray_icon(self):
        # Safely stop tray icon
        try:
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
        except Exception as e:
            print(f"Stop tray icon error: {e}")

    def _exit_application(self):
        # Clean exit of the application
        try:
            # Stop checker
            self.checker_running = False
            self._stop_event.set()
            
            # Stop tray icon
            self._stop_tray_icon()
            
            # Force exit
            os._exit(0)
            
        except Exception:
            # Force exit as last resort
            os._exit(0)

    def cleanup(self):
        # Clean up resources
        try:
            self.checker_running = False
            self._stop_event.set()
            self._stop_tray_icon()
        except Exception:
            pass

    # Public interface methods for compatibility
    def on_tray_click(self):
        self.action_queue.put("capture_region")

    def on_tray_restore(self):
        self.action_queue.put("restore")

    def on_tray_exit(self):
        self.action_queue.put("exit")