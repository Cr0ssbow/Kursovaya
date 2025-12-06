import flet as ft
from database.models import GuardEmployee, Company
from datetime import datetime
from base.base_employee_page import BaseEmployeePage

class EmployeesPage(BaseEmployeePage):
    """Страница сотрудников охраны"""
    
    def __init__(self, page: ft.Page):
        self.selected_rank = "Все разряды"
        super().__init__(page)
    
    def _create_form_fields(self):
        """Создает поля формы"""
        self.name_field = ft.TextField(label="ФИО", width=500)
        self.birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.certificate_field = ft.TextField(label="Номер удостоверения (буква№ 000000)", width=500, max_length=9, on_change=self._format_certificate_input)
        self.guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.medical_exam_field = ft.TextField(label="Дата прохождения медкомиссии (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.periodic_check_field = ft.TextField(label="Дата прохождения периодической проверки (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.guard_rank_field = ft.Dropdown(label="Разряд охранника", width=500, options=[ft.dropdown.Option("ОВН"), ft.dropdown.Option("Б")] + [ft.dropdown.Option(str(i)) for i in range(4, 7)])
        self.payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=500, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")
        self.company_checkboxes = self._create_company_checkboxes()
    
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        self.edit_name_field = ft.TextField(label="ФИО", width=500)
        self.edit_birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.edit_certificate_field = ft.TextField(label="Номер удостоверения (буква№ 000000)", width=500, max_length=9, on_change=self._format_certificate_input)
        self.edit_guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.edit_medical_exam_field = ft.TextField(label="Дата прохождения медкомиссии (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.edit_periodic_check_field = ft.TextField(label="Дата прохождения периодической проверки (дд.мм.гггг)", width=500, on_change=self.format_date_input, max_length=10)
        self.edit_guard_rank_field = ft.Dropdown(label="Разряд охранника", width=500, options=[ft.dropdown.Option("ОВН"), ft.dropdown.Option("Б")] + [ft.dropdown.Option(str(i)) for i in range(4, 7)])
        self.edit_payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=500, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")])
        self.edit_company_checkboxes = self._create_company_checkboxes(False)
    
    def _get_base_query(self):
        return GuardEmployee.select().where(GuardEmployee.termination_date.is_null())
    
    def _apply_search_filter(self, query):
        # Сначала применяем базовую фильтрацию
        query = super()._apply_search_filter(query)
        
        # Затем добавляем фильтр по разряду
        if self.selected_rank != "Все разряды":
            query = query.where(GuardEmployee.guard_rank == self.selected_rank)
        
        return query
    
    def _apply_name_filter(self, query):
        return query.where(GuardEmployee.full_name.contains(self.search_value))
    
    def _apply_company_filter(self, query, companies):
        from database.models import EmployeeCompany, Company
        company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
        employee_ids = [ec.guard_employee_id for ec in EmployeeCompany.select().where(EmployeeCompany.company_id.in_(company_ids))]
        return query.where(GuardEmployee.id.in_(employee_ids))
    
    def _get_employee_companies(self, employee):
        """Возвращает список компаний сотрудника"""
        from database.models import EmployeeCompany
        companies = [ec.company.name for ec in EmployeeCompany.select().join(Company).where(EmployeeCompany.guard_employee == employee)]
        return ", ".join(companies) if companies else "Не указано"
    
    def _get_sort_key(self, employee):
        """Возвращает ключ для сортировки по разряду"""
        rank = getattr(employee, 'guard_rank', '') or ''
        # Порядок сортировки: 4, 5, 6, Б, ОВН
        if rank == '4': return 1
        elif rank == '5': return 2
        elif rank == '6': return 3
        elif rank == 'Б': return 4
        elif rank == 'ОВН': return 5
        else: return 0
    
    def _get_secondary_sort_icon(self):
        return ft.Icons.MILITARY_TECH
    
    def _get_secondary_sort_name(self):
        return "разряду"
    
    def _get_order_field(self):
        return GuardEmployee.full_name
    
    def _create_list_item(self, employee):
        guard_rank_text = str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else "Не указано"
        return ft.ListTile(
            title=ft.Text(employee.full_name, weight="bold"),
            subtitle=ft.Text(f"Разряд: {guard_rank_text}"),
            on_click=lambda e, emp=employee: self.show_basic_info(emp)
        )
    
    def _get_detail_title(self):
        return "Информация о сотруднике"
    
    def show_basic_info(self, employee):
        """Показывает диалог с вкладками"""
        self.show_basic_info_with_tabs(employee)
    
    def _get_detail_content(self, employee):
        content = [
            ft.Row([
                ft.Column([
                    ft.Container(height=10),
                    self.get_photo_widget(employee),
                    ft.Text(f"Дата рождения: {self.format_date(employee.birth_date)}", size=16),
                    ft.Text(f"Номер удостоверения: {getattr(employee, 'certificate_number', '') or 'Не указано'}", size=16),
                    ft.Text(f"Дата выдачи УЧО: {self.format_date(getattr(employee, 'guard_license_date', None))}", size=16),
                    ft.Text(f"Разряд охранника: {str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else 'Не указано'}", size=16),
                    ft.Text(f"Медкомиссия: {self.format_date(getattr(employee, 'medical_exam_date', None))}", size=16),
                    ft.Text(f"Периодическая проверка: {self.format_date(getattr(employee, 'periodic_check_date', None))}", size=16),
                    ft.Text(f"Способ выдачи зарплаты: {getattr(employee, 'payment_method', 'на карту')}", size=16),
                    ft.Text(f"Компании: {self._get_employee_companies(employee)}", size=16),
                ], spacing=15),
                ft.Container(expand=True)
            ])
        ]
        return content
    

    
    def get_employee_folder_type(self):
        return "Сотрудники охраны"
    

    

    

    

    
    def _get_add_title(self):
        return "Добавить сотрудника"
    
    def _get_form_fields(self):
        company_row = ft.Row([ft.Text("Компании:", width=100)] + self.company_checkboxes)
        return [self.name_field, self.birth_field, self.certificate_field, self.guard_license_field, self.medical_exam_field, self.periodic_check_field, self.guard_rank_field, self.payment_method_field, company_row]
    
    def _get_edit_fields(self):
        return [self.edit_name_field, self.edit_birth_field, self.edit_certificate_field, self.edit_guard_license_field, self.edit_medical_exam_field, self.edit_periodic_check_field, self.edit_guard_rank_field, self.edit_payment_method_field, self.create_edit_company_dropdown()]
    
    def _populate_edit_fields(self, employee):
        self.edit_name_field.value = employee.full_name
        self.edit_birth_field.value = self.format_date(employee.birth_date)
        self.edit_certificate_field.value = getattr(employee, 'certificate_number', '') or ''
        self.edit_guard_license_field.value = self.format_date(getattr(employee, 'guard_license_date', None)) if hasattr(employee, 'guard_license_date') else ""
        self.edit_guard_rank_field.value = str(employee.guard_rank) if hasattr(employee, 'guard_rank') and employee.guard_rank else None
        self.edit_medical_exam_field.value = self.format_date(getattr(employee, 'medical_exam_date', None)) if hasattr(employee, 'medical_exam_date') else ""
        self.edit_periodic_check_field.value = self.format_date(getattr(employee, 'periodic_check_date', None)) if hasattr(employee, 'periodic_check_date') else ""
        self.edit_payment_method_field.value = getattr(employee, 'payment_method', 'на карту')
        
        # Заполняем чекбоксы компаний
        from database.models import EmployeeCompany
        employee_companies = [ec.company.name for ec in EmployeeCompany.select().join(Company).where(EmployeeCompany.guard_employee == employee)]
        for checkbox in self.edit_company_checkboxes:
            checkbox.value = checkbox.label in employee_companies
    
    def _save_operation(self):
        full_name = self.name_field.value.strip()
        birth_value = self.birth_field.value.strip()
        certificate_value = self.certificate_field.value.strip()
        guard_license_value = self.guard_license_field.value.strip()
        guard_rank_value = self.guard_rank_field.value
        medical_exam_value = self.medical_exam_field.value.strip()
        periodic_check_value = self.periodic_check_field.value.strip()
        payment_method_value = self.payment_method_field.value
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value:
            raise ValueError("Дата рождения обязательна!")
        
        birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        guard_license_date = datetime.strptime(guard_license_value, "%d.%m.%Y").date() if guard_license_value else None
        guard_rank = guard_rank_value if guard_rank_value else None
        medical_exam_date = datetime.strptime(medical_exam_value, "%d.%m.%Y").date() if medical_exam_value else None
        periodic_check_date = datetime.strptime(periodic_check_value, "%d.%m.%Y").date() if periodic_check_value else None
        
        employee = GuardEmployee.create(
            full_name=full_name,
            birth_date=birth_date,
            certificate_number=certificate_value or None,
            guard_license_date=guard_license_date,
            guard_rank=guard_rank,
            medical_exam_date=medical_exam_date,
            periodic_check_date=periodic_check_date,
            payment_method=payment_method_value or "на карту"
        )
        
        # Сохраняем связи с компаниями
        from database.models import Company, EmployeeCompany
        for checkbox in self.company_checkboxes:
            if checkbox.value:
                company = Company.get(Company.name == checkbox.label)
                EmployeeCompany.create(guard_employee=employee, company=company)
        

        return True
    
    def _save_edit_operation(self):
        full_name = self.edit_name_field.value.strip()
        birth_value = self.edit_birth_field.value.strip()
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value or birth_value == "Не указано":
            raise ValueError("Дата рождения обязательна!")
        
        self.current_employee.full_name = full_name
        self.current_employee.birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        self.current_employee.certificate_number = self.edit_certificate_field.value.strip() or None
        
        guard_license_value = self.edit_guard_license_field.value.strip()
        self.current_employee.guard_license_date = datetime.strptime(guard_license_value, "%d.%m.%Y").date() if guard_license_value and guard_license_value != "Не указано" else None
        
        self.current_employee.guard_rank = self.edit_guard_rank_field.value if self.edit_guard_rank_field.value else None
        
        medical_exam_value = self.edit_medical_exam_field.value.strip()
        self.current_employee.medical_exam_date = datetime.strptime(medical_exam_value, "%d.%m.%Y").date() if medical_exam_value and medical_exam_value != "Не указано" else None
        
        periodic_check_value = self.edit_periodic_check_field.value.strip()
        self.current_employee.periodic_check_date = datetime.strptime(periodic_check_value, "%d.%m.%Y").date() if periodic_check_value and periodic_check_value != "Не указано" else None
        
        self.current_employee.payment_method = self.edit_payment_method_field.value or 'на карту'
        
        self.current_employee.save()
        
        # Обновляем связи с компаниями
        from database.models import Company, EmployeeCompany
        # Удаляем старые связи
        EmployeeCompany.delete().where(EmployeeCompany.guard_employee == self.current_employee).execute()
        # Создаем новые
        for checkbox in self.edit_company_checkboxes:
            if checkbox.value:
                company = Company.get(Company.name == checkbox.label)
                EmployeeCompany.create(guard_employee=self.current_employee, company=company)
        return True
    
    def _get_success_message(self):
        return "Сотрудник добавлен!"
    
    def _get_page_title(self):
        return "Сотрудники охраны"
    
    def _get_add_button_text(self):
        return "Добавить сотрудника"
    
    def _get_employee_type(self):
        return "сотрудника"
    
    def on_rank_change(self, e):
        """Обработчик изменения фильтра по разряду"""
        self.selected_rank = e.control.value
        self.current_page = 0
        self.refresh_list()
        if self.page:
            self.page.update()
    
    def _format_certificate_input(self, e):
        """Форматирует ввод номера удостоверения"""
        value = e.control.value.upper().replace("№", "").replace(" ", "")
        if len(value) > 0 and value[0].isalpha():
            letter = value[0]
            numbers = ''.join(filter(str.isdigit, value[1:]))[:6]
            if numbers:
                e.control.value = f"{letter}№ {numbers}"
            else:
                e.control.value = f"{letter}№ "
        elif len(value) > 0 and not value[0].isalpha():
            e.control.value = ""
        self.page.update()
    
    def _get_search_row(self):
        """Переопределяем строку поиска для добавления фильтра по разряду"""
        return ft.Row([
            ft.TextField(label="Поиск по ФИО", width=300, on_change=self.on_search_change, autofocus=False, dense=True),
            ft.Dropdown(
                label="Разряд",
                width=200,
                value="Все разряды",
                options=[
                    ft.dropdown.Option("Все разряды"),
                    ft.dropdown.Option("ОВН"),
                    ft.dropdown.Option("Б"),
                    ft.dropdown.Option("4"),
                    ft.dropdown.Option("5"),
                    ft.dropdown.Option("6"),
                ],
                on_change=self.on_rank_change,
                dense=True,
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD if (self.sort_by_name and self.sort_ascending) else ft.Icons.ARROW_DOWNWARD if self.sort_by_name else ft.Icons.ABC,
                tooltip=f"По имени {'↑' if self.sort_ascending else '↓'}" if self.sort_by_name else "Сортировка по имени",
                on_click=self.sort_by_name_click
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD if (not self.sort_by_name and self.sort_ascending) else ft.Icons.ARROW_DOWNWARD if not self.sort_by_name else ft.Icons.MILITARY_TECH,
                tooltip=f"По разряду {'↑' if self.sort_ascending else '↓'}" if not self.sort_by_name else "Сортировка по разряду",
                on_click=self.sort_by_secondary_click
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
    

    

    

    

    

    

    

    

    

    

    

    


# Функция-обертка для совместимости
def employees_page(page: ft.Page = None) -> ft.Column:
    return EmployeesPage(page).render()