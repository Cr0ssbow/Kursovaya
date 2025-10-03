import flet as ft

def settings_page(page: ft.Page) -> ft.Column:
    global switch
    
    def theme_changed(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        switch.label = (
            "Светлая тема" if page.theme_mode == ft.ThemeMode.LIGHT else "Тёмная тема"
        )
        page.update()

    page.theme_mode = ft.ThemeMode.DARK
    switch = ft.Switch(label="Тёмная тема", on_change=theme_changed)
    
    return ft.Column(
        [
            ft.Text("Настройки", size=24, weight="bold"),
            ft.Text("Выбор темы"),
            switch,
        ],
        spacing=10,
        expand=True,
    )
