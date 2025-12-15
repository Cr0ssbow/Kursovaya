import flet as ft
from database.models import OfficeEmployee
from datetime import datetime
from base.base_employee_page import BaseEmployeePage

class OfficeEmployeesPage(BaseEmployeePage):
    """Страница сотрудников офиса"""
    
    def _create_form_fields(self):
        """Создает поля формы"""
        super()._create_form_fields()
        self.name_field = ft.TextField(label="ФИО", width=500)
        self.birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.position_field = ft.TextField(label="Должность", width=500)
        self.salary_field = ft.TextField(label="Зарплата", width=500)
        self.payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=500, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")
        self.company_popup = self.create_company_popup_button()
    
    def _get_base_query(self):
        return OfficeEmployee.select().where(OfficeEmployee.termination_date.is_null())
    
    def _apply_name_filter(self, query):
        return query.where(OfficeEmployee.full_name.contains(self.search_value))
    
    def _apply_company_filter(self, query, companies):
        from database.models import EmployeeCompany, Company
        company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
        employee_ids = [ec.office_employee_id for ec in EmployeeCompany.select().where(EmployeeCompany.company_id.in_(company_ids))]
        return query.where(OfficeEmployee.id.in_(employee_ids))
    
    def _apply_user_filter(self, query, user_id):
        return query.where(OfficeEmployee.created_by_user_id == user_id)
    
    def _get_employee_companies(self, employee):
        """Возвращает список компаний сотрудника"""
        from database.models import EmployeeCompany, Company
        companies = [ec.company.name for ec in EmployeeCompany.select().join(Company).where(EmployeeCompany.office_employee == employee)]
        return ", ".join(companies) if companies else "Не указано"
    
    def _get_order_field(self):
        return OfficeEmployee.full_name
    
    def _create_list_item(self, employee):
        return ft.ListTile(
            title=ft.Text(employee.full_name, weight="bold"),
            subtitle=ft.Text(f"Должность: {employee.position}"),
            on_click=lambda e, emp=employee: self.show_detail_dialog(emp)
        )
    
    def _get_detail_title(self):
        return "Карточка сотрудника офиса"
    
    def _get_detail_content(self, employee):
        return [
            ft.Row([
                ft.Column([
                    self.get_photo_widget(employee),
                    ft.Text(f"Дата рождения: {self.format_date(employee.birth_date)}", size=16),
                    ft.Text(f"Должность: {employee.position}", size=16),
                    ft.Text(f"Зарплата: {employee.salary} ₽", size=16),
                    ft.Text(f"Способ выдачи зарплаты: {employee.payment_method}", size=16),
                    ft.Text(f"Статус штата: {getattr(employee, 'staff_status', 'в штате')}", size=16),
                    ft.Text(f"Уголовная/административная ответственность: {getattr(employee, 'criminal_liability', 'нет')}", size=16),
                    ft.Text(f"Компании: {self._get_employee_companies(employee)}", size=16),
                ]),
                ft.Container(expand=True)
            ])
        ]
    
    def _get_add_title(self):
        return "Добавить сотрудника офиса"
    
    def _get_form_fields(self):
        return [self.name_field, self.birth_field, self.position_field, self.salary_field, self.payment_method_field, self.staff_status_dropdown, self.criminal_liability_dropdown, self.company_popup]
    
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
        
        # Получаем ID текущего пользователя
        created_by_user_id = None
        if hasattr(self.page, 'auth_manager') and self.page.auth_manager.current_user:
            created_by_user_id = self.page.auth_manager.current_user.id
        
        employee = OfficeEmployee.create(
            full_name=full_name,
            birth_date=birth_date,
            position=position_value,
            salary=salary,
            payment_method=payment_method_value or "на карту",
            staff_status=self.staff_status_dropdown.value or "в штате",
            criminal_liability=self.criminal_liability_dropdown.value or "нет",
            created_by_user_id=created_by_user_id
        )
        
        # Сохраняем связи с компаниями
        from database.models import Company, EmployeeCompany
        for checkbox in self.company_checkboxes:
            if checkbox.value:
                company = Company.get(Company.name == checkbox.label)
                EmployeeCompany.create(office_employee=employee, company=company)
        
        # Логирование
        if hasattr(self.page, 'auth_manager'):
            self.page.auth_manager.log_action("Создание сотрудника офиса", f"Создан сотрудник офиса: {full_name}")

        return True
    
    def _get_success_message(self):
        return "Сотрудник офиса добавлен!"
    
    def _get_page_title(self):
        return "Сотрудники офиса"
    
    def _get_add_button_text(self):
        return "Добавить сотрудника"
    
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        super()._create_edit_fields()
        self.edit_name_field = ft.TextField(label="ФИО", width=500)
        self.edit_birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.edit_position_field = ft.TextField(label="Должность", width=500)
        self.edit_salary_field = ft.TextField(label="Зарплата", width=500)
        self.edit_payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=500, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")])
        self.edit_company_popup = self.create_edit_company_popup_button()
    
    def _get_edit_fields(self):
        return [self.edit_name_field, self.edit_birth_field, self.edit_position_field, self.edit_salary_field, self.edit_payment_method_field, self.edit_staff_status_dropdown, self.edit_criminal_liability_dropdown, self.edit_company_popup]
    
    def _populate_edit_fields(self, employee):
        self.edit_name_field.value = employee.full_name
        self.edit_birth_field.value = self.format_date(employee.birth_date)
        self.edit_position_field.value = employee.position
        self.edit_salary_field.value = str(employee.salary)
        self.edit_payment_method_field.value = employee.payment_method
        self.edit_staff_status_dropdown.value = getattr(employee, 'staff_status', 'в штате')
        self.edit_criminal_liability_dropdown.value = getattr(employee, 'criminal_liability', 'нет')
        # Заполняем чекбоксы компаний
        from database.models import EmployeeCompany, Company
        employee_companies = [ec.company.name for ec in EmployeeCompany.select().join(Company).where(EmployeeCompany.office_employee == employee)]
        for checkbox in self.edit_company_checkboxes:
            checkbox.value = checkbox.label in employee_companies
        # Обновляем текст кнопки
        selected = [cb.label for cb in self.edit_company_checkboxes if cb.value]
        if len(selected) == len(self.edit_company_checkboxes):
            self.edit_company_popup_button.content.content.controls[0].value = "Все компании"
        elif len(selected) == 0:
            self.edit_company_popup_button.content.content.controls[0].value = "Нет компаний"
        else:
            self.edit_company_popup_button.content.content.controls[0].value = f"Выбрано: {len(selected)}"
    
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
        self.current_employee.salary = salary
        self.current_employee.payment_method = payment_method_value or "на карту"
        self.current_employee.staff_status = self.edit_staff_status_dropdown.value or "в штате"
        self.current_employee.criminal_liability = self.edit_criminal_liability_dropdown.value or "нет"
        
        self.current_employee.save()
        
        # Обновляем связи с компаниями
        from database.models import Company, EmployeeCompany
        # Удаляем старые связи
        EmployeeCompany.delete().where(EmployeeCompany.office_employee == self.current_employee).execute()
        # Создаем новые
        for checkbox in self.edit_company_checkboxes:
            if checkbox.value:
                company = Company.get(Company.name == checkbox.label)
                EmployeeCompany.create(office_employee=self.current_employee, company=company)
        
        # Логирование
        if hasattr(self.page, 'auth_manager'):
            self.page.auth_manager.log_action("Редактирование сотрудника офиса", f"Отредактирован сотрудник офиса: {self.current_employee.full_name}")
        
        return True
    
    def _get_employee_type(self):
        return "сотрудника офиса"
    
    def show_detail_dialog(self, employee):
        """Показывает диалог с вкладками (без личных карточек)"""
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Основная информация",
                    content=ft.Column(self._get_detail_content(employee), scroll=ft.ScrollMode.AUTO)
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
                ft.TextButton("Редактировать", on_click=lambda e: self.show_edit_dialog(employee)),
                ft.TextButton("Уволить", on_click=lambda e: self.show_termination_dialog(employee), style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Закрыть", on_click=lambda e: setattr(tabs_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        
        tabs_dialog.tabs_ref = tabs
        
        def on_tab_change(e):
            if e.control.selected_index == 1:  # Документы
                tabs.tabs[1].content = ft.Column(self._get_documents_content(employee, tabs_dialog), scroll=ft.ScrollMode.AUTO)
            self.page.update()
        
        tabs.on_change = on_tab_change
        
        self.page.overlay.append(tabs_dialog)
        tabs_dialog.open = True
        self.page.update()
    
    def get_employee_folder_type(self):
        return "Сотрудники офиса"

# Функция-обертка для совместимости
def office_employees_page(page: ft.Page = None) -> ft.Column:
    return OfficeEmployeesPage(page).render()