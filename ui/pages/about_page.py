import os
import platform
import json
import flet as ft
from config import APP_NAME, APP_VERSION, APP_CHANNEL

def _get_platform_info():
    # Get friendly platform name and architecture
    system = platform.system()
    arch = platform.machine()
    
    if system == "Windows":
        return f"Windows {arch}"
    elif system == "Darwin":
        return f"macOS {arch}"
    elif system == "Linux":
        return f"Linux {arch}"
    else:
        return f"{system} {arch}"

def _load_changelog():
    # Load complete update data from update.json
    try:
        with open('assets/update/update.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception:
        return None

def _show_changelog(app, e=None):
    # Show changelog dialog
    try:
        update_data = _load_changelog()
        
        def close_dlg(ev=None):
            try:
                app.page.close(dlg)
            except Exception:
                pass

        if not update_data or not update_data.get('releases'):
            content = ft.Column([
                ft.Text("无法加载更新日志", size=12, color=ft.Colors.GREY_600),
            ], tight=True, spacing=6)
        else:
            # Get the latest release (current version)
            latest_release = update_data['releases'][0]  # First release is the latest
            changelog = latest_release.get('changelog', {})
            
            content_items = []
            
            # Version info
            content_items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.NEW_RELEASES, size=18, color=ft.Colors.INDIGO_600),
                    ft.Text(f"版本 {latest_release.get('version', 'Unknown')}", 
                           size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                    ft.Text(f"({latest_release.get('releaseDate', 'Unknown')})", 
                           size=11, color=ft.Colors.GREY_600)
                ], spacing=8),
                padding=ft.padding.only(bottom=12)
            ))
            
            # Added features
            if changelog.get('added'):
                content_items.append(ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=16, color=ft.Colors.GREEN_700),
                    ft.Text("新增功能:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
                ], spacing=6))
                for item in changelog['added']:
                    content_items.append(ft.Row([
                        ft.Container(width=22),
                        ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=8, color=ft.Colors.GREEN_600),
                        ft.Text(f"{item}", size=11, color=ft.Colors.GREEN_600, expand=True)
                    ], spacing=6))
                content_items.append(ft.Container(height=8))
            
            # Changed features  
            if changelog.get('changed'):
                content_items.append(ft.Row([
                    ft.Icon(ft.Icons.BUILD_CIRCLE_OUTLINED, size=16, color=ft.Colors.BLUE_700),
                    ft.Text("优化改进:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
                ], spacing=6))
                for item in changelog['changed']:
                    content_items.append(ft.Row([
                        ft.Container(width=22),
                        ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=8, color=ft.Colors.BLUE_600),
                        ft.Text(f"{item}", size=11, color=ft.Colors.BLUE_600, expand=True)
                    ], spacing=6))
                content_items.append(ft.Container(height=8))
            
            # Fixed issues
            if changelog.get('fixed'):
                content_items.append(ft.Row([
                    ft.Icon(ft.Icons.BUG_REPORT_OUTLINED, size=16, color=ft.Colors.ORANGE_700),
                    ft.Text("问题修复:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)
                ], spacing=6))
                for item in changelog['fixed']:
                    content_items.append(ft.Row([
                        ft.Container(width=22),
                        ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=8, color=ft.Colors.ORANGE_600),
                        ft.Text(f"{item}", size=11, color=ft.Colors.ORANGE_600, expand=True)
                    ], spacing=6))
                content_items.append(ft.Container(height=8))
            
            # Security updates
            if changelog.get('security'):
                content_items.append(ft.Row([
                    ft.Icon(ft.Icons.SECURITY, size=16, color=ft.Colors.RED_700),
                    ft.Text("安全更新:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
                ], spacing=6))
                for item in changelog['security']:
                    content_items.append(ft.Row([
                        ft.Container(width=22),
                        ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=8, color=ft.Colors.RED_600),
                        ft.Text(f"{item}", size=11, color=ft.Colors.RED_600, expand=True)
                    ], spacing=6))
            
            content = ft.Column(content_items, tight=True, spacing=4, scroll=ft.ScrollMode.AUTO)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ARTICLE_OUTLINED, color=ft.Colors.INDIGO_600, size=20),
                ft.Text(f"更新日志 v{APP_VERSION}", size=14, weight=ft.FontWeight.W_600),
            ], spacing=8),
            content=ft.Container(
                content=content,
                width=500,
                height=400,
                padding=10
            ),
            actions=[
                ft.TextButton("关闭", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        app.page.open(dlg)
        app._update_status("更新日志已显示", ft.Colors.GREEN)
    except Exception as e:
        print(f"Changelog error: {e}")  # Debug output
        app._update_status("无法显示更新日志", ft.Colors.RED)

def _check_update(app, e=None):
    # Show modal dialog using page.open to ensure compatibility
    try:
        def close_dlg(ev=None):
            try:
                app.page.close(dlg)
            except Exception:
                pass
            app._update_status("No updates available", ft.Colors.GREY)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SYSTEM_UPDATE, color=ft.Colors.BLUE_600, size=20),
                ft.Text("Check for Updates", size=14, weight=ft.FontWeight.W_600),
            ], spacing=8),
            content=ft.Column([
                ft.Text(f"You are on the {APP_CHANNEL} version.\nCheck Update Functionality will be available in the next release", size=12),
                ft.Text(f"{APP_NAME} v{APP_VERSION}", size=12, color=ft.Colors.GREY_600),
            ], tight=True, spacing=6),
            actions=[
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        app.page.open(dlg)
    except Exception:
        app._update_status("No updates available", ft.Colors.GREY)

def build(app):
    # About page content
    return ft.Container(
        content=ft.Column([
            # About information card
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=22, color=ft.Colors.INDIGO_600),
                        ft.Text("About", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800)
                    ], spacing=10),
                    ft.Divider(height=1, color=ft.Colors.INDIGO_100, thickness=1),
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{APP_NAME}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
                                ft.Text(f"Version {APP_VERSION}", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_600),
                                ft.Text("Welcome To ZSnapr Dev By ZZBuAoYe.", size=12, color=ft.Colors.GREY_600, italic=True),
                            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=ft.padding.symmetric(vertical=12, horizontal=16),
                            bgcolor=ft.Colors.INDIGO_50,
                            border_radius=10,
                            alignment=ft.alignment.center
                        ),
                    ], spacing=8),
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.LANGUAGE, size=16, color=ft.Colors.WHITE), 
                                ft.Text("Website", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                            ], spacing=8, tight=True),
                            on_click=lambda e: os.startfile("https://zzbuaoye.top"),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12), 
                                bgcolor=ft.Colors.BLUE_600,
                                elevation=3,
                                shadow_color=ft.Colors.BLUE_200
                            ),
                            height=40
                        ),
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CODE, size=16, color=ft.Colors.WHITE), 
                                ft.Text("Repository", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                            ], spacing=8, tight=True),
                            on_click=lambda e: os.startfile("https://github.com/ZZBuAoYeLyrics"),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12), 
                                bgcolor=ft.Colors.GREY_700,
                                elevation=3,
                                shadow_color=ft.Colors.GREY_300
                            ),
                            height=40
                        ),
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=15),
                padding=22,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.INDIGO_100),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.12, ft.Colors.INDIGO_300),
                    offset=ft.Offset(0, 3)
                )
            ),
            
            # System information card
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.COMPUTER, size=22, color=ft.Colors.PURPLE_600),
                        ft.Text("System Information", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800)
                    ], spacing=10),
                    ft.Divider(height=1, color=ft.Colors.PURPLE_100, thickness=1),
                    ft.Column([
                        # Platform info with enhanced styling
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CHANGE_HISTORY_OUTLINED, size=18, color=ft.Colors.PURPLE_500),
                                    width=30,
                                    alignment=ft.alignment.center
                                ),
                                ft.Column([
                                    ft.Text("Platform", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_600),
                                    ft.Text(_get_platform_info(), size=13, weight=ft.FontWeight.W_600, color=ft.Colors.PURPLE_700),
                                ], spacing=2, tight=True),
                            ], spacing=12),
                            padding=ft.padding.symmetric(vertical=8, horizontal=12),
                            bgcolor=ft.Colors.PURPLE_50,
                            border_radius=8,
                        ),
                        # Python version info
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CODE, size=18, color=ft.Colors.BLUE_500),
                                    width=30,
                                    alignment=ft.alignment.center
                                ),
                                ft.Column([
                                    ft.Text("Python Version", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_600),
                                    ft.Text(f"{platform.python_version()}", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_700),
                                ], spacing=2, tight=True),
                            ], spacing=12),
                            padding=ft.padding.symmetric(vertical=8, horizontal=12),
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=8,
                        ),
                        # Working directory with better formatting
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.FOLDER_OPEN, size=18, color=ft.Colors.ORANGE_500),
                                        width=30,
                                        alignment=ft.alignment.center
                                    ),
                                    ft.Text("Working Directory", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_600),
                                ], spacing=12),
                                ft.Container(
                                    content=ft.Text(
                                        f"{os.getcwd()}", 
                                        size=11, 
                                        color=ft.Colors.ORANGE_700,
                                        weight=ft.FontWeight.W_500,
                                        selectable=True
                                    ),
                                    padding=ft.padding.only(left=42),
                                ),
                            ], spacing=4, tight=True),
                            padding=ft.padding.symmetric(vertical=8, horizontal=12),
                            bgcolor=ft.Colors.ORANGE_50,
                            border_radius=8,
                        ),
                    ], spacing=10),
                ], spacing=15),
                padding=22,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.PURPLE_100),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.12, ft.Colors.PURPLE_300),
                    offset=ft.Offset(0, 3)
                )
            ),
            
            # Update check card
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT, size=22, color=ft.Colors.GREEN_600),
                        ft.Text("Update Manager", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
                    ], spacing=10),
                    ft.Divider(height=1, color=ft.Colors.GREEN_100, thickness=1),
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Keep your application up to date with the latest features and security improvements.", 
                                       size=12, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=14, color=ft.Colors.GREEN_600),
                                        ft.Text(f"Current Channel: {APP_CHANNEL}", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_700),
                                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                    padding=ft.padding.symmetric(vertical=6, horizontal=12),
                                    bgcolor=ft.Colors.GREEN_50,
                                    border_radius=20,
                                ),
                            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=ft.padding.symmetric(vertical=12, horizontal=16),
                            bgcolor=ft.Colors.GREEN_50,
                            border_radius=10,
                        ),
                    ], spacing=8),
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.REFRESH, size=16, color=ft.Colors.WHITE), 
                                ft.Text("Check Updates", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600)
                            ], spacing=6, tight=True),
                            on_click=lambda e: _check_update(app, e),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12), 
                                bgcolor=ft.Colors.GREEN_600,
                                elevation=4,
                                shadow_color=ft.Colors.GREEN_200
                            ),
                            height=40
                        ),
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.ARTICLE_OUTLINED, size=16, color=ft.Colors.WHITE), 
                                ft.Text("更新日志", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600)
                            ], spacing=6, tight=True),
                            on_click=lambda e: _show_changelog(app, e),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12), 
                                bgcolor=ft.Colors.INDIGO_600,
                                elevation=4,
                                shadow_color=ft.Colors.INDIGO_200
                            ),
                            height=40
                        ),
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=15),
                padding=22,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.GREEN_100),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_300),
                    offset=ft.Offset(0, 3)
                )
            )
        ], spacing=20),
        padding=20
    )