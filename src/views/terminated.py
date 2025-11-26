import flet as ft
from database.models import Employee, db
from datetime import datetime

def format_date(date):
    """Форматирует дату в строку дд.мм.гггг"""
    return date.strftime("%d.%m.%Y") if date else "Не указано"

def terminated_page(page: ft.Page = None) -> ft.Column:
    search_value = ""
    
    # Диалог действий с сотрудником
    actions_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Действия с сотрудником"),
        content=ft.Column([], height=200),
        actions=[
            ft.TextButton("Вернуть", on_click=lambda e: restore_employee(current_employee), style=ft.ButtonStyle(color=ft.Colors.GREEN)),
            ft.TextButton("Редактировать", on_click=lambda e: show_edit_termination(current_employee)),
            ft.TextButton("Удалить", on_click=lambda e: delete_employee_permanently(current_employee), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Отмена", on_click=lambda e: close_actions_dialog())
        ]
    )
    
    # Диалог редактирования увольнения
    edit_termination_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Редактировать увольнение"),
        content=ft.Column([], height=150),
        actions=[
            ft.TextButton("Сохранить", on_click=lambda e: save_termination_changes()),
            ft.TextButton("Отмена", on_click=lambda e: close_edit_termination_dialog())
        ]
    )
    
    def format_date_input(e):
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
    
    edit_termination_date = ft.TextField(label="Дата увольнения", width=200, on_change=format_date_input, max_length=10)
    edit_termination_reason = ft.TextField(label="Причина увольнения", width=300, multiline=True)
    current_employee = None
    
    def show_employee_actions(employee):
        nonlocal current_employee
        current_employee = employee
        
        actions_dialog.title.value = f"Действия: {employee.full_name}"
        actions_dialog.content.controls = [
            ft.Text(f"Сотрудник: {employee.full_name}", weight="bold"),
            ft.Text(f"Дата увольнения: {format_date(employee.termination_date)}"),
            ft.Text(f"Причина: {getattr(employee, 'termination_reason', '') or 'Не указана'}"),
            ft.Text(f"Компания: {getattr(employee, 'company', 'Легион')}", size=16),
            ft.Divider(),
        ]
        
        actions_dialog.open = True
        if page and actions_dialog not in page.overlay:
            page.overlay.append(actions_dialog)
        if page:
            page.update()
    
    def close_actions_dialog():
        actions_dialog.open = False
        if page:
            page.update()
    
    def show_edit_termination(employee):
        edit_termination_date.value = format_date(employee.termination_date)
        edit_termination_reason.value = getattr(employee, 'termination_reason', '') or ''
        
        edit_termination_dialog.content.controls = [
            edit_termination_date,
            edit_termination_reason
        ]
        
        close_actions_dialog()
        edit_termination_dialog.open = True
        if page and edit_termination_dialog not in page.overlay:
            page.overlay.append(edit_termination_dialog)
        if page:
            page.update()
    
    def close_edit_termination_dialog():
        edit_termination_dialog.open = False
        if page:
            page.update()
    
    def save_termination_changes():
        try:
            if db.is_closed():
                db.connect()
            
            from datetime import datetime
            termination_date = datetime.strptime(edit_termination_date.value, "%d.%m.%Y").date()
            
            current_employee.termination_date = termination_date
            current_employee.termination_reason = edit_termination_reason.value or None
            current_employee.save()
            
            close_edit_termination_dialog()
            refresh_table()
        except Exception as ex:
            print(f"Ошибка сохранения: {ex}")
        finally:
            if not db.is_closed():
                db.close()
    
    def delete_employee_permanently(employee):
        try:
            if db.is_closed():
                db.connect()
            employee.delete_instance()
            close_actions_dialog()
            refresh_table()
        except Exception as ex:
            print(f"Ошибка удаления: {ex}")
        finally:
            if not db.is_closed():
                db.close()
    
    def get_terminated_employees():
        """Получает список уволенных сотрудников"""
        try:
            if db.is_closed():
                db.connect()
            
            from database.models import GuardEmployee, ChiefEmployee, OfficeEmployee
            
            # Получаем всех уволенных сотрудников
            all_terminated = []
            
            # Охранники
            guard_query = GuardEmployee.select().where(GuardEmployee.termination_date.is_null(False))
            if search_value:
                guard_query = guard_query.where(GuardEmployee.full_name.contains(search_value))
            all_terminated.extend(list(guard_query))
            
            # Начальники
            chief_query = ChiefEmployee.select().where(ChiefEmployee.termination_date.is_null(False))
            if search_value:
                chief_query = chief_query.where(ChiefEmployee.full_name.contains(search_value))
            all_terminated.extend(list(chief_query))
            
            # Офисные сотрудники
            office_query = OfficeEmployee.select().where(OfficeEmployee.termination_date.is_null(False))
            if search_value:
                office_query = office_query.where(OfficeEmployee.full_name.contains(search_value))
            all_terminated.extend(list(office_query))
            
            # Сортируем по имени
            all_terminated.sort(key=lambda emp: emp.full_name)
            
            return all_terminated
        except:
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def restore_employee(employee):
        """Восстанавливает сотрудника (убирает дату увольнения)"""
        try:
            if db.is_closed():
                db.connect()
            employee.termination_date = None
            employee.termination_reason = None
            employee.save()
            close_actions_dialog()
            refresh_table()
        except:
            pass
        finally:
            if not db.is_closed():
                db.close()
    
    def refresh_table():
        """Обновляет таблицу уволенных сотрудников"""
        terminated_employees = get_terminated_employees()
        terminated_table.rows.clear()
        
        for employee in terminated_employees:
            terminated_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(employee.full_name), on_tap=lambda e, emp=employee: show_employee_actions(emp)),
                        ft.DataCell(ft.Text(format_date(employee.termination_date))),
                        ft.DataCell(ft.Text(getattr(employee, 'termination_reason', '') or 'Не указана')),
                        ft.DataCell(ft.Text(getattr(employee, 'company', 'Легион'))),
                    ]
                )
            )
        
        if page:
            page.update()
    
    def on_search_change(e):
        nonlocal search_value
        search_value = e.control.value.strip()
        refresh_table()
    
    # Создаем таблицу
    terminated_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО", width=200)),
            ft.DataColumn(ft.Text("Дата увольнения", width=150)),
            ft.DataColumn(ft.Text("Причина увольнения", width=300)),
            ft.DataColumn(ft.Text("Компания", width=100)),
        ],
        rows=[],
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        heading_row_height=70,
        data_row_min_height=50,
        data_row_max_height=50,
        column_spacing=10,
        width=4000,
    )
    
    refresh_table()
    
    return ft.Column([
        ft.Text("Уволенные сотрудники", size=24, weight="bold"),
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
            content=ft.Column([terminated_table], scroll=ft.ScrollMode.AUTO),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            padding=10,
            expand=True,
        ),
    ], spacing=10, expand=True)