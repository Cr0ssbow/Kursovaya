import flet as ft
from database.models import Employee, db
from datetime import datetime

def load_employees():
    """Загружает список сотрудников из БД"""
    return Employee.select().order_by(Employee.full_name)

def format_date(date):
    """Форматирует дату в строку дд.мм.гггг"""
    return date.strftime("%d.%m.%Y") if date else "Не указано"

def format_salary(salary):
    """Форматирует зарплату в строку с разделителями"""
    return f"{float(salary):,.2f}".replace(",", " ").replace(".", ",") + " ₽"

employees_table = None

def employees_page(page: ft.Page = None) -> ft.Column:
    sort_column = "full_name"
    sort_reverse = False
    global employees_table
    
    # Диалог и поля формы
    add_dialog = ft.AlertDialog(modal=True)
    name_field = ft.TextField(label="ФИО", width=300)
    birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180)
    hire_field = ft.TextField(label="Дата принятия (дд.мм.гггг)", width=180)
    salary_field = ft.TextField(label="Зарплата", width=120)

    def show_add_dialog(e):
        add_dialog.title = ft.Text("Добавить сотрудника")
        add_dialog.content = ft.Column([
            name_field,
            birth_field,
            hire_field,
            salary_field,
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
            birth_date = datetime.strptime(birth_field.value.strip(), "%d.%m.%Y").date()
            hire_date = datetime.strptime(hire_field.value.strip(), "%d.%m.%Y").date()
            salary = float(salary_field.value.strip().replace(",", "."))
            if not full_name:
                raise ValueError("ФИО обязательно!")
            Employee.create(
                full_name=full_name,
                birth_date=birth_date,
                hire_date=hire_date,
                salary=salary
            )
            close_add_dialog(e)
            refresh_table()
            if page:
                page.update()
        except Exception as ex:
            add_dialog.content = ft.Column([
                name_field,
                birth_field,
                hire_field,
                salary_field,
                ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)
            ], spacing=10)
            # actions не меняем, чтобы не дублировались
            if page:
                page.update()
    
    search_value = ""

    def refresh_table():
        """Обновляет данные в таблице с учетом поиска"""
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
        employees_table.rows.clear()
        for employee in employees_list:
            employees_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(employee.full_name), on_tap=lambda e, emp=employee: show_edit_dialog(emp)),
                        ft.DataCell(ft.Text(format_date(employee.birth_date))),
                        ft.DataCell(ft.Text(format_date(employee.hire_date))),
                        ft.DataCell(ft.Text(format_salary(employee.salary))),
                    ]
                )
            )
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
    edit_birth = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180)
    edit_hire = ft.TextField(label="Дата принятия (дд.мм.гггг)", width=180)
    edit_salary = ft.TextField(label="Зарплата", width=120)

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
        edit_salary.value = str(employee.salary)
        edit_dialog.title = ft.Text(f"Редактировать сотрудника")
        edit_dialog.content = ft.Column([
            edit_name,
            edit_birth,
            edit_hire,
            edit_salary,
        ], spacing=10)
        edit_dialog.actions = [
            ft.TextButton("Сохранить", on_click=lambda e, emp=employee: save_edit_employee(emp)),
            ft.TextButton("Удалить", on_click=lambda e, emp=employee: show_confirm_delete_dialog(emp), style=ft.ButtonStyle(color=ft.colors.RED)),
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
            employee.full_name = edit_name.value.strip()
            employee.birth_date = datetime.strptime(edit_birth.value.strip(), "%d.%m.%Y").date()
            employee.hire_date = datetime.strptime(edit_hire.value.strip(), "%d.%m.%Y").date()
            employee.salary = float(edit_salary.value.strip().replace(",", "."))
            employee.save()
            close_edit_dialog(None)
            refresh_table()
            if page:
                page.update()
        except Exception as ex:
            edit_dialog.content = ft.Column([
                edit_name,
                edit_birth,
                edit_hire,
                edit_salary,
                ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)
            ], spacing=10)
            # actions не меняем, чтобы не дублировались
            if page:
                page.update()

    def on_search_change(e):
        nonlocal search_value
        search_value = e.control.value.strip()
        refresh_table()
        if page:
            page.update()
    
    # Создаем DataTable
    employees_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО", width=300), on_sort=lambda _: on_sort("full_name")),
            ft.DataColumn(ft.Text("Дата рождения", width=150), on_sort=lambda _: on_sort("birth_date")),
            ft.DataColumn(ft.Text("Дата принятия", width=150), on_sort=lambda _: on_sort("hire_date")),
            ft.DataColumn(ft.Text("Зарплата", width=150), on_sort=lambda _: on_sort("salary")),
        ],
        rows=[],
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        heading_row_height=70,
        data_row_min_height=50,
        data_row_max_height=100,
        column_spacing=10,
        width=4000,
        height=4000
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
                content=employees_table,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10,
                expand=True,
            ),
        ],
        spacing=10,
        expand=True,
    )
