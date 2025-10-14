import flet as ft
from database.models import Settings
from peewee import DoesNotExist

def save_theme_to_db(theme: str):
    Settings.insert(key="theme", value=theme).on_conflict_replace().execute()

def load_theme_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "theme")
        return setting.value
    except DoesNotExist:
        return "light"

def settings_page(page: ft.Page) -> ft.Column:
    global switch

    def theme_changed(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        switch.label = (
            "Светлая тема" if page.theme_mode == ft.ThemeMode.LIGHT else "Тёмная тема"
        )
        save_theme_to_db("dark" if page.theme_mode == ft.ThemeMode.DARK else "light")
        page.update()

    # Загружаем тему из БД
    theme = load_theme_from_db()
    page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT
    switch = ft.Switch(label=("Тёмная тема" if theme == "dark" else "Светлая тема"), value=(theme == "dark"), on_change=theme_changed)

    return ft.Column(
        [
            ft.Text("Настройки", size=24, weight="bold"),
            ft.Text("Выбор темы"),
            switch,
        ],
        spacing=10,
        expand=True,
    )
