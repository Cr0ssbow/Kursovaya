from peewee import *
from datetime import datetime
import os

# Создаем директорию для базы данных если её нет
db_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(db_dir, exist_ok=True)

# Путь к базе данных
db_path = os.path.join(db_dir, 'employees.db')

# Инициализация базы данных
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class Settings(BaseModel):
    key = CharField(unique=True)
    value = CharField()

class Employee(BaseModel):
    @classmethod
    def exists_by_name(cls, full_name: str) -> bool:
        return cls.select().where(cls.full_name == full_name).exists()
    """Модель сотрудника"""
    full_name = CharField(max_length=200, verbose_name="ФИО")
    birth_date = DateField(verbose_name="Дата рождения")
    photo_path = CharField(max_length=500, null=True, verbose_name="Путь к фото")
    certificate_number = CharField(max_length=20, null=True, verbose_name="Номер удостоверения")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    guard_license_date = DateField(null=True, verbose_name="Дата выдачи удостоверения охранника")
    guard_rank = IntegerField(null=True, verbose_name="Разряд охранника (3-6)")
    medical_exam_date = DateField(null=True, verbose_name="Дата прохождения медкомиссии")
    periodic_check_date = DateField(null=True, verbose_name="Дата периодической проверки")
    hourly_rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка", default=0)
    hours_worked = IntegerField(verbose_name="Количество часов", default=0)
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    payment_method = CharField(max_length=20, default="на карту", verbose_name="Способ выдачи зарплаты")
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'employees'
        
    def is_active(self):
        """Проверка, работает ли сотрудник"""
        return self.termination_date is None

    def calc_salary(self):
        """Расчет зарплаты с учетом прогулов, премий и удержаний"""
        total_salary = 0
        total_hours = 0
        
        for assignment in self.assignments:
            if not assignment.is_absent:  # Не учитываем прогулы
                total_salary += float(assignment.hourly_rate) * assignment.hours
                total_hours += assignment.hours
            
            # Добавляем премии и вычитаем удержания
            total_salary += float(assignment.bonus_amount) - float(assignment.deduction_amount)
        
        return total_salary, total_hours

    def delete_employee(self):
        """Удаление сотрудника из базы данных"""
        self.delete_instance()

class Object(BaseModel):
    """Модель объекта"""
    name = CharField(max_length=200, unique=True, verbose_name="Название объекта")
    address = CharField(max_length=500, null=True, verbose_name="Адрес объекта")
    description = TextField(null=True, verbose_name="Описание")
    hourly_rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка", default=0)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'objects'

class Assignment(BaseModel):
    """Модель назначения сотрудника на объект"""
    employee = ForeignKeyField(Employee, backref='assignments', on_delete='CASCADE') # связь один ко многим employee (1) → (многоо) Assignment
    object = ForeignKeyField(Object, backref='assignments', on_delete='CASCADE') # связь один ко многим Object (1) → (многоо) Assignment
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

# Создание таблиц
def init_database():
    """Инициализация базы данных"""
    db.connect()
    db.create_tables([Employee, Settings, Object, Assignment], safe=True)
    

    # Миграция: добавляем hourly_rate к таблице objects
    try:
        # Проверяем, есть ли уже поле hourly_rate
        cursor = db.execute_sql('PRAGMA table_info(objects)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'hourly_rate' not in columns:
            db.execute_sql('ALTER TABLE objects ADD COLUMN hourly_rate DECIMAL(7,2) DEFAULT 0')
    except:
        pass
    
    # Миграция: добавляем поля охранника к таблице employees
    try:
        cursor = db.execute_sql('PRAGMA table_info(employees)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'guard_license_date' not in columns:
            db.execute_sql('ALTER TABLE employees ADD COLUMN guard_license_date DATE')
        if 'guard_rank' not in columns:
            db.execute_sql('ALTER TABLE employees ADD COLUMN guard_rank INTEGER')
        if 'medical_exam_date' not in columns:
            db.execute_sql('ALTER TABLE employees ADD COLUMN medical_exam_date DATE')
        if 'periodic_check_date' not in columns:
            db.execute_sql('ALTER TABLE employees ADD COLUMN periodic_check_date DATE')
    except:
        pass
    
    # Миграция: добавляем поля премий и прогулов к таблице assignments
    try:
        cursor = db.execute_sql('PRAGMA table_info(assignments)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'is_absent' not in columns:
            db.execute_sql('ALTER TABLE assignments ADD COLUMN is_absent BOOLEAN DEFAULT 0')
        if 'absent_comment' not in columns:
            db.execute_sql('ALTER TABLE assignments ADD COLUMN absent_comment TEXT')
        if 'bonus_amount' not in columns:
            db.execute_sql('ALTER TABLE assignments ADD COLUMN bonus_amount DECIMAL(7,2) DEFAULT 0')
        if 'bonus_comment' not in columns:
            db.execute_sql('ALTER TABLE assignments ADD COLUMN bonus_comment TEXT')
        if 'deduction_amount' not in columns:
            db.execute_sql('ALTER TABLE assignments ADD COLUMN deduction_amount DECIMAL(7,2) DEFAULT 0')
    except:
        pass
    
    # Миграция: добавляем поле номера удостоверения
    try:
        cursor = db.execute_sql('PRAGMA table_info(employees)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'certificate_number' not in columns:
            db.execute_sql('ALTER TABLE employees ADD COLUMN certificate_number VARCHAR(20)')
    except:
        pass
    
    # Миграция: добавляем поле способа выдачи зарплаты
    try:
        cursor = db.execute_sql('PRAGMA table_info(employees)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'payment_method' not in columns:
            db.execute_sql('ALTER TABLE employees ADD COLUMN payment_method VARCHAR(20) DEFAULT "на карту"')
    except:
        pass

# Инициализируем базу данных при импорте
init_database()
