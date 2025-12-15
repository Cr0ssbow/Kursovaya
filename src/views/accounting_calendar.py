import flet as ft

def accounting_calendar_page(page: ft.Page = None):
    """Календарь бухгалтерии"""
    return ft.Column([
        ft.Text("Календарь бухгалтерии", size=24, weight="bold"),
        ft.Divider(),
        ft.Container(
            content=ft.Text("Страница в разработке", size=16, color=ft.Colors.GREY),
            alignment=ft.alignment.center,
            expand=True
        )
    ], expand=True)