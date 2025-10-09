import flet as ft
from peewee import *
from menu.drawer import drawer
from views.home import home_page
from views.employees import employees_page
from views.settings import settings_page
from database.utils import load_theme_from_db

def main(page: ft.Page):
    # Загружаем тему из БД при старте
    theme = load_theme_from_db()
    page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT

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
        
        # Закрываем drawer и обновляем страницу
        page.close(page.drawer)
        page.update()
    
    # Создаём drawer с обработчиком
    page.drawer = drawer(handle_navigation_change)
    
    # Добавляем кнопку меню и контейнер с содержимым
    page.add(
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
    )
    
    page.update()

ft.app(target=main)
