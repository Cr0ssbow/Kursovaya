import flet as ft
from database.models import OfficeEmployee, db
from datetime import datetime

def format_date(date):
    """Форматирует дату в строку дд.мм.гггг"""
    return date.strftime("%d.%m.%Y") if date else "Не указано"

def office_employees_page(page: ft.Page = None) -> ft.Column:
    current_page = 0
    page_size = 13
    search_value = ""
    
    def format_date_input(e):
        """Автоматически форматирует ввод даты"""
        value = e.control.value.replace(".", "")
        if len(value) == 8 and value.isdigit():
            day = int(value[:2])
            month = int(value[2:4])
            year = int(value[4:])
            
            if day > 31:
                day = 31
            if month > 12:
                month = 12
            if year > 2100:
                year = 2100
                
            formatted = f"{day:02d}.{month:02d}.{year}"
            e.control.value = formatted
            if page:
                page.update()
    
    # Диалог и поля формы
    add_dialog = ft.AlertDialog(modal=True)
    name_field = ft.TextField(label="ФИО", width=300)
    birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=format_date_input, max_length=10)
    position_field = ft.TextField(label="Должность", width=250)
    salary_field = ft.TextField(label="Зарплата", width=150)
    payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")

    def show_add_dialog(e):
        add_dialog.title = ft.Text("Добавить сотрудника офиса")
        add_dialog.content = ft.Column([
            name_field,
            birth_field,
            position_field,
            salary_field,
            payment_method_field,
        ], spacing=10)
        add_dialog.actions = [
            ft.TextButton("Сохранить", on_click=save_employee),
            ft.TextButton("Отмена", on_click=close_add_dialog),
        ]
        add_dialog.open = True
        if page and add_dialog not in page.overlay:
            page.overlay.append(add_dialog)
        if page:
            page.update()

    def close_add_dialog(e):
        add_dialog.open = False
        if page:
            page.update()

    def save_employee(e):
        try:
            if db.is_closed():
                db.connect()
            
            full_name = name_field.value.strip()
            birth_value = birth_field.value.strip()
            position_value = position_field.value.strip()
            salary_value = salary_field.value.strip()
            payment_method_value = payment_method_field.value
            
            if not full_name:
                raise ValueError("ФИО обязательно!")
            if not birth_value:
                raise ValueError("Дата рождения обязательна!")
            if not position_value:
                raise ValueError("Должность обязательна!")
            
            birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
            salary = float(salary_value) if salary_value else 0
            
            OfficeEmployee.create(
                full_name=full_name,
                birth_date=birth_date,
                position=position_value,
                salary=salary,
                payment_method=payment_method_value or "на карту"
            )
            close_add_dialog(e)
            refresh_table()
            if page:
                page.update()
        except ValueError as ex:
            add_dialog.content = ft.Column([
                name_field,
                birth_field,
                position_field,
                salary_field,
                payment_method_field,
                ft.Text(f"Ошибка: {str(ex)}", color=ft.Colors.RED)
            ], spacing=10)
            if page:
                page.update()
        except Exception as ex:
            print(f"Ошибка сохранения: {ex}")
        finally:
            if not db.is_closed():
                db.close()

    def refresh_table():
        """Обновляет данные в таблице"""
        query = OfficeEmployee.select().where(OfficeEmployee.termination_date.is_null())
        
        if search_value:
            query = query.where(OfficeEmployee.full_name.contains(search_value))
        
        employees_list = list(query.order_by(OfficeEmployee.full_name))
        
        # Пагинация
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        page_employees = employees_list[start_idx:end_idx]
        
        employees_table.rows.clear()
        for employee in page_employees:
            employees_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(employee.full_name, color=ft.Colors.BLUE), on_tap=lambda e, emp=employee: show_detail_dialog(emp)),
                        ft.DataCell(ft.Text(employee.position)),
                    ]
                )
            )
        
        # Обновляем кнопки пагинации
        total_pages = (len(employees_list) + page_size - 1) // page_size
        prev_btn.disabled = current_page == 0
        next_btn.disabled = current_page >= total_pages - 1
        page_info.value = f"Страница {current_page + 1} из {max(1, total_pages)}"

    def on_search_change(e):
        nonlocal search_value, current_page
        search_value = e.control.value.strip()
        current_page = 0
        refresh_table()
        if page:
            page.update()
    
    def prev_page(e):
        nonlocal current_page
        if current_page > 0:
            current_page -= 1
            refresh_table()
            if page:
                page.update()
    
    def next_page(e):
        nonlocal current_page
        current_page += 1
        refresh_table()
        if page:
            page.update()
    
    # Элементы пагинации
    prev_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=prev_page)
    next_btn = ft.IconButton(icon=ft.Icons.ARROW_FORWARD, on_click=next_page)
    page_info = ft.Text("Страница 1 из 1")
    
    # Диалог детальной информации
    detail_dialog = ft.AlertDialog(modal=True)
    
    def show_detail_dialog(employee):
        detail_dialog.title = ft.Text(f"Информация о сотруднике: {employee.full_name}")
        detail_dialog.content = ft.Column([
            ft.Text(f"Дата рождения: {format_date(employee.birth_date)}", size=16),
            ft.Text(f"Должность: {employee.position}", size=16),
            ft.Text(f"Зарплата: {employee.salary} ₽", size=16),
            ft.Text(f"Способ выдачи зарплаты: {employee.payment_method}", size=16),
        ], spacing=10, height=200)
        detail_dialog.actions = [
            ft.TextButton("Закрыть", on_click=lambda e: close_detail_dialog()),
        ]
        detail_dialog.open = True
        if page and detail_dialog not in page.overlay:
            page.overlay.append(detail_dialog)
        if page:
            page.update()
    
    def close_detail_dialog():
        detail_dialog.open = False
        if page:
            page.update()
    
    # Создаем DataTable
    employees_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО", width=400)),
            ft.DataColumn(ft.Text("Должность", width=200)),
        ],
        rows=[],
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        heading_row_height=70,
        data_row_min_height=50,
        data_row_max_height=50,
        column_spacing=10,
        width=700,
        height=707
    )
    refresh_table()
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Сотрудники офиса", size=24, weight="bold"),
                    ft.ElevatedButton(
                        "Добавить сотрудника",
                        icon=ft.Icons.ADD,
                        on_click=show_add_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Row([
                ft.TextField(
                    label="Поиск по ФИО",
                    width=300,
                    on_change=on_search_change,
                    autofocus=False,
                    dense=True,
                ),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.Column([
                    employees_table
                ], scroll=ft.ScrollMode.AUTO),
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10,
                expand=True,
            ),
            ft.Row([
                prev_btn,
                page_info,
                next_btn,
            ], alignment=ft.MainAxisAlignment.CENTER),
        ],
        spacing=10,
        expand=True,
    )