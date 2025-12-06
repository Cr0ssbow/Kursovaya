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
                icon=ft.Icon(ft.Icons.SECURITY),
                label="Сотрудники охраны",
                selected_icon=ft.Icons.SECURITY_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.SUPERVISOR_ACCOUNT),
                label="Начальники охраны",
                selected_icon=ft.Icons.SUPERVISOR_ACCOUNT_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.WORK),
                label="Сотрудники офиса",
                selected_icon=ft.Icons.WORK_OUTLINED,
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
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.NOTE),
                label="Заметки",
                selected_icon=ft.Icons.NOTE_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.PERSON_OFF),
                label="Уволенные сотрудники",
                selected_icon=ft.Icons.PERSON_OFF_OUTLINED,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.CREDIT_CARD_OFF),
                label="Списанные карточки",
                selected_icon=ft.Icons.CREDIT_CARD_OFF_OUTLINED,
            ),
            ft.Divider(thickness=2),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS),
                label="Администрирование",
                selected_icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
            ),
        ],
    )
