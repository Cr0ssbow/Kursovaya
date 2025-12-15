import flet as ft

def duty_calendar_page(page: ft.Page = None):
    """Календарь дежурной части"""
    return ft.Column([
        ft.Text("Календарь дежурной части", size=24, weight="bold"),
        ft.Divider(),
        ft.Container(
            content=ft.Text("Страница в разработке", size=16, color=ft.Colors.GREY),
            alignment=ft.alignment.center,
            expand=True
        )
    ], expand=True)