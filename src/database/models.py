from peewee import *
from datetime import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настройки подключения к PostgreSQL
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_NAME = os.getenv('DB_NAME', 'legion_employees')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')
# Инициализация базы данных PostgreSQL
db = PostgresqlDatabase(
    DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    options='-c client_encoding=utf8'
)

class BaseModel(Model):
    class Meta:
        database = db

class Settings(BaseModel):
    key = CharField(unique=True)
    value = CharField()

class Company(BaseModel):
    """Модель компании"""
    name = CharField(max_length=50, unique=True, verbose_name="Название компании")
    
    class Meta:
        table_name = 'companies'

class GuardEmployee(BaseModel):
    @classmethod
    def exists_by_name(cls, full_name: str) -> bool:
        return cls.select().where(cls.full_name == full_name).exists()
    """Модель сотрудника охраны"""
    full_name = CharField(max_length=200, verbose_name="ФИО")
    birth_date = DateField(verbose_name="Дата рождения")
    photo_path = CharField(max_length=500, null=True, verbose_name="Путь к фото")
    certificate_number = CharField(max_length=20, null=True, verbose_name="Номер удостоверения")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    termination_reason = TextField(null=True, verbose_name="Причина увольнения")
    guard_license_date = DateField(null=True, verbose_name="Дата выдачи удостоверения охранника")
    guard_rank = CharField(max_length=10, null=True, verbose_name="Разряд охранника")
    medical_exam_date = DateField(null=True, verbose_name="Дата прохождения медкомиссии")
    periodic_check_date = DateField(null=True, verbose_name="Дата периодической проверки")
    hours_worked = IntegerField(verbose_name="Количество часов", default=0)
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    payment_method = CharField(max_length=20, default="на карту", verbose_name="Способ выдачи зарплаты")
    
    class Meta:
        table_name = 'guard_employees'
        
    def is_active(self):
        """Проверка, работает ли сотрудник"""
        return self.termination_date is None

    def calc_salary(self):
        """Расчет зарплаты с учетом прогулов, премий и удержаний"""
        total_salary = 0
        total_hours = 0
        
        for assignment in self.assignments:
            if not assignment.is_absent:
                total_salary += float(assignment.hourly_rate) * assignment.hours
                total_hours += assignment.hours
            total_salary += float(assignment.bonus_amount) - float(assignment.deduction_amount)
        
        return total_salary, total_hours

    def delete_employee(self):
        """Удаление сотрудника из базы данных"""
        self.delete_instance()

class ChiefEmployee(BaseModel):
    @classmethod
    def exists_by_name(cls, full_name: str) -> bool:
        return cls.select().where(cls.full_name == full_name).exists()
    """Модель начальника охраны"""
    full_name = CharField(max_length=200, verbose_name="ФИО")
    birth_date = DateField(verbose_name="Дата рождения")
    photo_path = CharField(max_length=500, null=True, verbose_name="Путь к фото")
    position = CharField(max_length=100, verbose_name="Должность")
    guard_rank = CharField(max_length=10, null=True, verbose_name="Разряд охранника")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    termination_reason = TextField(null=True, verbose_name="Причина увольнения")
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    payment_method = CharField(max_length=20, default="на карту", verbose_name="Способ выдачи зарплаты")
    
    class Meta:
        table_name = 'chief_employees'
        
    def is_active(self):
        return self.termination_date is None

class OfficeEmployee(BaseModel):
    @classmethod
    def exists_by_name(cls, full_name: str) -> bool:
        return cls.select().where(cls.full_name == full_name).exists()
    """Модель сотрудника офиса"""
    full_name = CharField(max_length=200, verbose_name="ФИО")
    birth_date = DateField(verbose_name="Дата рождения")
    photo_path = CharField(max_length=500, null=True, verbose_name="Путь к фото")
    position = CharField(max_length=100, verbose_name="Должность")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    termination_reason = TextField(null=True, verbose_name="Причина увольнения")
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    payment_method = CharField(max_length=20, default="на карту", verbose_name="Способ выдачи зарплаты")
    
    class Meta:
        table_name = 'office_employees'
        
    def is_active(self):
        return self.termination_date is None

# Для обратной совместимости
Employee = GuardEmployee

class Object(BaseModel):
    """Модель объекта"""
    name = CharField(max_length=200, unique=True, verbose_name="Название объекта")
    description = TextField(null=True, verbose_name="Описание")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'objects'

class ObjectAddress(BaseModel):
    """Модель адресов объекта"""
    object = ForeignKeyField(Object, backref='addresses', on_delete='CASCADE')
    address = CharField(max_length=500, verbose_name="Адрес")
    is_primary = BooleanField(default=False, verbose_name="Основной адрес")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'object_addresses'

class ObjectRate(BaseModel):
    """Модель почасовых ставок объекта"""
    object = ForeignKeyField(Object, backref='rates', on_delete='CASCADE')
    rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка")
    description = CharField(max_length=200, null=True, verbose_name="Описание ставки")
    is_default = BooleanField(default=False, verbose_name="Ставка по умолчанию")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'object_rates'

class Assignment(BaseModel):
    """Модель назначения сотрудника на объект"""
    employee = ForeignKeyField(GuardEmployee, backref='assignments', on_delete='CASCADE') # связь один ко многим employee (1) → (многоо) Assignment
    object = ForeignKeyField(Object, backref='assignments', on_delete='CASCADE') # связь один ко многим Object (1) → (многоо) Assignment
    chief = ForeignKeyField(ChiefEmployee, backref='supervised_assignments', on_delete='SET NULL', null=True, verbose_name="Начальник охраны")
    date = DateField(verbose_name="Дата назначения")
    hours = IntegerField(verbose_name="Количество часов")
    hourly_rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка")
    is_absent = BooleanField(default=False, verbose_name="Прогул")
    absent_comment = TextField(null=True, verbose_name="Комментарий к прогулу")
    deduction_amount = DecimalField(max_digits=7, decimal_places=2, default=0, verbose_name="Сумма удержания")
    bonus_amount = DecimalField(max_digits=7, decimal_places=2, default=0, verbose_name="Сумма премии")
    bonus_comment = TextField(null=True, verbose_name="Комментарий к премии")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'assignments'

class EmployeeCompany(BaseModel):
    """Модель связи сотрудник-компания"""
    guard_employee = ForeignKeyField(GuardEmployee, backref='companies', on_delete='CASCADE', null=True)
    chief_employee = ForeignKeyField(ChiefEmployee, backref='companies', on_delete='CASCADE', null=True)
    office_employee = ForeignKeyField(OfficeEmployee, backref='companies', on_delete='CASCADE', null=True)
    company = ForeignKeyField(Company, backref='employees', on_delete='CASCADE')
    
    class Meta:
        table_name = 'employee_companies'

class ChiefObjectAssignment(BaseModel):
    """Модель назначения начальника на объект"""
    chief = ForeignKeyField(ChiefEmployee, backref='object_assignments', on_delete='CASCADE')
    object = ForeignKeyField(Object, backref='chief_assignments', on_delete='CASCADE')
    assigned_date = DateField(verbose_name="Дата назначения", default=datetime.now)
    
    class Meta:
        table_name = 'chief_object_assignments'
        indexes = (
            (('chief', 'object'), True),  # Уникальная связь начальник-объект
        )

class PersonalCard(BaseModel):
    """Модель личной карточки"""
    guard_employee = ForeignKeyField(GuardEmployee, backref='personal_cards', on_delete='CASCADE', null=True)
    chief_employee = ForeignKeyField(ChiefEmployee, backref='personal_cards', on_delete='CASCADE', null=True)
    company = ForeignKeyField(Company, backref='personal_cards', on_delete='CASCADE')
    issue_date = DateField(verbose_name="Дата выдачи")
    photo_path = CharField(max_length=500, null=True, verbose_name="Путь к фотографии карточки")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'personal_cards'

class EmployeeDocument(BaseModel):
    """Модель документов сотрудников"""
    guard_employee = ForeignKeyField(GuardEmployee, backref='documents', on_delete='CASCADE', null=True)
    chief_employee = ForeignKeyField(ChiefEmployee, backref='documents', on_delete='CASCADE', null=True)
    document_type = CharField(max_length=50, verbose_name="Тип документа")  # Паспорт, Удостоверение, СНИЛС, Периодички
    page_number = IntegerField(verbose_name="Номер страницы")
    file_path = CharField(max_length=500, verbose_name="Путь к файлу")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'employee_documents'

# Создание таблиц
def init_database():
    """Инициализация базы данных"""
    try:
        db.connect()
        db.create_tables([Company, GuardEmployee, ChiefEmployee, OfficeEmployee, EmployeeCompany, Settings, Object, ObjectAddress, ObjectRate, Assignment, ChiefObjectAssignment, PersonalCard, EmployeeDocument], safe=True)
        
        # Создаем компании по умолчанию
        for company_name in ["Легион", "Норд", "Росбезопасность"]:
            Company.get_or_create(name=company_name)
        
        # Миграция: добавляем столбец company если его нет
        try:
            db.execute_sql("ALTER TABLE guard_employees ADD COLUMN company VARCHAR(20) DEFAULT 'Легион'")
        except:
            pass  # Столбец уже существует
        
        try:
            db.execute_sql("ALTER TABLE chief_employees ADD COLUMN company VARCHAR(20) DEFAULT 'Легион'")
        except:
            pass
        
        try:
            db.execute_sql("ALTER TABLE office_employees ADD COLUMN company VARCHAR(20) DEFAULT 'Легион'")
        except:
            pass
        
        # Миграция: добавляем столбец chief_id в assignments
        try:
            db.execute_sql("ALTER TABLE assignments ADD COLUMN chief_id INTEGER")
        except:
            pass  # Столбец уже существует
        
        try:
            db.execute_sql("ALTER TABLE assignments ADD CONSTRAINT fk_assignments_chief FOREIGN KEY (chief_id) REFERENCES chief_employees(id) ON DELETE SET NULL")
        except:
            pass  # Ограничение уже существует
        
        # Миграция: добавляем столбец photo_path в personal_cards
        try:
            db.execute_sql("ALTER TABLE personal_cards ADD COLUMN photo_path VARCHAR(500)")
        except:
            pass  # Столбец уже существует
        
        # Миграция: изменяем тип guard_rank на VARCHAR
        try:
            db.execute_sql("ALTER TABLE guard_employees ALTER COLUMN guard_rank TYPE VARCHAR(10)")
        except:
            pass  # Поле уже имеет нужный тип
        
        # Миграция: добавляем guard_rank для начальников
        try:
            db.execute_sql("ALTER TABLE chief_employees ADD COLUMN guard_rank VARCHAR(10)")
        except:
            pass  # Поле уже существует
        
        # Миграция: добавляем company_id для личных карточек
        try:
            db.execute_sql("ALTER TABLE personal_cards ADD COLUMN company_id INTEGER")
        except:
            pass  # Поле уже существует
        
        # Обновляем существующие карточки
        try:
            legion = Company.get(Company.name == "Легион")
            db.execute_sql(f"UPDATE personal_cards SET company_id = {legion.id} WHERE company_id IS NULL")
        except:
            pass
        
        # Миграция: удаляем старые поля из objects
        try:
            db.execute_sql("ALTER TABLE objects DROP COLUMN IF EXISTS address")
            db.execute_sql("ALTER TABLE objects DROP COLUMN IF EXISTS hourly_rate")
        except:
            pass
            
        # Создаем настройку темы по умолчанию
        try:
            Settings.get(Settings.key == "theme")
        except:
            Settings.create(key="theme", value="light")
        
        # Миграция: переносим старые данные о компаниях в новую структуру
        migrate_company_data()
            
    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        print("Убедитесь, что PostgreSQL запущен и настройки подключения корректны")
        raise

def migrate_company_data():
    """Миграция старых данных о компаниях"""
    try:
        # Проверяем, есть ли старое поле company
        cursor = db.execute_sql("SELECT column_name FROM information_schema.columns WHERE table_name='guard_employees' AND column_name='company'")
        if cursor.fetchone():
            # Мигрируем данные для GuardEmployee
            for employee in GuardEmployee.select():
                if hasattr(employee, 'company') and employee.company:
                    try:
                        company = Company.get(Company.name == employee.company)
                        EmployeeCompany.get_or_create(guard_employee=employee, company=company)
                    except:
                        pass
        
        # Мигрируем ChiefEmployee
        cursor = db.execute_sql("SELECT column_name FROM information_schema.columns WHERE table_name='chief_employees' AND column_name='company'")
        if cursor.fetchone():
            for employee in ChiefEmployee.select():
                if hasattr(employee, 'company') and employee.company:
                    try:
                        company = Company.get(Company.name == employee.company)
                        EmployeeCompany.get_or_create(chief_employee=employee, company=company)
                    except:
                        pass
        
        # Мигрируем OfficeEmployee
        cursor = db.execute_sql("SELECT column_name FROM information_schema.columns WHERE table_name='office_employees' AND column_name='company'")
        if cursor.fetchone():
            for employee in OfficeEmployee.select():
                if hasattr(employee, 'company') and employee.company:
                    try:
                        company = Company.get(Company.name == employee.company)
                        EmployeeCompany.get_or_create(office_employee=employee, company=company)
                    except:
                        pass
        
        # Для сотрудников без компаний назначаем Легион
        legion = Company.get(Company.name == "Легион")
        
        for employee in GuardEmployee.select():
            if not EmployeeCompany.select().where(EmployeeCompany.guard_employee == employee).exists():
                EmployeeCompany.create(guard_employee=employee, company=legion)
        
        for employee in ChiefEmployee.select():
            if not EmployeeCompany.select().where(EmployeeCompany.chief_employee == employee).exists():
                EmployeeCompany.create(chief_employee=employee, company=legion)
        
        for employee in OfficeEmployee.select():
            if not EmployeeCompany.select().where(EmployeeCompany.office_employee == employee).exists():
                EmployeeCompany.create(office_employee=employee, company=legion)
                
    except Exception as e:
        print(f"Ошибка миграции: {e}")

# Инициализируем базу данных при импорте
if __name__ != '__main__':
    init_database()
