import datetime
import flet as ft

def home_page() -> ft.Column:
    return ft.Column(
        [
            ft.Text("Главная страница", size=24, weight="bold"),
            ft.Text("Добро пожаловать!"),
        ],
        spacing=10,
        expand=True,
    )
