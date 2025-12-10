import flet as ft
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from database.models import User, Role, UserLog, db, GuardEmployee, ChiefEmployee, OfficeEmployee

class AuthManager:
    def __init__(self):
        self.current_user = None
        self.ph = PasswordHasher()
        self._create_default_admin()
    
    def _hash_password(self, password: str) -> str:
        return self.ph.hash(password)
    
    def _create_default_admin(self):
        """Создает администратора по умолчанию"""
        try:
            if db.is_closed():
                db.connect()
            
            all_pages = "home,settings,employees,chief_employees,office_employees,objects,calendar,statistics,notes,terminated,discarded_cards,logs,administration"
            
            if not User.select().exists():
                import os
                admin_password = os.getenv('ADMIN_PASSWORD', 'Admin')
                User.create(
                    username="Admin",
                    password_hash=self._hash_password(admin_password),
                    role="Admin",
                    allowed_pages=all_pages
                )
            else:
                # Обновляем существующих администраторов
                for admin in User.select().where((User.role == "Admin") | (User.role == "admin")):
                    if not admin.allowed_pages or admin.allowed_pages == "home" or len(admin.allowed_pages.split(',')) < 10:
                        admin.allowed_pages = all_pages
                        admin.save()
                
                # Обновляем обычных пользователей, добавляя доступ к настройкам
                for user in User.select().where(User.role != "Admin"):
                    if user.allowed_pages and "settings" not in user.allowed_pages:
                        if user.allowed_pages == "home":
                            user.allowed_pages = "home,settings"
                        else:
                            user.allowed_pages = user.allowed_pages + ",settings"
                        user.save()
        except Exception as e:
            print(f"Ошибка создания администратора: {e}")
        finally:
            if not db.is_closed():
                db.close()
    
    def login(self, username: str, password: str) -> bool:
        """Авторизация пользователя"""
        try:
            if db.is_closed():
                db.connect()
            
            user = User.get((User.username == username) & (User.is_active == True))
            
            # Проверяем пароль с Argon2
            try:
                self.ph.verify(user.password_hash, password)
                self.current_user = user
                self.log_action("Вход в систему", f"Пользователь {username} вошел в систему")
                return True
            except VerifyMismatchError:
                return False
                
        except User.DoesNotExist:
            return False
        except Exception as e:
            print(f"Ошибка авторизации: {e}")
            return False
        finally:
            if not db.is_closed():
                db.close()
    
    def logout(self):
        """Выход из системы"""
        if self.current_user:
            self.log_action("Выход из системы", f"Пользователь {self.current_user.username} вышел из системы")
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """Проверка авторизации"""
        return self.current_user is not None
    
    def has_role(self, role: str) -> bool:
        """Проверка роли пользователя"""
        return self.current_user and self.current_user.role == role
    
    def create_user(self, username: str, password: str, role: str = "user", employee_id: int = None, employee_type: str = None, allowed_pages: str = "home,settings") -> bool:
        """Создание нового пользователя"""
        try:
            if db.is_closed():
                db.connect()
            
            user_data = {
                'username': username,
                'password_hash': self._hash_password(password),
                'role': role,
                'allowed_pages': allowed_pages
            }
            
            if employee_id and employee_type:
                if employee_type == 'guard':
                    user_data['guard_employee'] = employee_id
                elif employee_type == 'chief':
                    user_data['chief_employee'] = employee_id
                elif employee_type == 'office':
                    user_data['office_employee'] = employee_id
            
            User.create(**user_data)
            self.log_action("Создание пользователя", f"Создан пользователь {username}")
            return True
        except Exception as e:
            print(f"Ошибка создания пользователя: {e}")
            return False
        finally:
            if not db.is_closed():
                db.close()
    
    def get_all_employees(self):
        """Получение всех сотрудников"""
        from database.models import GuardEmployee, ChiefEmployee, OfficeEmployee
        try:
            if db.is_closed():
                db.connect()
            
            employees = []
            for emp in GuardEmployee.select():
                employees.append((emp.id, emp.full_name, 'guard'))
            for emp in ChiefEmployee.select():
                employees.append((emp.id, emp.full_name, 'chief'))
            for emp in OfficeEmployee.select():
                employees.append((emp.id, emp.full_name, 'office'))
            
            return employees
        except Exception as e:
            print(f"Ошибка получения сотрудников: {e}")
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def has_page_access(self, page_name: str) -> bool:
        """Проверка доступа к странице"""
        if not self.current_user:
            return False
        if self.current_user.role == "Admin":
            return True
        return page_name in self.current_user.allowed_pages.split(',')
    
    def get_all_users(self):
        """Получение всех пользователей"""
        try:
            if db.is_closed():
                db.connect()
            return list(User.select())
        except Exception as e:
            print(f"Ошибка получения пользователей: {e}")
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        try:
            if db.is_closed():
                db.connect()
            
            user = User.get_by_id(user_id)
            if user.username != "Admin":  # Защита от удаления админа
                username = user.username
                user.delete_instance()
                self.log_action("Удаление пользователя", f"Удален пользователь {username}")
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления пользователя: {e}")
            return False
        finally:
            if not db.is_closed():
                db.close()
    
    def update_user(self, user_id: int, username: str = None, password: str = None, role: str = None, employee_id: int = None, employee_type: str = None, allowed_pages: str = None) -> bool:
        """Обновление пользователя"""
        try:
            if db.is_closed():
                db.connect()
            
            user = User.get_by_id(user_id)
            
            if username:
                user.username = username
            if password:
                user.password_hash = self._hash_password(password)
            if role:
                user.role = role
            if allowed_pages:
                user.allowed_pages = allowed_pages
            
            # Очищаем связи с сотрудниками
            user.guard_employee = None
            user.chief_employee = None
            user.office_employee = None
            
            # Устанавливаем новую связь
            if employee_id and employee_type:
                if employee_type == 'guard':
                    user.guard_employee = employee_id
                elif employee_type == 'chief':
                    user.chief_employee = employee_id
                elif employee_type == 'office':
                    user.office_employee = employee_id
            
            user.save()
            return True
        except Exception as e:
            print(f"Ошибка обновления пользователя: {e}")
            return False
        finally:
            if not db.is_closed():
                db.close()
    
    def get_all_roles(self):
        """Получение всех ролей"""
        try:
            if db.is_closed():
                db.connect()
            # Проверяем существование таблицы
            db.create_tables([Role], safe=True)
            Role.get_or_create(name="Admin", defaults={'description': 'Администратор системы'})
            Role.get_or_create(name="user", defaults={'description': 'Обычный пользователь'})
            return list(Role.select())
        except Exception as e:
            print(f"Ошибка получения ролей: {e}")
            # Возвращаем базовые роли
            class MockRole:
                def __init__(self, name, description=""):
                    self.name = name
                    self.description = description
                    self.id = None  # Mock-объекты не имеют ID
            return [MockRole("Admin", "Администратор"), MockRole("user", "Пользователь")]
        finally:
            if not db.is_closed():
                db.close()
    
    def create_role(self, name: str, description: str = "") -> bool:
        """Создание новой роли"""
        try:
            if db.is_closed():
                db.connect()
            Role.create(name=name, description=description)
            return True
        except Exception as e:
            print(f"Ошибка создания роли: {e}")
            return False
        finally:
            if not db.is_closed():
                db.close()
    
    def delete_role(self, role_id: int) -> bool:
        """Удаление роли"""
        try:
            if db.is_closed():
                db.connect()
            
            role = Role.get_by_id(role_id)
            if role.name not in ["Admin", "user"]:
                role.delete_instance()
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления роли: {e}")
            return False
        finally:
            if not db.is_closed():
                db.close()
    
    def log_action(self, action: str, description: str = None):
        """Логирование действий пользователя"""
        print(f"Попытка логирования: {action}, {description}")
        if not self.current_user:
            print("Нет текущего пользователя")
            return
        
        try:
            if db.is_closed():
                db.connect()
            UserLog.create(
                user=self.current_user,
                action=action,
                description=description
            )
            print(f"Лог успешно создан: {action}")
        except Exception as e:
            print(f"Ошибка логирования: {e}")
        finally:
            if not db.is_closed():
                db.close()

def create_login_page(page: ft.Page, auth_manager: AuthManager, on_success):
    """Создает страницу авторизации"""
    username_field = ft.TextField(label="Логин", width=300)
    password_field = ft.TextField(label="Пароль", password=True, width=300)
    error_text = ft.Text("", color=ft.Colors.RED)
    
    def handle_login(e):
        if auth_manager.login(username_field.value, password_field.value):
            on_success()
        else:
            error_text.value = "Неверный логин или пароль"
            page.update()
    
    return ft.Column([
        ft.Text("Авторизация", size=24, weight="bold"),
        username_field,
        password_field,
        ft.ElevatedButton("Войти", on_click=handle_login),
        error_text
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)