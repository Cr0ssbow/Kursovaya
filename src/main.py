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
from views.shifts2 import shifts2_page
from views.statistics import statistics_page
from views.notes import notes_page
from views.terminated import terminated_page
from database.models import Employee
from datetime import datetime

def check_birthdays():
    """Проверяет дни рождения сотрудников на сегодня"""
    today = datetime.now().date()
    birthday_employees = []
    
    for employee in Employee.select():
        if employee.birth_date.month == today.month and employee.birth_date.day == today.day:
            birthday_employees.append(employee.full_name)
    
    return birthday_employees

def main(page: ft.Page):
    page.title = "ЧОП Легион - Система учёта сотрудников"
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'assets', 'legion.ico')
    else:
        icon_path = os.path.abspath("D:/Kursovaya/src/assets/legion.ico")
    page.window.icon = icon_path
    page.window_width = 800
    page.window_height = 600
    page.window_min_width = 800
    page.window_min_height = 600
    # Загружаем тему из БД при старте
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
    
    # Проверяем дни рождения при запуске
    birthday_employees = check_birthdays()
    birthday_banner = None
    if birthday_employees:
        birthday_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CAKE, color=ft.Colors.WHITE),
                ft.Text(f"День рождения: {', '.join(birthday_employees)}", weight="bold", color=ft.Colors.WHITE),
                ft.IconButton(ft.Icons.CLOSE, icon_color=ft.Colors.WHITE, on_click=lambda e: hide_banner())
            ]),
            bgcolor=ft.Colors.PRIMARY,
            padding=10,
            border_radius=5
        )
        
        def hide_banner():
            birthday_banner.visible = False
            page.update()

    # Контейнер для отображения текущей страницы
    content_container = ft.Container(
        content=home_page(page),  # По умолчанию показываем главную страницу
        expand=True,
    )
    
    # Функция для переключения страниц
    def handle_navigation_change(e):
        selected_index = e.control.selected_index
        
        # Переключаем страницу в зависимости от индекса
        if selected_index == 0:
            content_container.content = home_page(page)

        elif selected_index == 1:
            content_container.content = settings_page(page) 

        elif selected_index == 2:
            content_container.content = employees_page(page)

        elif selected_index == 3:
            content_container.content = chief_employees_page(page)

        elif selected_index == 4:
            content_container.content = office_employees_page(page)

        elif selected_index == 5:
            content_container.content = objects_page(page)

        elif selected_index == 6:
            shifts_content, shifts_dialog = shifts2_page(page)
            content_container.content = shifts_content
            
            if shifts_dialog not in page.overlay:
                page.overlay.append(shifts_dialog)
            
        elif selected_index == 7:
            content_container.content = statistics_page(page)

        elif selected_index == 8:
            content_container.content = notes_page(page)

        elif selected_index == 9:
            content_container.content = terminated_page(page)

        page.close(page.drawer)
        page.update()
    
    # Создаём drawer с обработчиком
    page.drawer = drawer(handle_navigation_change)
    
    # Добавляем кнопку меню и контейнер с содержимым
    page.add( 
        ft.Column([
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.MENU,
                        on_click=lambda e: page.open(page.drawer),
                    ),
                    ft.Text("Система учёта сотрудников ЧОП Легион", size=20, weight="bold"),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            ft.Divider(),
            content_container,
            birthday_banner if birthday_banner else ft.Container(height=0),
        ], expand=True)
    )
    
    page.update()

ft.app(target=main)