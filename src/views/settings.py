import flet as ft
from database.models import Settings, db
from peewee import DoesNotExist
from excel_export import export_assignments_to_excel

def save_theme_to_db(theme: str):
    try:
        Settings.get(Settings.key == "theme")
        Settings.update(value=theme).where(Settings.key == "theme").execute()
    except DoesNotExist:
        Settings.create(key="theme", value=theme)

def load_theme_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "theme")
        return setting.value
    except DoesNotExist:
        return "light"

def save_cell_shape_to_db(shape: str):
    try:
        Settings.get(Settings.key == "cell_shape")
        Settings.update(value=shape).where(Settings.key == "cell_shape").execute()
    except DoesNotExist:
        Settings.create(key="cell_shape", value=shape)

def load_cell_shape_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "cell_shape")
        return setting.value
    except DoesNotExist:
        return "square"

def save_birthday_display_to_db(enabled: bool):
    try:
        Settings.get(Settings.key == "show_birthdays")
        Settings.update(value="true" if enabled else "false").where(Settings.key == "show_birthdays").execute()
    except DoesNotExist:
        Settings.create(key="show_birthdays", value="true" if enabled else "false")

def load_birthday_display_from_db() -> bool:
    try:
        setting = Settings.get(Settings.key == "show_birthdays")
        return setting.value == "true"
    except DoesNotExist:
        return True  # По умолчанию включено

def manage_companies_dialog(page: ft.Page):
    """Диалог управления компаниями"""
    from database.models import Company
    
    companies_list = ft.Column([], spacing=5)
    new_company_field = ft.TextField(label="Новая компания", width=300)
    
    def refresh_companies():
        companies_list.controls.clear()
        for company in Company.select():
            companies_list.controls.append(
                ft.Row([
                    ft.Text(company.name, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        on_click=lambda e, c=company: delete_company(c),
                        tooltip="Удалить"
                    )
                ])
            )
        page.update()
    
    def add_company(e):
        name = new_company_field.value.strip()
        if name:
            try:
                Company.create(name=name)
                new_company_field.value = ""
                refresh_companies()
                show_snackbar("Компания добавлена!")
            except:
                show_snackbar("Компания уже существует!", True)
    
    def delete_company(company):
        from database.models import EmployeeCompany
        # Проверяем, есть ли сотрудники в этой компании
        if EmployeeCompany.select().where(EmployeeCompany.company == company).exists():
            show_snackbar("Нельзя удалить компанию с сотрудниками!", True)
        else:
            company.delete_instance()
            refresh_companies()
            show_snackbar("Компания удалена!")
    
    def show_snackbar(message, is_error=False):
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if is_error else ft.Colors.GREEN
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    
    dialog = ft.AlertDialog(
        title=ft.Text("Управление компаниями"),
        content=ft.Container(
            content=ft.Column([
                ft.Text("Список компаний:"),
                ft.Container(
                    content=companies_list,
                    height=200,
                    width=400
                ),
                ft.Divider(),
                ft.Row([
                    new_company_field,
                    ft.ElevatedButton("Добавить", on_click=add_company)
                ])
            ]),
            width=500,
            height=350
        ),
        actions=[
            ft.TextButton("Закрыть", on_click=lambda e: page.close(dialog))
        ]
    )
    
    refresh_companies()
    page.overlay.append(dialog)
    page.update()
    dialog.open = True
    page.update()

def settings_page(page: ft.Page) -> ft.Column:
    def theme_changed(e):
        selected_theme = e.control.value
        
        if selected_theme == "dark":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = None
        elif selected_theme == "dark_green":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
        elif selected_theme == "purple":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE)
        elif selected_theme == "amber":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)
        elif selected_theme == "brown":
            page.theme_mode = ft.ThemeMode.DARK
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.BROWN)
        elif selected_theme == "deep_orange":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_ORANGE)
        elif selected_theme == "light_green":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.LIGHT_GREEN)
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = None
        
        save_theme_to_db(selected_theme)
        page.update()

    # Загружаем тему из БД
    theme = load_theme_from_db()
    
    if theme == "dark":
        page.theme_mode = ft.ThemeMode.DARK
    elif theme == "dark_green":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
    elif theme == "purple":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE)
    elif theme == "amber":
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)
    elif theme == "brown":
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.BROWN)
    elif theme == "deep_orange":
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_ORANGE)
    elif theme == "light_green":
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.LIGHT_GREEN)
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = None
    
    theme_dropdown = ft.Dropdown(
        label="Выберите тему",
        value=theme,
        options=[
            ft.dropdown.Option("light", "Светлая тема"),
            ft.dropdown.Option("dark", "Тёмная тема"),
            ft.dropdown.Option("dark_green", "Темно-зелёная тема"),
            ft.dropdown.Option("purple", "Фиолетовая тема"),
            ft.dropdown.Option("amber", "Янтарная тема"),
            ft.dropdown.Option("brown", "Коричневая тема"),
            ft.dropdown.Option("deep_orange", "Оранжевая тема"),
            ft.dropdown.Option("light_green", "Светло-зелёная тема")
        ],
        on_change=theme_changed
    )
    
    def cell_shape_changed(e):
        selected_shape = e.control.value
        save_cell_shape_to_db(selected_shape)
    
    # Загружаем форму ячеек из БД
    cell_shape = load_cell_shape_from_db()
    
    cell_shape_dropdown = ft.Dropdown(
        label="Форма ячеек календаря",
        value=cell_shape,
        options=[
            ft.dropdown.Option("square", "Квадратные"),
            ft.dropdown.Option("round", "Круглые")
        ],
        on_change=cell_shape_changed
    )
    
    def birthday_display_changed(e):
        save_birthday_display_to_db(e.control.value)
    
    # Загружаем настройку отображения дней рождения из БД
    show_birthdays = load_birthday_display_from_db()
    
    birthday_checkbox = ft.Checkbox(
        label="Показывать контейнер дней рождения на главной странице",
        value=show_birthdays,
        on_change=birthday_display_changed
    )

    def import_to_excel(e):
        from datetime import datetime, date
        
        # Создаем список месяцев
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        
        current_date = date.today()
        current_month = current_date.month
        current_year = current_date.year
        
        month_dropdown = ft.Dropdown(
            label="Выберите месяц",
            width=200,
            value=str(current_month),
            options=[ft.dropdown.Option(str(i), months[i-1]) for i in range(1, 13)]
        )
        
        year_field = ft.TextField(
            label="Год",
            width=100,
            value=str(current_year)
        )
        
        def export_excel(e):
            try:
                month = int(month_dropdown.value)
                year = int(year_field.value)
                
                success, message = export_assignments_to_excel(month, year)
                
                export_dialog.open = False
                page.update()
                
                snack = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.GREEN if success else ft.Colors.RED,
                    duration=3000 if success else 5000
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                
            except ValueError:
                snack = ft.SnackBar(
                    content=ft.Text("Неверный формат года!"),
                    bgcolor=ft.Colors.RED
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
        
        export_dialog = ft.AlertDialog(
            title=ft.Text("Экспорт в Excel"),
            content=ft.Column([
                ft.Text("Выберите месяц и год для экспорта:"),
                ft.Row([month_dropdown, year_field], spacing=10)
            ], height=120, width=300),
            actions=[
                ft.TextButton("Экспорт", on_click=export_excel),
                ft.TextButton("Отмена", on_click=lambda e: setattr(export_dialog, 'open', False) or page.update())
            ],
            modal=True
        )
        
        page.overlay.append(export_dialog)
        export_dialog.open = True
        page.update()

    return ft.Column(
        [
            ft.Text("Настройки", size=24, weight="bold"),
            theme_dropdown,
            cell_shape_dropdown,
            birthday_checkbox,
            ft.Divider(),
            ft.Text("Импорт данных"),
            ft.ElevatedButton(
                "Импорт в Excel",
                icon=ft.Icons.FILE_DOWNLOAD,
                on_click=import_to_excel,
            ),
            ft.Divider(),
            ft.Text("Управление компаниями"),
            ft.ElevatedButton(
                "Управление компаниями",
                icon=ft.Icons.BUSINESS,
                on_click=lambda e: manage_companies_dialog(page),
            ),
        ],
        spacing=10,
        expand=True,
    )
