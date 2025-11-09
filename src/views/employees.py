import flet as ft
from database.models import Employee, Assignment, db
from datetime import datetime

def load_employees():
    """Загружает список сотрудников из БД"""
    return Employee.select().order_by(Employee.full_name)

def format_date(date):
    """Форматирует дату в строку дд.мм.гггг"""
    return date.strftime("%d.%m.%Y") if date else "Не указано"

def format_salary(salary):
    """Форматирует зарплату в строку с разделителями"""
    n = int(float(salary) * 100)
    formatted = ""
    count = 0
    
    while n > 0:
        if count > 0 and count % 3 == 0:
            formatted = " " + formatted
        formatted = str(n % 10) + formatted
        n = n // 10
        count += 1
    
    if len(formatted) > 2:
        formatted = formatted[:-2] + "," + formatted[-2:]
    else:
        formatted = "0," + formatted.zfill(2)
    
    return formatted + " ₽"

employees_table = None

def employees_page(page: ft.Page = None) -> ft.Column:
    sort_column = "full_name"
    sort_reverse = False
    current_page = 0
    page_size = 13
    global employees_table
    
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
    birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=format_date_input, input_filter=ft.InputFilter(regex_string=r"[0-9.]", allow=True), max_length=10)
    hire_field = ft.TextField(label="Дата принятия (дд.мм.гггг)", width=180, on_change=format_date_input, input_filter=ft.InputFilter(regex_string=r"[0-9.]", allow=True), max_length=10)
    guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=250, on_change=format_date_input, input_filter=ft.InputFilter(regex_string=r"[0-9.]", allow=True), max_length=10)
    guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option(str(i)) for i in range(3, 7)])

    def show_add_dialog(e):
        add_dialog.title = ft.Text("Добавить сотрудника")
        add_dialog.content = ft.Column([
            name_field,
            birth_field,
            hire_field,
            guard_license_field,
            guard_rank_field,
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
        from database.models import Employee
        from datetime import datetime
        try:
            full_name = name_field.value.strip()
            birth_value = birth_field.value.strip()
            hire_value = hire_field.value.strip()
            guard_license_value = guard_license_field.value.strip()
            guard_rank_value = guard_rank_field.value
            
            if not full_name:
                raise ValueError("ФИО обязательно!")
            if not birth_value:
                raise ValueError("Дата рождения обязательна!")
            if not hire_value:
                raise ValueError("Дата принятия на работу обязательна!")
            
            birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
            hire_date = datetime.strptime(hire_value, "%d.%m.%Y").date()
            guard_license_date = datetime.strptime(guard_license_value, "%d.%m.%Y").date() if guard_license_value else None
            guard_rank = int(guard_rank_value) if guard_rank_value else None
            
            Employee.create(
                full_name=full_name,
                birth_date=birth_date,
                hire_date=hire_date,
                guard_license_date=guard_license_date,
                guard_rank=guard_rank
            )
            close_add_dialog(e)
            refresh_table()
            if page:
                page.update()
        except ValueError as ex:
            add_dialog.content = ft.Column([
                name_field,
                birth_field,
                hire_field,
                guard_license_field,
                guard_rank_field,
                ft.Text(f"Ошибка: {str(ex)}", color=ft.Colors.RED)
            ], spacing=10)
            if page:
                page.update()
        except Exception:
            pass
    
    search_value = ""

    def refresh_table():
        """Обновляет данные в таблице с учетом поиска и пагинации"""
        if search_value:
            employees_list = list(Employee.select().where(Employee.full_name.contains(search_value)).order_by(Employee.full_name))
        else:
            employees_list = list(load_employees())
        # Сортировка
        def key(emp):
            if sort_column == "full_name":
                return emp.full_name
            elif sort_column == "birth_date":
                return emp.birth_date
            elif sort_column == "hire_date":
                return emp.hire_date
            elif sort_column == "salary":
                return float(emp.salary)
            return emp.full_name
        employees_list.sort(key=key, reverse=sort_reverse)
        
        # Пагинация
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        page_employees = employees_list[start_idx:end_idx]
        
        employees_table.rows.clear()
        for employee in page_employees:
            guard_license_text = format_date(getattr(employee, 'guard_license_date', None))
            guard_rank_text = str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else "Не указано"
            
            employees_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(employee.full_name), on_tap=lambda e, emp=employee: show_edit_dialog(emp)),
                        ft.DataCell(ft.Text(format_date(employee.birth_date))),
                        ft.DataCell(ft.Text(format_date(employee.hire_date))),
                        ft.DataCell(ft.Text(guard_license_text)),
                        ft.DataCell(ft.Text(guard_rank_text)),
                    ]
                )
            )
        
        # Обновляем кнопки пагинации
        total_pages = (len(employees_list) + page_size - 1) // page_size
        prev_btn.disabled = current_page == 0
        next_btn.disabled = current_page >= total_pages - 1
        page_info.value = f"Страница {current_page + 1} из {max(1, total_pages)}"
    def on_sort(col):
        nonlocal sort_column, sort_reverse
        if sort_column == col:
            sort_reverse = not sort_reverse
        else:
            sort_column = col
            sort_reverse = False
        refresh_table()
        if page:
            page.update()

    # Диалог редактирования
    edit_dialog = ft.AlertDialog(modal=True)
    edit_name = ft.TextField(label="ФИО", width=300)
    edit_birth = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=format_date_input, input_filter=ft.InputFilter(regex_string=r"[0-9.]", allow=True), max_length=10)
    edit_hire = ft.TextField(label="Дата принятия (дд.мм.гггг)", width=180, on_change=format_date_input, input_filter=ft.InputFilter(regex_string=r"[0-9.]", allow=True), max_length=10)
    edit_guard_license = ft.TextField(label="Дата выдачи удостоверения (дд.мм.гггг)", width=250, on_change=format_date_input, input_filter=ft.InputFilter(regex_string=r"[0-9.]", allow=True), max_length=10)
    edit_guard_rank = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option(str(i)) for i in range(3, 7)])

    # Диалог подтверждения удаления
    confirm_delete_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Подтвердите удаление"),
        content=ft.Text("Вы уверены, что хотите удалить этого сотрудника?"),
        actions=[
            ft.TextButton("Да", on_click=None), # Будет установлен динамически
            ft.TextButton("Отмена", on_click=lambda e: close_confirm_delete_dialog()),
        ]
    )

    def show_confirm_delete_dialog(employee_to_delete):
        confirm_delete_dialog.actions[0].on_click = lambda e: delete_employee(employee_to_delete)
        confirm_delete_dialog.open = True
        if page and confirm_delete_dialog not in page.overlay:
            page.overlay.append(confirm_delete_dialog)
        if page:
            page.update()

    def close_confirm_delete_dialog():
        confirm_delete_dialog.open = False
        if page:
            page.update()

    def delete_employee(employee):
        employee.delete_employee()
        close_confirm_delete_dialog()
        close_edit_dialog(None) # Закрываем диалог редактирования после удаления
        refresh_table()
        if page:
            page.update()

    def show_edit_dialog(employee):
        edit_name.value = employee.full_name
        edit_birth.value = format_date(employee.birth_date)
        edit_hire.value = format_date(employee.hire_date)
        edit_guard_license.value = format_date(employee.guard_license_date) if hasattr(employee, 'guard_license_date') else ""
        edit_guard_rank.value = str(employee.guard_rank) if hasattr(employee, 'guard_rank') and employee.guard_rank else None
        edit_dialog.title = ft.Text(f"Редактировать сотрудника")
        edit_dialog.content = ft.Column([
            edit_name,
            edit_birth,
            edit_hire,
            edit_guard_license,
            edit_guard_rank,
        ], spacing=10)
        edit_dialog.actions = [
            ft.TextButton("Сохранить", on_click=lambda e, emp=employee: save_edit_employee(emp)),
            ft.TextButton("Удалить", on_click=lambda e, emp=employee: show_confirm_delete_dialog(emp), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Отмена", on_click=close_edit_dialog),
        ]
        edit_dialog.open = True
        if page and edit_dialog not in page.overlay:
            page.overlay.append(edit_dialog)
        if page:
            page.update()
            
    def close_edit_dialog(e):
        edit_dialog.open = False
        if page:
            page.update()

    def save_edit_employee(employee):
        from datetime import datetime
        try:
            full_name = edit_name.value.strip()
            birth_value = edit_birth.value.strip()
            hire_value = edit_hire.value.strip()
            guard_license_value = edit_guard_license.value.strip()
            guard_rank_value = edit_guard_rank.value
            
            if not full_name:
                raise ValueError("ФИО обязательно!")
            if not birth_value or birth_value == "Не указано":
                raise ValueError("Дата рождения обязательна!")
            if not hire_value or hire_value == "Не указано":
                raise ValueError("Дата принятия на работу обязательна!")
            
            employee.full_name = full_name
            employee.birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
            employee.hire_date = datetime.strptime(hire_value, "%d.%m.%Y").date()
            employee.guard_license_date = datetime.strptime(guard_license_value, "%d.%m.%Y").date() if guard_license_value and guard_license_value != "Не указано" else None
            employee.guard_rank = int(guard_rank_value) if guard_rank_value else None
            employee.save()
            close_edit_dialog(None)
            refresh_table()
            if page:
                page.update()
        except ValueError as ex:
            edit_dialog.content = ft.Column([
                edit_name,
                edit_birth,
                edit_hire,
                edit_guard_license,
                edit_guard_rank,
                ft.Text(f"Ошибка: {str(ex)}", color=ft.Colors.RED)
            ], spacing=10)
        except Exception:
            pass
            # actions не меняем, чтобы не дублировались
            if page:
                page.update()

    def on_search_change(e):
        nonlocal search_value, current_page
        search_value = e.control.value.strip()
        current_page = 0  # Сброс на первую страницу при поиске
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
    
    # Создаем DataTable
    employees_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО", width=300), on_sort=lambda _: on_sort("full_name")),
            ft.DataColumn(ft.Text("Дата рождения", width=150), on_sort=lambda _: on_sort("birth_date")),
            ft.DataColumn(ft.Text("Дата принятия", width=150), on_sort=lambda _: on_sort("hire_date")),
            ft.DataColumn(ft.Text("Дата выдачи УЧО", width=150)),
            ft.DataColumn(ft.Text("Разряд", width=100)),
        ],
        rows=[],
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        heading_row_height=70,
        data_row_min_height=50,
        data_row_max_height=50,
        column_spacing=10,
        width=4000,
        height=707
    )
    refresh_table()
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Сотрудники", size=24, weight="bold"),
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
