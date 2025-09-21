import flet as ft
from config import HOTKEYS, DEFAULT_SETTINGS

def build(app):
    # Resolve values with fallbacks
    save_dir = getattr(app.save_dir_field, "value", None) if hasattr(app, "save_dir_field") else None
    if not save_dir:
        save_dir = getattr(getattr(app, "save_manager", None), "default_directory", None) or getattr(getattr(app, "engine", None), "save_directory", None) or DEFAULT_SETTINGS["save_directory"]
    image_format = getattr(app.format_dropdown, "value", None) if hasattr(app, "format_dropdown") else None
    if not image_format:
        image_format = getattr(getattr(app, "engine", None), "image_format", None) or DEFAULT_SETTINGS["image_format"]
    delay_value = getattr(app.delay_field, "value", None) if hasattr(app, "delay_field") else None
    if not delay_value:
        delay_value = str(getattr(getattr(app, "engine", None), "delay", 0))
    auto_save = getattr(app.auto_save_checkbox, "value", None) if hasattr(app, "auto_save_checkbox") else None
    if auto_save is None:
        auto_save = bool(getattr(getattr(app, "engine", None), "auto_save", False))
    return ft.Container(
        content=ft.Column([
            ft.Container(visible=False,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CAMERA_ALT, size=20, color=ft.Colors.BLUE_600),
                        ft.Text("Quick Capture", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
                    ], spacing=8),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Row([
                        ft.Container(
                            content=ft.ElevatedButton(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.FULLSCREEN, size=24, color=ft.Colors.WHITE),
                                    ft.Text("Full Screen", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                on_click=app._capture_fullscreen,
                                style=ft.ButtonStyle(
                                    bgcolor={
                                        ft.ControlState.DEFAULT: ft.Colors.BLUE_600,
                                        ft.ControlState.HOVERED: ft.Colors.BLUE_700,
                                    },
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    elevation=2,
                                    shadow_color=ft.Colors.BLUE_200
                                ),
                                width=140,
                                height=60
                            ),
                            margin=ft.margin.all(5)
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.CROP_FREE, size=24, color=ft.Colors.WHITE),
                                    ft.Text("Select Region", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                on_click=app._capture_region,
                                style=ft.ButtonStyle(
                                    bgcolor={
                                        ft.ControlState.DEFAULT: ft.Colors.GREEN_600,
                                        ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                                    },
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    elevation=2,
                                    shadow_color=ft.Colors.GREEN_200
                                ),
                                width=140,
                                height=60
                            ),
                            margin=ft.margin.all(5)
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.WINDOW, size=24, color=ft.Colors.WHITE),
                                    ft.Text("Active Window", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                on_click=app._capture_window,
                                style=ft.ButtonStyle(
                                    bgcolor={
                                        ft.ControlState.DEFAULT: ft.Colors.ORANGE_600,
                                        ft.ControlState.HOVERED: ft.Colors.ORANGE_700,
                                    },
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    elevation=2,
                                    shadow_color=ft.Colors.ORANGE_200
                                ),
                                width=140,
                                height=60
                            ),
                            margin=ft.margin.all(5)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
                ], spacing=12),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                )
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.INFO, size=20, color=ft.Colors.BLUE_600),
                        ft.Text("Current Settings", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
                    ], spacing=8),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.ResponsiveRow([
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.BLUE_600), ft.Text("Save Directory", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text(save_dir, size=12, weight=ft.FontWeight.W_500, selectable=True)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 12}
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.IMAGE, size=16, color=ft.Colors.GREEN_600), ft.Text("Image Format", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text(str(image_format), size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 6}
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.TIMER, size=16, color=ft.Colors.ORANGE_600), ft.Text("Delay (s)", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text(delay_value, size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 6}
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.SAVE, size=16, color=ft.Colors.PURPLE_600), ft.Text("Auto Save", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text("On" if auto_save else "Off", size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 6}
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.KEYBOARD, size=16, color=ft.Colors.PURPLE_600), ft.Text("Fullscreen Hotkey", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text(HOTKEYS.get("fullscreen", "").upper(), size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 6}
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.KEYBOARD, size=16, color=ft.Colors.PURPLE_600), ft.Text("Region Hotkey", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text(HOTKEYS.get("region", "").upper(), size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 6}
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.Icons.KEYBOARD, size=16, color=ft.Colors.PURPLE_600), ft.Text("Window Hotkey", size=12, color=ft.Colors.GREY_700)], spacing=6),
                                ft.Text(HOTKEYS.get("window", "").upper(), size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6),
                            padding=12,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.GREY_200),
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
                            col={"xs": 12, "md": 6}
                        ),
                    ], run_spacing=10),
                    
                ], spacing=12),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                )
            )
        ], spacing=15),
        padding=15
    )