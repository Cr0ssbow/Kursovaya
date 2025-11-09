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
    hire_date = DateField(verbose_name="Дата принятия на работу")
    termination_date = DateField(null=True, verbose_name="Дата увольнения")
    guard_license_date = DateField(null=True, verbose_name="Дата выдачи удостоверения охранника")
    guard_rank = IntegerField(null=True, verbose_name="Разряд охранника (3-6)")
    hourly_rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка", default=0)
    hours_worked = IntegerField(verbose_name="Количество часов", default=0)
    salary = DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата", default=0)
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'employees'
        
    def is_active(self):
        """Проверка, работает ли сотрудник"""
        return self.termination_date is None

    def calc_salary(self):
        """Расчет зарплаты: часы * ставка"""
        return float(self.hourly_rate) * self.hours_worked

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
    employee = ForeignKeyField(Employee, backref='assignments') # связь один ко многим employee (1) → (многоо) Assignment
    object = ForeignKeyField(Object, backref='assignments') # связь один ко многим Object (1) → (многоо) Assignment
    date = DateField(verbose_name="Дата назначения")
    hours = IntegerField(verbose_name="Количество часов")
    hourly_rate = DecimalField(max_digits=7, decimal_places=2, verbose_name="Почасовая ставка")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'assignments'

# Создание таблиц
def init_database():
    """Инициализация базы данных"""
    db.connect()
    db.create_tables([Employee, Settings, Object, Assignment], safe=True)
    
    # Миграция: добавляем null=True к полям дат
    try:
        db.execute_sql('PRAGMA table_info(employees)')
        # Пересоздаем таблицу с новой структурой
        db.execute_sql('DROP TABLE IF EXISTS employees_backup')
        db.execute_sql('ALTER TABLE employees RENAME TO employees_backup')
        db.create_tables([Employee], safe=False)
        db.execute_sql('INSERT INTO employees (id, full_name, birth_date, photo_path, hire_date, termination_date, hourly_rate, hours_worked, salary, created_at) SELECT id, full_name, birth_date, photo_path, hire_date, termination_date, hourly_rate, hours_worked, salary, created_at FROM employees_backup')
        db.execute_sql('DROP TABLE employees_backup')
    except:
        pass
    
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
    except:
        pass

# Инициализируем базу данных при импорте
init_database()
