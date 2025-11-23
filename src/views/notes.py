import flet as ft

def notes_page(page: ft.Page = None) -> ft.Column:
    return ft.Column([
        ft.Text("Заметки", size=24, weight="bold"),
        ft.Divider(),
        ft.Text("Здесь будут ваши заметки", size=16)
    ], spacing=20, expand=True)