import flet as ft

def statistics_page(page: ft.Page = None):
    statistics_content = ft.Column([
        ft.Text("Статистика", size=24, weight="bold"),
        ft.Divider(),
        ft.Container(
            content=ft.Text("Пустая страница статистики", size=16),
            expand=True,
        ),
    ], spacing=10, expand=True)
    
    return statistics_content