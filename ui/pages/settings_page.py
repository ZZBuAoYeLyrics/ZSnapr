import flet as ft
from config import DEFAULT_SETTINGS, SUPPORTED_FORMATS, HOTKEYS

def build(app):
    app.save_dir_field = ft.TextField(
        label="Save Directory",
        value=DEFAULT_SETTINGS["save_directory"],
        expand=True,
        border_radius=8,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )

    browse_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=app._browse_directory,
        tooltip="Browse for directory",
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_50,
            color=ft.Colors.BLUE_700,
            shape=ft.CircleBorder()
        )
    )

    app.format_dropdown = ft.Dropdown(
        label="Image Format",
        value=DEFAULT_SETTINGS["image_format"],
        options=[ft.dropdown.Option(fmt["name"]) for fmt in SUPPORTED_FORMATS],
        width=140,
        border_radius=8,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )

    app.delay_field = ft.TextField(
        label="Delay (seconds)",
        value=str(DEFAULT_SETTINGS["delay_seconds"]),
        width=120,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=8,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )

    app.auto_save_checkbox = ft.Checkbox(
        label="Auto-save screenshots",
        value=DEFAULT_SETTINGS["auto_save"],
        check_color=ft.Colors.WHITE,
        fill_color=ft.Colors.GREEN_600
    )
    
    app.auto_copy_fullscreen_checkbox = ft.Checkbox(
        label="Auto-copy fullscreen screenshots to clipboard",
        value=DEFAULT_SETTINGS["auto_copy_fullscreen"],
        check_color=ft.Colors.WHITE,
        fill_color=ft.Colors.BLUE_600
    )
    
    app.auto_copy_window_checkbox = ft.Checkbox(
        label="Auto-copy window screenshots to clipboard",
        value=DEFAULT_SETTINGS["auto_copy_window"],
        check_color=ft.Colors.WHITE,
        fill_color=ft.Colors.PURPLE_600
    )

    app.fullscreen_hotkey_field = ft.TextField(
        label="Fullscreen Hotkey",
        value=HOTKEYS.get("fullscreen", ""),
        expand=True,
        border_radius=8,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )
    fullscreen_record_btn = ft.IconButton(
        icon=ft.Icons.FIBER_SMART_RECORD_OUTLINED,
        tooltip="Record",
        on_click=lambda e: app._record_hotkey("fullscreen"),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_50,
            color=ft.Colors.PURPLE_700,
            shape=ft.CircleBorder()
        )
    )
    app.region_hotkey_field = ft.TextField(
        label="Region Hotkey",
        value=HOTKEYS.get("region", ""),
        expand=True,
        border_radius=8,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )
    region_record_btn = ft.IconButton(
        icon=ft.Icons.FIBER_SMART_RECORD_OUTLINED,
        tooltip="Record",
        on_click=lambda e: app._record_hotkey("region"),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_50,
            color=ft.Colors.PURPLE_700,
            shape=ft.CircleBorder()
        )
    )
    app.window_hotkey_field = ft.TextField(
        label="Window Hotkey",
        value=HOTKEYS.get("window", ""),
        expand=True,
        border_radius=8,
        filled=True,
        bgcolor=ft.Colors.GREY_50
    )
    window_record_btn = ft.IconButton(
        icon=ft.Icons.FIBER_SMART_RECORD_OUTLINED,
        tooltip="Record",
        on_click=lambda e: app._record_hotkey("window"),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_50,
            color=ft.Colors.PURPLE_700,
            shape=ft.CircleBorder()
        )
    )

    return ft.Container(
        content=ft.Column([
            # File Settings Card
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FOLDER_OUTLINED, size=22, color=ft.Colors.BLUE_600),
                        ft.Text("File Settings", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
                    ], spacing=10),
                    ft.Divider(height=1, color=ft.Colors.BLUE_100, thickness=1),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Save Directory", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                            ft.Row([app.save_dir_field, browse_btn], spacing=10)
                        ], spacing=5),
                        margin=ft.margin.symmetric(vertical=8)
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Image Format", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                                    app.format_dropdown
                                ], spacing=5),
                                expand=1
                            ),
                            ft.Container(width=20),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Capture Delay", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                                    app.delay_field
                                ], spacing=5),
                                expand=1
                            )
                        ]),
                        margin=ft.margin.symmetric(vertical=8)
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Capture Options", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                            ft.Container(
                                content=ft.Column([
                                    app.auto_save_checkbox,
                                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                                    app.auto_copy_fullscreen_checkbox,
                                    app.auto_copy_window_checkbox,
                                ], spacing=8),
                                padding=ft.padding.symmetric(vertical=8, horizontal=12),
                                bgcolor=ft.Colors.GREY_50,
                                border_radius=8,
                                border=ft.border.all(1, ft.Colors.GREY_100)
                            )
                        ], spacing=8),
                        margin=ft.margin.symmetric(vertical=8)
                    ),

                ], spacing=15),
                padding=22,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.BLUE_100),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.12, ft.Colors.BLUE_300),
                    offset=ft.Offset(0, 3)
                )
            ),
            
            # Hotkeys Settings Card
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.KEYBOARD_OUTLINED, size=22, color=ft.Colors.PURPLE_600),
                        ft.Text("Hotkey Settings", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800)
                    ], spacing=10),
                    ft.Divider(height=1, color=ft.Colors.PURPLE_100, thickness=1),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Global Hotkeys", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                            ft.ResponsiveRow([
                                ft.Row([app.fullscreen_hotkey_field, fullscreen_record_btn], spacing=6, col={"xs": 12, "md": 4}),
                                ft.Row([app.region_hotkey_field, region_record_btn], spacing=6, col={"xs": 12, "md": 4}),
                                ft.Row([app.window_hotkey_field, window_record_btn], spacing=6, col={"xs": 12, "md": 4}),
                            ], run_spacing=8, alignment=ft.MainAxisAlignment.START)
                        ], spacing=8),
                        margin=ft.margin.symmetric(vertical=8)
                    ),
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
            
            # Apply Settings Button
            ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=20, color=ft.Colors.WHITE),
                        ft.Text("Apply All Settings", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
                    ], spacing=10, tight=True),
                    on_click=app._apply_settings,
                    style=ft.ButtonStyle(
                        bgcolor={
                            ft.ControlState.DEFAULT: ft.Colors.GREEN_600,
                            ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                        },
                        shape=ft.RoundedRectangleBorder(radius=12),
                        elevation=4,
                        shadow_color=ft.Colors.GREEN_200
                    ),
                    height=50
                ),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=10)
            )
        ], spacing=20),
        padding=20
    )