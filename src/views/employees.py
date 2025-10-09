import flet as ft
from database.models import Employee, db
from database.utils import add_test_employees, clear_employees
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
    global employees_table
    
    def add_employee(e):
        """Обработчик нажатия кнопки Добавить"""
        add_test_employees()
        refresh_table()
        if page:
            page.update()
    
    def clear_all(e):
        """Обработчик нажатия кнопки Очистить"""
        clear_employees()
        refresh_table()
        if page:
            page.update()
    
    def refresh_table():
        """Обновляет данные в таблице"""
        employees_list = load_employees()
        employees_table.rows.clear()
        
        for employee in employees_list:
            employees_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(employee.full_name)),
                        ft.DataCell(ft.Text(format_date(employee.birth_date))),
                        ft.DataCell(ft.Text(format_date(employee.hire_date))),
                        ft.DataCell(ft.Text(format_salary(employee.salary))),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    "Работает" if employee.is_active() else "Уволен",
                                    color=ft.Colors.GREEN if employee.is_active() else ft.Colors.RED,
                                ),
                                padding=ft.padding.all(5),
                            )
                        ),
                    ]
                )
            )
    
    # Загружаем сотрудников
    employees_list = load_employees()
    
    # Создаем DataTable
    employees_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ФИО", width=300)),
            ft.DataColumn(ft.Text("Дата рождения", width=150)),
            ft.DataColumn(ft.Text("Дата принятия", width=150)),
            ft.DataColumn(ft.Text("Зарплата", width=150)),
            ft.DataColumn(ft.Text("Статус", width=100)),
        ],
        rows=[],
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),  # Горизонтальные линии
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),    # Вертикальные линии
        heading_row_height=70,  # Высота заголовка
        data_row_min_height=50, # Минимальная высота строк с данными
        data_row_max_height=100,# Максимальная высота строк
        column_spacing=10,      # Отступы между колонками
        width=4000,  # Общая ширина таблицы
        height=4000  # Высота таблицы с возможностью прокрутки
    )
    
    # Добавляем строки с данными
    for employee in employees_list:
        employees_table.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(employee.full_name)),
                    ft.DataCell(ft.Text(format_date(employee.birth_date))),
                    ft.DataCell(ft.Text(format_date(employee.hire_date))),
                    ft.DataCell(ft.Text(format_salary(employee.salary))),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(
                                "Работает" if employee.is_active() else "Уволен",
                                color=ft.Colors.GREEN if employee.is_active() else ft.Colors.RED,
                            ),
                            padding=ft.padding.all(5),
                        )
                    ),
                ]
            )
        )
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Сотрудники", size=24, weight="bold"),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Добавить тестовых",
                                icon=ft.Icons.ADD,
                                on_click=add_employee,
                            ),
                            ft.ElevatedButton(
                                "Очистить",
                                icon=ft.Icons.DELETE,
                                on_click=clear_all,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Container(
                content=employees_table,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10,
                expand=True,  # Растягиваем контейнер
            ),
        ],
        spacing=10,
        expand=True,
    )
