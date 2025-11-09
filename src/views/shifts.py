import flet as ft
from database.models import Assignment, Employee, Object, db
from datetime import datetime

def shifts_page(page: ft.Page = None) -> ft.Column:
    # Текущий месяц и год
    from datetime import date
    current_date = date.today()
    selected_month = current_date.month
    selected_year = current_date.year
    
    shifts_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Дата", width=100)),
            ft.DataColumn(ft.Text("Сотрудник", width=200)),
            ft.DataColumn(ft.Text("Объект", width=200)),
            ft.DataColumn(ft.Text("Часы", width=80)),
            ft.DataColumn(ft.Text("Ставка", width=100)),
            ft.DataColumn(ft.Text("Действия", width=100)),
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
    
    def refresh_shifts():
        """Обновляет список смен за выбранный месяц"""
        try:
            if db.is_closed():
                db.connect()
            
            assignments = Assignment.select().join(Employee).switch(Assignment).join(Object).where(
                (Assignment.date.month == selected_month) &
                (Assignment.date.year == selected_year)
            ).order_by(Assignment.date.desc())
            
            shifts_table.rows.clear()
            for assignment in assignments:
                shifts_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(assignment.date.strftime("%d.%m.%Y"))),
                            ft.DataCell(ft.Text(assignment.employee.full_name)),
                            ft.DataCell(ft.Text(assignment.object.name)),
                            ft.DataCell(ft.Text(str(assignment.hours))),
                            ft.DataCell(ft.Text(f"{float(assignment.hourly_rate):.2f} ₽")),
                            ft.DataCell(
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, a=assignment: delete_shift(a)
                                )
                            ),
                        ]
                    )
                )
            
            if not db.is_closed():
                db.close()
        except Exception as e:
            print(f"Ошибка при загрузке смен: {e}")
        
        if page:
            page.update()
    
    # Диалог подтверждения удаления
    confirm_delete_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Подтвердите удаление"),
        content=ft.Text("Вы уверены, что хотите удалить эту смену?"),
        actions=[
            ft.TextButton("Да", on_click=None),
            ft.TextButton("Отмена", on_click=lambda e: close_confirm_dialog()),
        ],
    )
    
    def show_confirm_delete(assignment):
        confirm_delete_dialog.actions[0].on_click = lambda e: confirm_delete_shift(assignment)
        page.dialog = confirm_delete_dialog
        confirm_delete_dialog.open = True
        page.update()
    
    def close_confirm_dialog():
        confirm_delete_dialog.open = False
        page.dialog = None
        page.update()
    
    def confirm_delete_shift(assignment):
        try:
            if db.is_closed():
                db.connect()
            assignment.delete_instance()
            if not db.is_closed():
                db.close()
            close_confirm_dialog()
            refresh_shifts()
        except Exception as e:
            print(f"Ошибка при удалении смены: {e}")
    
    def delete_shift(assignment):
        """Показывает диалог подтверждения удаления"""
        show_confirm_delete(assignment)
    
    def change_month(delta):
        nonlocal selected_month, selected_year
        selected_month += delta
        if selected_month > 12:
            selected_month = 1
            selected_year += 1
        elif selected_month < 1:
            selected_month = 12
            selected_year -= 1
        month_display.value = f"{selected_month:02d}.{selected_year}"
        apply_filters()
    
    month_display = ft.Text(f"{selected_month:02d}.{selected_year}", size=20, weight="bold")
    
    def apply_filters():
        """Применяет все фильтры одновременно"""
        try:
            if db.is_closed():
                db.connect()
            
            query = Assignment.select().join(Employee).switch(Assignment).join(Object)
            conditions = []
            
            # Фильтр по дате
            date_value = date_field.value.strip()
            if date_value and len(date_value) == 10:
                try:
                    filter_date = datetime.strptime(date_value, "%d.%m.%Y").date()
                    conditions.append(Assignment.date == filter_date)
                except:
                    pass
            else:
                conditions.append(Assignment.date.month == selected_month)
                conditions.append(Assignment.date.year == selected_year)
            
            # Фильтр по сотруднику
            employee_value = employee_field.value.strip()
            if employee_value:
                conditions.append(Employee.full_name.contains(employee_value))
            
            # Фильтр по объекту
            object_value = object_field.value.strip()
            if object_value:
                conditions.append(Object.name.contains(object_value))
            
            if conditions:
                query = query.where(*conditions)
            
            assignments = query.order_by(Assignment.date.desc())
            update_table(assignments)
            
            if not db.is_closed():
                db.close()
        except Exception as e:
            print(f"Ошибка при фильтрации: {e}")
            refresh_shifts()
    
    def format_date_input(e):
        """Автоматически форматирует ввод даты"""
        value = e.control.value.replace(".", "")
        if len(value) == 8 and value.isdigit():
            formatted = f"{value[:2]}.{value[2:4]}.{value[4:]}"
            e.control.value = formatted
            e.control.update()
        apply_filters()
    
    # Поле выбора конкретной даты
    date_field = ft.TextField(
        label="Дата (дд.мм.гггг)",
        width=150,
        on_change=format_date_input
    )
    
    # Поле поиска по сотруднику
    employee_field = ft.TextField(
        label="Сотрудник",
        width=150,
        on_change=lambda e: filter_by_employee(e.control.value)
    )
    
    # Поле поиска по объекту
    object_field = ft.TextField(
        label="Объект",
        width=150,
        on_change=lambda e: filter_by_object(e.control.value)
    )
    
    def filter_by_employee(employee_name):
        apply_filters()
    
    def filter_by_object(object_name):
        apply_filters()
    
    def update_table(assignments):
        shifts_table.rows.clear()
        for assignment in assignments:
            shifts_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(assignment.date.strftime("%d.%m.%Y"))),
                        ft.DataCell(ft.Text(assignment.employee.full_name)),
                        ft.DataCell(ft.Text(assignment.object.name)),
                        ft.DataCell(ft.Text(str(assignment.hours))),
                        ft.DataCell(ft.Text(f"{float(assignment.hourly_rate):.2f} ₽")),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, a=assignment: delete_shift(a)
                            )
                        ),
                    ]
                )
            )
        if page:
            page.update()
    
    def filter_by_date(date_str):
        if not date_str:
            refresh_shifts()
            return
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            
            if db.is_closed():
                db.connect()
            
            assignments = Assignment.select().join(Employee).switch(Assignment).join(Object).where(
                Assignment.date == filter_date
            ).order_by(Assignment.date.desc())
            
            shifts_table.rows.clear()
            for assignment in assignments:
                shifts_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(assignment.date.strftime("%d.%m.%Y"))),
                            ft.DataCell(ft.Text(assignment.employee.full_name)),
                            ft.DataCell(ft.Text(assignment.object.name)),
                            ft.DataCell(ft.Text(str(assignment.hours))),
                            ft.DataCell(ft.Text(f"{float(assignment.hourly_rate):.2f} ₽")),
                            ft.DataCell(
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, a=assignment: delete_shift(a)
                                )
                            ),
                        ]
                    )
                )
            
            if not db.is_closed():
                db.close()
            
            if page:
                page.update()
        except:
            refresh_shifts()
    
    refresh_shifts()
    
    shifts_content = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Смены", size=24, weight="bold"),
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: change_month(-1)),
                        month_display,
                        ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: change_month(1)),
                        date_field,
                        employee_field,
                        object_field,
                    ], spacing=5),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Container(
                content=ft.Column([
                    shifts_table
                ], scroll=ft.ScrollMode.AUTO),
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10,
                expand=True,
            ),
        ],
        spacing=10,
        expand=True,
    )
    
    return shifts_content, confirm_delete_dialog