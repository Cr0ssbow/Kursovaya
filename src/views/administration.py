import flet as ft

def administration_page(page: ft.Page = None):
    """Страница администрирования"""
    
    return ft.Column([
        ft.Text("Администрирование", size=24, weight="bold"),
        ft.Divider(),
        ft.Text("Здесь будут функции администрирования системы", size=16),
        ft.Container(
            content=ft.Text("В разработке...", size=14, color=ft.Colors.GREY),
            padding=20
        )
    ], spacing=10, expand=True)