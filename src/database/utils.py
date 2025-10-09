from datetime import datetime, date
from decimal import Decimal
from peewee import DoesNotExist
from .models import Employee, db, Settings

def add_test_employees():
    """Добавляет тестовых сотрудников в базу данных"""
    test_employees = [
        {
            'full_name': 'Иванов Иван Иванович',
            'birth_date': date(1990, 5, 15),
            'hire_date': date(2020, 3, 1),
            'salary': Decimal('75000.00')
        },
        {
            'full_name': 'Петрова Мария Александровна',
            'birth_date': date(1985, 8, 23),
            'hire_date': date(2019, 7, 15),
            'salary': Decimal('85000.00')
        },
        {
            'full_name': 'Сидоров Алексей Петрович',
            'birth_date': date(1993, 12, 7),
            'hire_date': date(2021, 1, 10),
            'termination_date': date(2023, 6, 30),
            'salary': Decimal('65000.00')
        }
    ]
    
    with db.atomic():
        for emp_data in test_employees:
            # Проверяем, существует ли сотрудник с таким именем
            employee, created = Employee.get_or_create(
                full_name=emp_data['full_name'],
                defaults=emp_data
            )
            if created:
                print(f"Добавлен сотрудник: {employee.full_name}")
            else:
                print(f"Сотрудник уже существует: {employee.full_name}")

def clear_employees():
    """Удаляет всех сотрудников из базы данных"""
    query = Employee.delete()
    deleted = query.execute()
    print(f"Удалено {deleted} сотрудников")

def save_theme_to_db(theme: str):
    Settings.insert(key="theme", value=theme).on_conflict_replace().execute()

def load_theme_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "theme")
        return setting.value
    except DoesNotExist:
        return "light"