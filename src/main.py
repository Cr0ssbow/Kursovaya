import flet as ft
from peewee import *
from menu.drawer import drawer
from views.home import home_page
from views.employees import employees_page
from views.settings import settings_page, load_theme_from_db
from views.calendar import calendar_page
from views.objects import objects_page

def main(page: ft.Page):
    page.window_width = 800
    page.window_height = 600
    page.window_min_width = 800
    page.window_min_height = 600
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

        elif selected_index == 3:
            content_container.content = objects_page(page)

        elif selected_index == 4:
            calendar_content, date_menu_dialog = calendar_page(page)
            content_container.content = calendar_content
            
            if date_menu_dialog not in page.overlay:
                page.overlay.append(date_menu_dialog)

        
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
