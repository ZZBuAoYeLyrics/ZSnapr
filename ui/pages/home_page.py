import flet as ft
from config import DEFAULT_SETTINGS

def build(app):
    # Robust getters with fallbacks
    save_dir = ""
    try:
        if hasattr(app, "save_dir_field") and app.save_dir_field and app.save_dir_field.value:
            save_dir = app.save_dir_field.value
        elif hasattr(app, "save_manager") and app.save_manager and getattr(app.save_manager, "default_directory", None):
            save_dir = app.save_manager.default_directory
        else:
            save_dir = DEFAULT_SETTINGS.get("save_directory", "")
    except Exception:
        save_dir = DEFAULT_SETTINGS.get("save_directory", "")

    img_fmt = ""
    try:
        if hasattr(app, "format_dropdown") and app.format_dropdown and app.format_dropdown.value:
            img_fmt = app.format_dropdown.value
        elif hasattr(app, "engine") and app.engine and getattr(app.engine, "image_format", None):
            img_fmt = app.engine.image_format
        else:
            img_fmt = DEFAULT_SETTINGS.get("image_format", "")
    except Exception:
        img_fmt = DEFAULT_SETTINGS.get("image_format", "")

    delay = "0"
    try:
        if hasattr(app, "delay_field") and app.delay_field and app.delay_field.value is not None:
            delay = str(app.delay_field.value)
        else:
            delay = str(DEFAULT_SETTINGS.get("delay_seconds", 0))
    except Exception:
        delay = str(DEFAULT_SETTINGS.get("delay_seconds", 0))

    auto_save = False
    try:
        if hasattr(app, "auto_save_checkbox") and app.auto_save_checkbox is not None:
            auto_save = bool(app.auto_save_checkbox.value)
        else:
            auto_save = bool(DEFAULT_SETTINGS.get("auto_save", False))
    except Exception:
        auto_save = bool(DEFAULT_SETTINGS.get("auto_save", False))

    def info_tile(icon, title, value, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, size=18, color=color), ft.Text(title, size=12, color=ft.Colors.GREY_700)], spacing=8),
                ft.Text(str(value), size=13, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900, selectable=True)
            ], spacing=6),
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1))
        )

    def save_dir_tile(path):
        # Compact card: left path, right action
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    expand=True,
                    content=ft.Row([
                        ft.Icon(ft.Icons.FOLDER, size=18, color=ft.Colors.BLUE_600),
                        ft.Text(str(path), size=13, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900, selectable=True),
                    ], spacing=8)
                ),
                ft.OutlinedButton(
                    content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN, size=16), ft.Text("Open", size=12)], spacing=6, tight=True),
                    on_click=app._open_folder,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    height=32
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 1))
        )

    quick_actions = ft.Container()

    return ft.Container(
        content=ft.Column([
            ft.Container(content=quick_actions, margin=ft.margin.only(top=8, bottom=10)),
            ft.ResponsiveRow([
                save_dir_tile(save_dir),
                info_tile(ft.Icons.IMAGE, "Image Format", img_fmt, ft.Colors.GREEN_600),
                info_tile(ft.Icons.TIMER, "Delay (s)", delay, ft.Colors.ORANGE_600),
                info_tile(ft.Icons.SAVE, "Auto Save", "On" if auto_save else "Off", ft.Colors.PURPLE_600),
            ], col={"xs": 12, "sm": 6, "md": 6, "lg": 3}, run_spacing=10)
        ], spacing=10),
        padding=15
    )