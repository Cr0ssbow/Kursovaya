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
    photo_base64 = TextField(null=True, verbose_name="Фото в base64")
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
    created_by_user_id = IntegerField(null=True, verbose_name="Создан пользователем")
    
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
    photo_base64 = TextField(null=True, verbose_name="Фото в base64")
    position = CharField(max_length=100, verbose_name="Должность")
    guard_rank = CharField(max_length=10, null=True, verbose_name="Разряд охранника")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    termination_reason = TextField(null=True, verbose_name="Причина увольнения")
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    payment_method = CharField(max_length=20, default="на карту", verbose_name="Способ выдачи зарплаты")
    created_by_user_id = IntegerField(null=True, verbose_name="Создан пользователем")
    
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
    photo_base64 = TextField(null=True, verbose_name="Фото в base64")
    position = CharField(max_length=100, verbose_name="Должность")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    termination_reason = TextField(null=True, verbose_name="Причина увольнения")
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    payment_method = CharField(max_length=20, default="на карту", verbose_name="Способ выдачи зарплаты")
    created_by_user_id = IntegerField(null=True, verbose_name="Создан пользователем")
    
    class Meta:
        table_name = 'office_employees'
        
    def is_active(self):
        return self.termination_date is None

# Для обратной совместимости
Employee = GuardEmployee

class Role(BaseModel):
    """Модель роли пользователя"""
    name = CharField(max_length=50, unique=True, verbose_name="Название роли")
    description = TextField(null=True, verbose_name="Описание")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'roles'

class User(BaseModel):
    """Модель пользователя для авторизации"""
    username = CharField(max_length=50, unique=True, verbose_name="Логин")
    password_hash = CharField(max_length=255, verbose_name="Хеш пароля")
    role = CharField(max_length=20, default="user", verbose_name="Роль")
    guard_employee = ForeignKeyField(GuardEmployee, null=True, backref='user_account')
    chief_employee = ForeignKeyField(ChiefEmployee, null=True, backref='user_account')
    office_employee = ForeignKeyField(OfficeEmployee, null=True, backref='user_account')
    allowed_pages = TextField(default="home,settings", verbose_name="Доступные страницы")
    is_active = BooleanField(default=True, verbose_name="Активен")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'users'

class UserLog(BaseModel):
    """Модель логирования действий пользователей"""
    user = ForeignKeyField(User, backref='logs', on_delete='CASCADE')
    action = CharField(max_length=100, verbose_name="Действие")
    description = TextField(null=True, verbose_name="Описание")
    ip_address = CharField(max_length=45, null=True, verbose_name="IP адрес")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'user_logs'

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
    comment = TextField(null=True, verbose_name="Комментарий")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'assignments'
        indexes = (
            (('date',), False),
            (('employee', 'date'), False),
        )

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
    file_base64 = TextField(null=True, verbose_name="Файл в base64")
    filename = CharField(max_length=255, null=True, verbose_name="Название файла")
    is_discarded = BooleanField(default=False, verbose_name="Списана")
    discarded_date = DateField(null=True, verbose_name="Дата списания")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'personal_cards'

class PersonalCardPhoto(BaseModel):
    """Модель фотографий личных карточек"""
    personal_card = ForeignKeyField(PersonalCard, backref='photos', on_delete='CASCADE')
    photo_base64 = TextField(verbose_name="Фото в base64")
    filename = CharField(max_length=255, verbose_name="Название файла")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'personal_card_photos'

class EmployeeDocument(BaseModel):
    """Модель документов сотрудников"""
    guard_employee = ForeignKeyField(GuardEmployee, backref='documents', on_delete='CASCADE', null=True)
    chief_employee = ForeignKeyField(ChiefEmployee, backref='documents', on_delete='CASCADE', null=True)
    office_employee = ForeignKeyField(OfficeEmployee, backref='documents', on_delete='CASCADE', null=True)
    document_type = CharField(max_length=50, verbose_name="Тип документа")
    file_base64 = TextField(null=True, verbose_name="Файл в base64")
    filename = CharField(max_length=255, null=True, verbose_name="Название файла")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'employee_documents'

class EmployeeDocumentPhoto(BaseModel):
    """Модель фотографий документов"""
    document = ForeignKeyField(EmployeeDocument, backref='photos', on_delete='CASCADE')
    photo_base64 = TextField(verbose_name="Фото в base64")
    filename = CharField(max_length=255, verbose_name="Название файла")
    page_number = IntegerField(verbose_name="Номер страницы", default=1)
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'employee_document_photos'

class CashWithdrawal(BaseModel):
    """Модель выхода за наличку (ВЗН)"""
    employee = ForeignKeyField(GuardEmployee, backref='cash_withdrawals', on_delete='CASCADE')
    object = ForeignKeyField(Object, backref='cash_withdrawals', on_delete='CASCADE')
    chief = ForeignKeyField(ChiefEmployee, backref='supervised_cash_withdrawals', on_delete='SET NULL', null=True)
    date = DateField(verbose_name="Дата ВЗН")
    hours = IntegerField(verbose_name="Количество часов")
    hourly_rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка")
    is_absent = BooleanField(default=False, verbose_name="Прогул")
    absent_comment = TextField(null=True, verbose_name="Комментарий к прогулу")
    deduction_amount = DecimalField(max_digits=7, decimal_places=2, default=0, verbose_name="Сумма удержания")
    bonus_amount = DecimalField(max_digits=7, decimal_places=2, default=0, verbose_name="Сумма премии")
    bonus_comment = TextField(null=True, verbose_name="Комментарий к премии")
    comment = TextField(null=True, verbose_name="Комментарий")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'cash_withdrawals'
        indexes = (
            (('date',), False),
            (('employee', 'date'), False),
        )

# Создание таблиц
def init_database():
    """Инициализация базы данных"""
    try:
        db.connect()
        db.create_tables([Company, GuardEmployee, ChiefEmployee, OfficeEmployee, EmployeeCompany, Settings, Role, User, UserLog, Object, ObjectAddress, ObjectRate, Assignment, ChiefObjectAssignment, PersonalCard, PersonalCardPhoto, EmployeeDocument, EmployeeDocumentPhoto, CashWithdrawal], safe=True)
        
        # Создаем компании по умолчанию
        for company_name in ["Легион", "Норд", "Росбезопасность"]:
            Company.get_or_create(name=company_name)
            
        # Создаем настройку темы по умолчанию
        try:
            Settings.get(Settings.key == "theme")
        except:
            Settings.create(key="theme", value="light")
            
        # Создаем роли по умолчанию
        try:
            Role.get_or_create(name="Admin", defaults={'description': 'Администратор системы'})
            Role.get_or_create(name="user", defaults={'description': 'Обычный пользователь'})
        except Exception as role_error:
            print(f"Ошибка создания ролей: {role_error}")
            
        # Миграция: добавляем поле комментария к сменам
        try:
            db.execute_sql("ALTER TABLE assignments ADD COLUMN comment TEXT")
        except:
            pass
            
        # Миграция: добавляем поле created_by_user_id к моделям сотрудников
        try:
            db.execute_sql("ALTER TABLE guard_employees ADD COLUMN created_by_user_id INTEGER")
        except:
            pass
            
        try:
            db.execute_sql("ALTER TABLE chief_employees ADD COLUMN created_by_user_id INTEGER")
        except:
            pass
            
        try:
            db.execute_sql("ALTER TABLE office_employees ADD COLUMN created_by_user_id INTEGER")
        except:
            pass
            
        # Миграция: добавляем поля для ВЗН
        try:
            db.execute_sql("ALTER TABLE cash_withdrawals ADD COLUMN is_absent BOOLEAN DEFAULT FALSE")
        except:
            pass
            
        try:
            db.execute_sql("ALTER TABLE cash_withdrawals ADD COLUMN absent_comment TEXT")
        except:
            pass
            
        try:
            db.execute_sql("ALTER TABLE cash_withdrawals ADD COLUMN deduction_amount DECIMAL(7,2) DEFAULT 0")
        except:
            pass
            
        try:
            db.execute_sql("ALTER TABLE cash_withdrawals ADD COLUMN bonus_amount DECIMAL(7,2) DEFAULT 0")
        except:
            pass
            
        try:
            db.execute_sql("ALTER TABLE cash_withdrawals ADD COLUMN bonus_comment TEXT")
        except:
            pass
            
        # Создаем индексы для производительности
        try:
            db.execute_sql("CREATE INDEX IF NOT EXISTS idx_assignments_date ON assignments(date);")
            db.execute_sql("CREATE INDEX IF NOT EXISTS idx_assignments_employee_date ON assignments(employee_id, date);")
            db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cash_withdrawals_date ON cash_withdrawals(date);")
            db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cash_withdrawals_employee_date ON cash_withdrawals(employee_id, date);")
        except:
            pass
            
    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        print("Убедитесь, что PostgreSQL запущен и настройки подключения корректны")
        raise

# Инициализируем базу данных при импорте
if __name__ != '__main__':
    init_database()