import flet as ft
from database.models import ChiefEmployee, Object, ChiefObjectAssignment, db
from datetime import datetime
from base.base_employee_page import BaseEmployeePage
import os

class ChiefEmployeesPage(BaseEmployeePage):
    """Страница начальников охраны"""
    
    def _create_form_fields(self):
        """Создает поля формы"""
        self.name_field = ft.TextField(label="ФИО", width=300)
        self.birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.position_field = ft.TextField(label="Должность", width=250)
        self.guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option("ОВН"), ft.dropdown.Option("Б")] + [ft.dropdown.Option(str(i)) for i in range(4, 7)])
        self.salary_field = ft.TextField(label="Зарплата", width=150)
        self.payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")
        self.company_checkboxes = self._create_company_checkboxes()
    
    def _create_list(self):
        """Создает список"""
        self.employees_list = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            height=500
        )
    
    def _get_base_query(self):
        return ChiefEmployee.select().where(ChiefEmployee.termination_date.is_null())
    
    def _apply_name_filter(self, query):
        return query.where(ChiefEmployee.full_name.contains(self.search_value))
    
    def _apply_company_filter(self, query, companies):
        from database.models import EmployeeCompany, Company
        company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
        employee_ids = [ec.chief_employee_id for ec in EmployeeCompany.select().where(EmployeeCompany.company_id.in_(company_ids))]
        return query.where(ChiefEmployee.id.in_(employee_ids))
    
    def _create_company_checkboxes(self, first_checked=True):
        """Создает чекбоксы для компаний"""
        from database.models import Company
        checkboxes = []
        for i, company in enumerate(Company.select()):
            checkboxes.append(ft.Checkbox(
                label=company.name, 
                value=first_checked and i == 0
            ))
        return checkboxes
    
    def _get_employee_companies(self, employee):
        """Возвращает список компаний сотрудника"""
        from database.models import EmployeeCompany, Company
        companies = [ec.company.name for ec in EmployeeCompany.select().join(Company).where(EmployeeCompany.chief_employee == employee)]
        return ", ".join(companies) if companies else "Не указано"
    
    def _get_order_field(self):
        return ChiefEmployee.full_name
    
    def _create_list_item(self, employee):
        return ft.ListTile(
            title=ft.Text(employee.full_name, weight="bold"),
            subtitle=ft.Text(f"Должность: {employee.position}"),
            on_click=lambda e, emp=employee: self.show_detail_dialog(emp)
        )
    
    def _get_detail_title(self):
        return "Карточка начальника"
    
    def show_detail_dialog(self, employee):
        """Показывает диалог с вкладками"""
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Основная информация",
                    content=ft.Column(self._get_detail_content(employee), scroll=ft.ScrollMode.AUTO)
                ),
                ft.Tab(
                    text="Личные карточки",
                    content=ft.Column([], scroll=ft.ScrollMode.AUTO)
                ),
                ft.Tab(
                    text="Документы",
                    content=ft.Column([], scroll=ft.ScrollMode.AUTO)
                )
            ],
            expand=True
        )
        
        tabs_dialog = ft.AlertDialog(
            title=ft.Text(f"{self._get_detail_title()}: {employee.full_name}"),
            content=tabs,
            actions=[
                ft.TextButton("Изменить фотографию", on_click=lambda e: self.change_photo(employee)),
                ft.TextButton("Управление объектами", on_click=lambda e: self.show_objects_dialog(employee)),
                ft.TextButton("Редактировать", on_click=lambda e: self.show_edit_dialog(employee)),
                ft.TextButton("Уволить", on_click=lambda e: self.show_termination_dialog(employee), style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Закрыть", on_click=lambda e: setattr(tabs_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        
        # Сохраняем ссылку на tabs в диалоге
        tabs_dialog.tabs_ref = tabs
        
        def on_tab_change(e):
            if e.control.selected_index == 1:  # Карточки
                tabs.tabs[1].content = ft.Column(self._get_personal_cards_content(employee, tabs_dialog), scroll=ft.ScrollMode.AUTO)
            elif e.control.selected_index == 2:  # Документы
                tabs.tabs[2].content = ft.Column(self._get_documents_content(employee, tabs_dialog), scroll=ft.ScrollMode.AUTO)
            self.page.update()
        
        tabs.on_change = on_tab_change
        
        self.page.overlay.append(tabs_dialog)
        tabs_dialog.open = True
        self.page.update()
    

    

    
    def get_employee_folder_type(self):
        return "Начальник охраны"
    

    
    def _get_detail_content(self, employee):
        # Получаем закрепленные объекты
        assigned_objects = []
        try:
            if db.is_closed():
                db.connect()
            assignments = ChiefObjectAssignment.select().where(ChiefObjectAssignment.chief == employee)
            assigned_objects = [assignment.object.name for assignment in assignments]
        except Exception as e:
            print(f"Ошибка получения объектов: {e}")
        finally:
            if not db.is_closed():
                db.close()
        
        objects_text = ", ".join(assigned_objects) if assigned_objects else "Нет закрепленных объектов"
        
        content = [
            ft.Row([
                ft.Column([
                    self.get_photo_widget(employee.full_name),
                    ft.Text(f"Дата рождения: {self.format_date(employee.birth_date)}", size=16),
                    ft.Text(f"Должность: {employee.position}", size=16),
                    ft.Text(f"Разряд охранника: {str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else 'Не указано'}", size=16),
                    ft.Text(f"Зарплата: {employee.salary} ₽", size=16),
                    ft.Text(f"Способ выдачи зарплаты: {employee.payment_method}", size=16),
                    ft.Text(f"Компании: {self._get_employee_companies(employee)}", size=16),
                    ft.Text(f"Закрепленные объекты: {objects_text}", size=16),
                ]),
                ft.Container(expand=True)
            ])
        ]
        return content
    
    def _get_add_title(self):
        return "Добавить начальника охраны"
    
    def _get_form_fields(self):
        company_row = ft.Row([ft.Text("Компании:", width=100)] + self.company_checkboxes)
        return [self.name_field, self.birth_field, self.position_field, self.guard_rank_field, self.salary_field, self.payment_method_field, company_row]
    
    def _save_operation(self):
        full_name = self.name_field.value.strip()
        birth_value = self.birth_field.value.strip()
        position_value = self.position_field.value.strip()
        salary_value = self.salary_field.value.strip()
        payment_method_value = self.payment_method_field.value
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value:
            raise ValueError("Дата рождения обязательна!")
        if not position_value:
            raise ValueError("Должность обязательна!")
        
        birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        salary = float(salary_value) if salary_value else 0
        
        employee = ChiefEmployee.create(
            full_name=full_name,
            birth_date=birth_date,
            position=position_value,
            guard_rank=self.guard_rank_field.value if self.guard_rank_field.value else None,
            salary=salary,
            payment_method=payment_method_value or "на карту"
        )
        
        # Сохраняем связи с компаниями
        from database.models import Company, EmployeeCompany
        for checkbox in self.company_checkboxes:
            if checkbox.value:
                company = Company.get(Company.name == checkbox.label)
                EmployeeCompany.create(chief_employee=employee, company=company)
        

        return True
    
    def _get_success_message(self):
        return "Начальник добавлен!"
    
    def _get_page_title(self):
        return "Начальники охраны"
    
    def _get_add_button_text(self):
        return "Добавить начальника"
    
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        self.edit_name_field = ft.TextField(label="ФИО", width=300)
        self.edit_birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.edit_position_field = ft.TextField(label="Должность", width=250)
        self.edit_guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option("ОВН"), ft.dropdown.Option("Б")] + [ft.dropdown.Option(str(i)) for i in range(4, 7)])
        self.edit_salary_field = ft.TextField(label="Зарплата", width=150)
        self.edit_payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")])
        self.edit_company_checkboxes = self._create_company_checkboxes(False)
    
    def _get_edit_fields(self):
        edit_company_row = ft.Row([ft.Text("Компании:", width=100)] + self.edit_company_checkboxes)
        return [self.edit_name_field, self.edit_birth_field, self.edit_position_field, self.edit_guard_rank_field, self.edit_salary_field, self.edit_payment_method_field, edit_company_row]
    
    def _populate_edit_fields(self, employee):
        self.edit_name_field.value = employee.full_name
        self.edit_birth_field.value = self.format_date(employee.birth_date)
        self.edit_position_field.value = employee.position
        self.edit_guard_rank_field.value = str(employee.guard_rank) if hasattr(employee, 'guard_rank') and employee.guard_rank else None
        self.edit_salary_field.value = str(employee.salary)
        self.edit_payment_method_field.value = employee.payment_method
        # Заполняем чекбоксы компаний
        from database.models import EmployeeCompany, Company
        employee_companies = [ec.company.name for ec in EmployeeCompany.select().join(Company).where(EmployeeCompany.chief_employee == employee)]
        for checkbox in self.edit_company_checkboxes:
            checkbox.value = checkbox.label in employee_companies
    
    def _save_edit_operation(self):
        full_name = self.edit_name_field.value.strip()
        birth_value = self.edit_birth_field.value.strip()
        position_value = self.edit_position_field.value.strip()
        salary_value = self.edit_salary_field.value.strip()
        payment_method_value = self.edit_payment_method_field.value
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value or birth_value == "Не указано":
            raise ValueError("Дата рождения обязательна!")
        if not position_value:
            raise ValueError("Должность обязательна!")
        
        birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        salary = float(salary_value) if salary_value else 0
        
        self.current_employee.full_name = full_name
        self.current_employee.birth_date = birth_date
        self.current_employee.position = position_value
        self.current_employee.guard_rank = self.edit_guard_rank_field.value if self.edit_guard_rank_field.value else None
        self.current_employee.salary = salary
        self.current_employee.payment_method = payment_method_value or "на карту"
        
        self.current_employee.save()
        
        # Обновляем связи с компаниями
        from database.models import Company, EmployeeCompany
        # Удаляем старые связи
        EmployeeCompany.delete().where(EmployeeCompany.chief_employee == self.current_employee).execute()
        # Создаем новые
        for checkbox in self.edit_company_checkboxes:
            if checkbox.value:
                company = Company.get(Company.name == checkbox.label)
                EmployeeCompany.create(chief_employee=self.current_employee, company=company)
        return True
    
    def _get_employee_type(self):
        return "начальника"
    

    
    def show_objects_dialog(self, chief):
        """Показывает диалог управления объектами"""
        try:
            if db.is_closed():
                db.connect()
            
            # Получаем все объекты
            all_objects = list(Object.select())
            
            # Получаем уже назначенные объекты
            assigned_objects = set()
            assignments = ChiefObjectAssignment.select().where(ChiefObjectAssignment.chief == chief)
            for assignment in assignments:
                assigned_objects.add(assignment.object.id)
            
            # Создаем чекбоксы для объектов
            object_checkboxes = []
            for obj in all_objects:
                checkbox = ft.Checkbox(
                    label=obj.name,
                    value=obj.id in assigned_objects,
                    data=obj.id
                )
                object_checkboxes.append(checkbox)
            
            def save_assignments():
                try:
                    if db.is_closed():
                        db.connect()
                    
                    # Удаляем все текущие назначения
                    ChiefObjectAssignment.delete().where(ChiefObjectAssignment.chief == chief).execute()
                    
                    # Добавляем новые назначения
                    for checkbox in object_checkboxes:
                        if checkbox.value:
                            obj = Object.get_by_id(checkbox.data)
                            ChiefObjectAssignment.create(chief=chief, object=obj)
                    
                    self.page.close(objects_dialog)
                    self.show_snackbar("Объекты обновлены!")
                    
                except Exception as e:
                    self.show_snackbar(f"Ошибка: {str(e)}", True)
                finally:
                    if not db.is_closed():
                        db.close()
            
            objects_dialog = ft.AlertDialog(
                title=ft.Text(f"Управление объектами - {chief.full_name}"),
                content=ft.Container(
                    content=ft.Column(object_checkboxes, scroll=ft.ScrollMode.AUTO),
                    width=400,
                    height=300
                ),
                actions=[
                    ft.TextButton("Сохранить", on_click=lambda e: save_assignments()),
                    ft.TextButton("Отмена", on_click=lambda e: self.page.close(objects_dialog))
                ]
            )
            
            self.page.overlay.append(objects_dialog)
            self.page.update()
            self.page.open(objects_dialog)
            
        except Exception as e:
            self.show_snackbar(f"Ошибка: {str(e)}", True)
        finally:
            if not db.is_closed():
                db.close()


    

    


# Функция-обертка для совместимости
def chief_employees_page(page: ft.Page = None) -> ft.Column:
    return ChiefEmployeesPage(page).render()