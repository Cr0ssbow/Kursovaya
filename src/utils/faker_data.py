from faker import Faker
from database.models import Employee, Object, Assignment, CashWithdrawal, Company, EmployeeCompany, ChiefEmployee, OfficeEmployee, db
from datetime import datetime, date, timedelta
import random

fake = Faker('ru_RU')

def create_fake_employees(count=100):
    """Создает тестовых сотрудников"""
    employees = []
    for _ in range(count):
        employee = Employee.create(
            full_name=fake.name(),
            phone=fake.phone_number(),
            address=fake.address(),
            passport_series=fake.random_int(1000, 9999),
            passport_number=fake.random_int(100000, 999999),
            passport_issued_by=fake.company(),
            passport_issued_date=fake.date_between(start_date='-10y', end_date='-1y'),
            birth_date=fake.date_between(start_date='-65y', end_date='-18y'),
            position=random.choice(['Охранник', 'Старший охранник', 'Начальник смены']),
            hire_date=fake.date_between(start_date='-2y', end_date='today'),
            salary=random.randint(25000, 45000),
            certificate_number=f"{fake.random_int(100000, 999999)}-ОХ",
            guard_license_date=fake.date_between(start_date='-5y', end_date='-1y'),
            guard_rank=random.choice(['4', '5', '6']),
            medical_exam_date=fake.date_between(start_date='-1y', end_date='today'),
            periodic_check_date=fake.date_between(start_date='-2y', end_date='today'),
            payment_method="на карту",
            is_chief=random.choice([True, False]),
            is_office=random.choice([True, False])
        )
        employees.append(employee)
        
        # Привязываем к случайной компании
        companies = list(Company.select())
        if companies:
            company = random.choice(companies)
            EmployeeCompany.create(
                guard_employee=employee,
                company=company
            )
    return employees

def create_fake_objects(count=5):
    """Создает тестовые объекты"""
    objects = []
    for _ in range(count):
        obj = Object.create(
            name=fake.company(),
            address=fake.address(),
            contact_person=fake.name(),
            phone=fake.phone_number()
        )
        objects.append(obj)
    return objects

def create_fake_assignments(employees, objects, days=30):
    """Создает тестовые назначения на смены"""
    assignments = []
    start_date = date.today() - timedelta(days=days)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        for employee in employees:
            if random.random() < 0.7:  # 70% вероятность работы
                obj = random.choice(objects)
                hours = random.choice([8, 12, 24])
                hourly_rate = random.randint(150, 250)
                
                assignment = Assignment.create(
                    employee=employee,
                    object=obj,
                    date=current_date,
                    hours=hours,
                    hourly_rate=hourly_rate,
                    is_absent=random.random() < 0.1,  # 10% пропусков
                    bonus_amount=random.randint(0, 1000) if random.random() < 0.2 else 0,
                    deduction_amount=random.randint(0, 500) if random.random() < 0.1 else 0,
                    bonus_comment=fake.sentence() if random.random() < 0.2 else "",
                    absent_comment=fake.sentence() if random.random() < 0.1 else ""
                )
                assignments.append(assignment)
    
    return assignments

def create_fake_cash_withdrawals(employees, objects, days=30):
    """Создает тестовые записи ВЗН"""
    withdrawals = []
    start_date = date.today() - timedelta(days=days)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        for employee in employees:
            if random.random() < 0.3:  # 30% вероятность ВЗН
                obj = random.choice(objects)
                hours = random.choice([4, 6, 8])
                hourly_rate = random.randint(200, 300)
                
                withdrawal = CashWithdrawal.create(
                    employee=employee,
                    object=obj,
                    date=current_date,
                    hours=hours,
                    hourly_rate=hourly_rate,
                    is_absent=random.random() < 0.05,  # 5% пропусков ВЗН
                    bonus_amount=random.randint(0, 500) if random.random() < 0.15 else 0,
                    deduction_amount=random.randint(0, 300) if random.random() < 0.08 else 0,
                    bonus_comment=fake.sentence() if random.random() < 0.15 else ""
                )
                withdrawals.append(withdrawal)
    
    return withdrawals

def create_december_shifts():
    """Создает 10 смен на каждый день декабря"""
    try:
        if db.is_closed():
            db.connect()
        
        employees = list(Employee.select())
        objects = list(Object.select())
        
        if not employees or not objects:
            print("Нет сотрудников или объектов")
            return
        
        print("Создание смен на весь декабрь...")
        
        import calendar
        days_in_december = calendar.monthrange(2025, 12)[1]  # Получаем количество дней в декабре
        
        for day in range(1, days_in_december + 1):  # Декабрь 1-31
            current_date = date(2025, 12, day)
            print(f"Создание смен на {day} декабря...")
            
            for _ in range(100):  # 100 смен на день
                employee = random.choice(employees)
                obj = random.choice(objects)
                hours = random.choice([8, 12, 24])
                hourly_rate = random.randint(150, 250)
                
                Assignment.create(
                    employee=employee,
                    object=obj,
                    date=current_date,
                    hours=hours,
                    hourly_rate=hourly_rate,
                    is_absent=random.random() < 0.1,
                    bonus_amount=random.randint(0, 1000) if random.random() < 0.2 else 0,
                    deduction_amount=random.randint(0, 500) if random.random() < 0.1 else 0,
                    bonus_comment=fake.sentence() if random.random() < 0.2 else "",
                    absent_comment=fake.sentence() if random.random() < 0.1 else ""
                )
        
        print("Смены на весь декабрь созданы!")
        
    except Exception as e:
        print(f"Ошибка при создании смен: {e}")
    finally:
        if not db.is_closed():
            db.close()

def create_fake_chiefs(count=100):
    """Создает тестовых начальников охраны"""
    chiefs = []
    for _ in range(count):
        chief = ChiefEmployee.create(
            full_name=fake.name(),
            birth_date=fake.date_between(start_date='-65y', end_date='-25y'),
            position=random.choice(['Начальник охраны', 'Старший начальник охраны']),
            guard_rank=random.choice(['5', '6']),
            salary=random.randint(50000, 80000),
            payment_method="на карту"
        )
        chiefs.append(chief)
        
        # Привязываем к случайной компании
        companies = list(Company.select())
        if companies:
            company = random.choice(companies)
            EmployeeCompany.create(
                chief_employee=chief,
                company=company
            )
    return chiefs

def create_fake_office_employees(count=100):
    """Создает тестовых сотрудников офиса"""
    office_employees = []
    for _ in range(count):
        office_emp = OfficeEmployee.create(
            full_name=fake.name(),
            birth_date=fake.date_between(start_date='-65y', end_date='-18y'),
            position=random.choice(['Менеджер', 'Бухгалтер', 'Кадровик', 'Секретарь', 'Юрист']),
            salary=random.randint(30000, 60000),
            payment_method="на карту"
        )
        office_employees.append(office_emp)
        
        # Привязываем к случайной компании
        companies = list(Company.select())
        if companies:
            company = random.choice(companies)
            EmployeeCompany.create(
                office_employee=office_emp,
                company=company
            )
    return office_employees

def generate_all_fake_data():
    """Генерирует все тестовые данные"""
    try:
        if db.is_closed():
            db.connect()
        
        print("Создание тестовых сотрудников...")
        employees = create_fake_employees(100)
        
        print("Создание начальников охраны...")
        chiefs = create_fake_chiefs(100)
        
        print("Создание сотрудников офиса...")
        office_employees = create_fake_office_employees(100)
        
        print("Создание тестовых объектов...")
        objects = create_fake_objects(8)
        
        print("Создание тестовых назначений...")
        assignments = create_fake_assignments(employees, objects, 60)
        
        print("Создание тестовых ВЗН...")
        withdrawals = create_fake_cash_withdrawals(employees, objects, 60)
        
        print(f"Создано: {len(employees)} сотрудников, {len(chiefs)} начальников, {len(office_employees)} офисных сотрудников, {len(objects)} объектов, {len(assignments)} назначений, {len(withdrawals)} ВЗН")
        
    except Exception as e:
        print(f"Ошибка при создании тестовых данных: {e}")
    finally:
        if not db.is_closed():
            db.close()