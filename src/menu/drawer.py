import flet as ft
from peewee import *

def drawer(on_change_handler):
    """Создаёт navigation drawer с обработчиком событий"""
    return ft.NavigationDrawer(
        on_change=on_change_handler,  # Добавлен обработчик события
        controls=[
            ft.Container(height=12),
            ft.NavigationDrawerDestination(
                label="Домашняя страница",
                icon=ft.Icons.HOME,
                selected_icon=ft.Icon(ft.Icons.HOME_OUTLINED),
            ),
            ft.Divider(thickness=2),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.SETTINGS),
                label="Настройки",
                selected_icon=ft.Icons.SETTINGS_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.PERSON),
                label="Сотрудники",
                selected_icon=ft.Icons.PERSON_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.BUSINESS),
                label="Объекты",
                selected_icon=ft.Icons.BUSINESS_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.SCHEDULE),
                label="Календарь смен",
                selected_icon=ft.Icons.SCHEDULE_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.BAR_CHART),
                label="Статистика",
                selected_icon=ft.Icons.BAR_CHART_OUTLINED,
            ),
        ],
    )
