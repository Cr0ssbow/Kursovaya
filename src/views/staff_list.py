import flet as ft
from database.models import GuardEmployee, ChiefEmployee, Assignment
from peewee import fn

def staff_list_page(page: ft.Page):
    """Страница актуального перечня штатного состава"""
    
    # Получаем всех активных начальников охраны
    chief_employees = ChiefEmployee.select().where(ChiefEmployee.termination_date.is_null())
    
    rows = []
    
    for chief in chief_employees:
        # Получаем всех сотрудников охраны, которые созданы этим начальником (через created_by_user_id)
        from database.models import User
        try:
            # Находим пользователя, связанного с этим начальником
            user = User.get(User.chief_employee == chief)
            subordinates = GuardEmployee.select().where(
                (GuardEmployee.created_by_user_id == user.id) & 
                (GuardEmployee.termination_date.is_null())
            )
        except User.DoesNotExist:
            # Если нет связанного пользователя, проверяем через Assignment
            subordinates = GuardEmployee.select().join(Assignment).where(
                (Assignment.chief == chief) & 
                (GuardEmployee.termination_date.is_null())
            ).distinct()
        
        total_staff = len(subordinates)  # Общее количество людей в штате
        
        # Количество трудоустроенных (в штате)
        employed_count = len([emp for emp in subordinates if getattr(emp, 'staff_status', 'в штате') == 'в штате'])
        
        # Количество людей с уголовной/административной ответственностью
        criminal_count = len([emp for emp in subordinates if getattr(emp, 'criminal_liability', 'нет') == 'да'])
        
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(chief.full_name)),
                    ft.DataCell(ft.Text(str(total_staff))),
                    ft.DataCell(ft.Text(str(employed_count))),
                    ft.DataCell(ft.Text(str(criminal_count))),
                ]
            )
        )
    
    # Создаем таблицу
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО начальника охраны")),
            ft.DataColumn(ft.Text("Штат")),
            ft.DataColumn(ft.Text("Трудоустроено")),
            ft.DataColumn(ft.Text("С ответственностью")),
        ],
        rows=rows,
        border=ft.border.all(1, ft.Colors.OUTLINE),
        border_radius=10,
    )
    
    return ft.Column([
        ft.Text("Актуальный перечень штатного состава", size=24, weight="bold"),
        ft.Divider(),
        ft.Container(
            content=data_table,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            padding=10,
        )
    ], scroll=ft.ScrollMode.AUTO, expand=True)