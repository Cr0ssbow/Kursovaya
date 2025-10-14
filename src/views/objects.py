import flet as ft

def objects_page(page: ft.Page):
    return ft.Column(
        [
            ft.Text("Страница Объекты", size=30, weight="bold"),
            ft.Text("Здесь будет список объектов."),
        ],
    )
