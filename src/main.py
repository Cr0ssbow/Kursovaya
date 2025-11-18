import flet as ft
from peewee import *
from menu.drawer import drawer
from views.home import home_page
from views.employees import employees_page
from views.settings import settings_page, load_theme_from_db
from views.calendar import calendar_page
from views.objects import objects_page
from views.salary import salary_page
from views.shifts2 import shifts2_page
from views.statistics import statistics_page
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
    page.window_width = 800
    page.window_height = 600
    page.window_min_width = 800
    page.window_min_height = 600
    # Загружаем тему из БД при старте
    theme = load_theme_from_db()
    page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT
    
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
        content=home_page(),  # По умолчанию показываем главную страницу
        expand=True,
    )
    
    # Функция для переключения страниц
    def handle_navigation_change(e):
        selected_index = e.control.selected_index
        
        # Переключаем страницу в зависимости от индекса
        if selected_index == 0:
            content_container.content = home_page()

        elif selected_index == 1:
            content_container.content = settings_page(page) 

        elif selected_index == 2:
            content_container.content = employees_page(page)

        elif selected_index == 3:
            content_container.content = objects_page(page)

        elif selected_index == 4:
            calendar_content, date_menu_dialog = calendar_page(page)
            content_container.content = calendar_content
            
            if date_menu_dialog not in page.overlay:
                page.overlay.append(date_menu_dialog)
            
        elif selected_index == 5:
            shifts_content, shifts_dialog = shifts2_page(page)
            content_container.content = shifts_content
            
            if shifts_dialog not in page.overlay:
                page.overlay.append(shifts_dialog)
            
        elif selected_index == 6:
            content_container.content = salary_page(page)
            
        elif selected_index == 7:
            content_container.content = statistics_page(page)

        
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
                    ft.Text("Моё приложение", size=20, weight="bold"),
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