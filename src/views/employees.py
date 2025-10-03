import flet as ft

def employees_page() -> ft.Column:
    return ft.Column(
        [
            ft.Text("Сотрудники", size=24, weight="bold"),
            ft.ElevatedButton("Добавить сотрудника"),
            ft.Divider(),
            ft.ListTile(title=ft.Text("Иван Петров")),
            ft.ListTile(title=ft.Text("Мария Сидорова")),
        ],
        spacing=10,
        expand=True,
    )
