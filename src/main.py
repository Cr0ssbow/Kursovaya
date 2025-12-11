import flet as ft
import sys
from peewee import *
from menu.drawer import drawer
from views.home import home_page
from views.employees import employees_page
from views.chief_employees import chief_employees_page
from views.office_employees import office_employees_page
from views.settings import settings_page, load_theme_from_db
import os
from views.objects import objects_page
from views.calendar import calendar_page
from views.statistics import statistics_page
from views.notes import notes_page
from views.terminated import terminated_page
from views.discarded_cards import discarded_cards_page
from views.logs import logs_page
from views.administration import administration_page
from database.models import Employee
from datetime import datetime
from utils.faker_data import generate_all_fake_data, create_december_shifts
from auth.auth import AuthManager, create_login_page

def main(page: ft.Page):
    # Генерируем тестовые данные при первом запуске
    generate_all_fake_data()  # Раскомментируйте для генерации данных
    create_december_shifts()  # Создаем 100 смен на каждый день декабря
    
    page.title = "ЧОП Легион - Система учёта сотрудников"
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'assets', 'legion.ico')
    else:
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'legion.ico')
    page.window.icon = icon_path
    page.window_width = 800
    page.window_height = 600
    page.window_min_width = 800
    page.window_min_height = 600
    
    # Инициализируем менеджер авторизации
    auth_manager = AuthManager()
    
    # Загружаем тему из БД при старте
    theme = load_theme_from_db()
    
    if theme == "dark":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = None
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
    

    # Контейнер для отображения текущей страницы
    content_container = ft.Container(
        expand=True,
    )
    
    # Функция для переключения страниц
    def handle_navigation_change(e):
        selected_index = e.control.selected_index
        
        # Получаем маппинг из атрибута функции
        page_name = getattr(handle_navigation_change, 'page_mapping', {}).get(selected_index)
        
        if not page_name:
            return
        
        # Переключаем страницу по названию
        if page_name == "home":
            content_container.content = home_page(page)
        elif page_name == "settings":
            content_container.content = settings_page(page)
        elif page_name == "employees":
            page.auth_manager = auth_manager
            content_container.content = employees_page(page)
        elif page_name == "chief_employees":
            page.auth_manager = auth_manager
            content_container.content = chief_employees_page(page)
        elif page_name == "office_employees":
            page.auth_manager = auth_manager
            content_container.content = office_employees_page(page)
        elif page_name == "objects":
            page.auth_manager = auth_manager
            content_container.content = objects_page(page)
        elif page_name == "calendar":
            shifts_content, shifts_dialog = calendar_page(page)
            content_container.content = shifts_content
            if shifts_dialog not in page.overlay:
                page.overlay.append(shifts_dialog)
        elif page_name == "statistics":
            content_container.content = statistics_page(page)
        elif page_name == "notes":
            content_container.content = notes_page(page)
        elif page_name == "terminated":
            content_container.content = terminated_page(page)
        elif page_name == "discarded_cards":
            content_container.content = discarded_cards_page(page)
        elif page_name == "logs":
            content_container.content = logs_page(page)
        elif page_name == "administration":
            content_container.content = administration_page(page)

        page.close(page.drawer)
        page.update()
    
    def show_main_app():
        """Показывает основное приложение после авторизации"""
        page.controls.clear()
        
        
        # Создаём drawer с обработчиком и проверкой доступа
        page.drawer = drawer(handle_navigation_change, auth_manager)
        
        # Устанавливаем главную страницу по умолчанию
        content_container.content = home_page(page)
        
        # Добавляем кнопку меню и контейнер с содержимым
        page.add( 
            ft.Column([
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.MENU,
                            on_click=lambda e: page.open(page.drawer),
                        ),
                        ft.Text("Система учёта сотрудников ЧОП Легион", size=20, weight="bold")
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Row(
                    [
                        ft.TextButton(
                            f"Пользователь: {auth_manager.current_user.username}",
                            on_click=lambda e: None
                        ),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            tooltip="Выйти",
                            on_click=lambda e: logout()
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Divider(),
                content_container,

            ], expand=True)
        )
        page.update()
    
    def logout():
        """Выход из системы"""
        auth_manager.logout()
        show_login()
    
    def show_login():
        """Показывает экран авторизации"""
        page.controls.clear()
        login_content = create_login_page(page, auth_manager, show_main_app)
        page.add(
            ft.Container(
                content=login_content,
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()
    
    # Показываем экран авторизации при запуске
    show_login()

ft.app(target=main)