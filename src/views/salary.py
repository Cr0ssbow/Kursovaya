import flet as ft
from database.models import Employee, Assignment, db
from datetime import datetime, date

def salary_page(page: ft.Page = None) -> ft.Column:
    # Текущий месяц и год
    current_date = date.today()
    selected_month = current_date.month
    selected_year = current_date.year
    
    salary_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО", width=300)),
            ft.DataColumn(ft.Text("Зарплата", width=150)),
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
    
    # Поле поиска по ФИО
    search_field = ft.TextField(
        label="Поиск по ФИО",
        width=200,
        on_change=lambda e: refresh_salary_table()
    )
    
    def refresh_salary_table():
        """Обновляет данные зарплат за выбранный месяц"""
        try:
            if db.is_closed():
                db.connect()
            
            # Фильтрация по ФИО
            search_value = search_field.value.strip()
            if search_value:
                employees = Employee.select().where(Employee.full_name.contains(search_value))
            else:
                employees = Employee.select()
            
            salary_table.rows.clear()
            for employee in employees:
                # Вычисляем зарплату за выбранный месяц
                assignments = Assignment.select().where(
                    (Assignment.employee == employee) &
                    (Assignment.date.month == selected_month) &
                    (Assignment.date.year == selected_year)
                )
                total_salary = sum(float(a.hourly_rate) * a.hours + float(a.bonus_amount) for a in assignments if not a.is_absent)
                
                salary_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(employee.full_name)),
                            ft.DataCell(ft.Text(f"{total_salary:.2f} ₽")),
                        ]
                    )
                )
            
            if not db.is_closed():
                db.close()
        except Exception as e:
            print(f"Ошибка при загрузке зарплат: {e}")
        
        if page:
            page.update()
    
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
        refresh_salary_table()
    
    month_display = ft.Text(f"{selected_month:02d}.{selected_year}", size=20, weight="bold")
    
    refresh_salary_table()
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Зарплата", size=24, weight="bold"),
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: change_month(-1)),
                        month_display,
                        ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: change_month(1)),
                        search_field,
                    ], spacing=5),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Container(
                content=ft.Column([
                    salary_table
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