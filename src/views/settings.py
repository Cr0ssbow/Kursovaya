import flet as ft
from database.models import Settings, db
from peewee import DoesNotExist
from excel_export import export_assignments_to_excel

def save_theme_to_db(theme: str):
    Settings.insert(key="theme", value=theme).on_conflict_replace().execute()

def load_theme_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "theme")
        return setting.value
    except DoesNotExist:
        return "light"

def save_cell_shape_to_db(shape: str):
    Settings.insert(key="cell_shape", value=shape).on_conflict_replace().execute()

def load_cell_shape_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "cell_shape")
        return setting.value
    except DoesNotExist:
        return "square"

def settings_page(page: ft.Page) -> ft.Column:
    def theme_changed(e):
        selected_theme = e.control.value
        
        if selected_theme == "dark":
            page.theme_mode = ft.ThemeMode.DARK
        elif selected_theme == "dark_green":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
        elif selected_theme == "purple":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE)
        elif selected_theme == "amber":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)
        elif selected_theme == "brown":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.BROWN)
        elif selected_theme == "deep_orange":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_ORANGE)
        elif selected_theme == "light_green":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.LIGHT_GREEN)
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = None
        
        save_theme_to_db(selected_theme)
        page.update()

    # Загружаем тему из БД
    theme = load_theme_from_db()
    
    if theme == "dark":
        page.theme_mode = ft.ThemeMode.DARK
    elif theme == "dark_green":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
    elif theme == "purple":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE)
    elif theme == "amber":
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)
    elif theme == "brown":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.BROWN)
    elif theme == "deep_orange":
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_ORANGE)
    elif theme == "light_green":
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.LIGHT_GREEN)
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = None
    
    theme_dropdown = ft.Dropdown(
        label="Выберите тему",
        value=theme,
        options=[
            ft.dropdown.Option("light", "Светлая тема"),
            ft.dropdown.Option("dark", "Тёмная тема"),
            ft.dropdown.Option("dark_green", "Темно-зелёная тема"),
            ft.dropdown.Option("purple", "Фиолетовая тема"),
            ft.dropdown.Option("amber", "Янтарная тема"),
            ft.dropdown.Option("brown", "Коричневая тема"),
            ft.dropdown.Option("deep_orange", "Оранжевая тема"),
            ft.dropdown.Option("light_green", "Светло-зелёная тема")
        ],
        on_change=theme_changed
    )
    
    def cell_shape_changed(e):
        selected_shape = e.control.value
        save_cell_shape_to_db(selected_shape)
    
    # Загружаем форму ячеек из БД
    cell_shape = load_cell_shape_from_db()
    
    cell_shape_dropdown = ft.Dropdown(
        label="Форма ячеек календаря",
        value=cell_shape,
        options=[
            ft.dropdown.Option("square", "Квадратные"),
            ft.dropdown.Option("round", "Круглые")
        ],
        on_change=cell_shape_changed
    )

    def import_to_excel(e):
        success, message = export_assignments_to_excel()
        
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN if success else ft.Colors.RED,
            duration=3000 if success else 5000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    return ft.Column(
        [
            ft.Text("Настройки", size=24, weight="bold"),
            theme_dropdown,
            cell_shape_dropdown,
            ft.Divider(),
            ft.Text("Импорт данных"),
            ft.ElevatedButton(
                "Импорт в Excel",
                icon=ft.Icons.FILE_DOWNLOAD,
                on_click=import_to_excel,
            ),
        ],
        spacing=10,
        expand=True,
    )
