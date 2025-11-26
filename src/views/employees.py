import flet as ft
from database.models import GuardEmployee
from datetime import datetime
from base.base_employee_page import BaseEmployeePage

class EmployeesPage(BaseEmployeePage):
    """Страница сотрудников охраны"""
    
    def __init__(self, page: ft.Page):
        self.selected_rank = "Все разряды"
        super().__init__(page)
    
    def _create_form_fields(self):
        """Создает поля формы"""
        self.name_field = ft.TextField(label="ФИО", width=300)
        self.birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.certificate_field = ft.TextField(label="Номер удостоверения (буква№ 000000)", width=200, max_length=9, on_change=self._format_certificate_input)
        self.guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.medical_exam_field = ft.TextField(label="Дата прохождения медкомиссии (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.periodic_check_field = ft.TextField(label="Дата прохождения периодической проверки (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option(str(i)) for i in range(3, 7)])
        self.payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")
    
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        self.edit_name_field = ft.TextField(label="ФИО", width=300)
        self.edit_birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.edit_certificate_field = ft.TextField(label="Номер удостоверения (буква№ 000000)", width=200, max_length=9, on_change=self._format_certificate_input)
        self.edit_guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.edit_medical_exam_field = ft.TextField(label="Дата прохождения медкомиссии (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.edit_periodic_check_field = ft.TextField(label="Дата прохождения периодической проверки (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.edit_guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option(str(i)) for i in range(3, 7)])
        self.edit_payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")])
        self.edit_company_field = ft.Dropdown(label="Компания", width=150, options=[ft.dropdown.Option("Легион"), ft.dropdown.Option("Норд")])
    
    def _create_table(self):
        """Создает таблицу"""
        self.employees_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ФИО", width=400)),
                ft.DataColumn(ft.Text("Разряд", width=100)),
            ],
            rows=[],
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            heading_row_height=70,
            data_row_min_height=50,
            data_row_max_height=50,
            column_spacing=10,
            width=600,
            height=707
        )
    
    def _get_base_query(self):
        return GuardEmployee.select().where(GuardEmployee.termination_date.is_null())
    
    def _apply_search_filter(self, query):
        # Сначала применяем базовую фильтрацию
        query = super()._apply_search_filter(query)
        
        # Затем добавляем фильтр по разряду
        if self.selected_rank != "Все разряды":
            query = query.where(GuardEmployee.guard_rank == int(self.selected_rank))
        
        return query
    
    def _apply_name_filter(self, query):
        return query.where(GuardEmployee.full_name.contains(self.search_value))
    
    def _apply_company_filter(self, query, companies):
        return query.where(GuardEmployee.company.in_(companies))
    
    def _get_order_field(self):
        return GuardEmployee.full_name
    
    def _create_table_row(self, employee):
        guard_rank_text = str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else "Не указано"
        return ft.DataRow(cells=[
            ft.DataCell(ft.Text(employee.full_name), on_tap=lambda e, emp=employee: self.show_detail_dialog(emp)),
            ft.DataCell(ft.Text(guard_rank_text)),
        ])
    
    def _get_detail_title(self):
        return "Информация о сотруднике"
    
    def _get_detail_content(self, employee):
        return [
            ft.Text(f"Дата рождения: {self.format_date(employee.birth_date)}", size=16),
            ft.Text(f"Номер удостоверения: {getattr(employee, 'certificate_number', '') or 'Не указано'}", size=16),
            ft.Text(f"Дата выдачи УЧО: {self.format_date(getattr(employee, 'guard_license_date', None))}", size=16),
            ft.Text(f"Разряд охранника: {str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else 'Не указано'}", size=16),
            ft.Text(f"Медкомиссия: {self.format_date(getattr(employee, 'medical_exam_date', None))}", size=16),
            ft.Text(f"Периодическая проверка: {self.format_date(getattr(employee, 'periodic_check_date', None))}", size=16),
            ft.Text(f"Способ выдачи зарплаты: {getattr(employee, 'payment_method', 'на карту')}", size=16),
            ft.Text(f"Компания: {getattr(employee, 'company', 'Легион')}", size=16),
        ]
    
    def _get_add_title(self):
        return "Добавить сотрудника"
    
    def _get_form_fields(self):
        return [self.name_field, self.birth_field, self.certificate_field, self.guard_license_field, self.medical_exam_field, self.periodic_check_field, self.guard_rank_field, self.payment_method_field, self.company_field]
    
    def _get_edit_fields(self):
        return [self.edit_name_field, self.edit_birth_field, self.edit_certificate_field, self.edit_guard_license_field, self.edit_medical_exam_field, self.edit_periodic_check_field, self.edit_guard_rank_field, self.edit_payment_method_field, self.edit_company_field]
    
    def _populate_edit_fields(self, employee):
        self.edit_name_field.value = employee.full_name
        self.edit_birth_field.value = self.format_date(employee.birth_date)
        self.edit_certificate_field.value = getattr(employee, 'certificate_number', '') or ''
        self.edit_guard_license_field.value = self.format_date(getattr(employee, 'guard_license_date', None)) if hasattr(employee, 'guard_license_date') else ""
        self.edit_guard_rank_field.value = str(employee.guard_rank) if hasattr(employee, 'guard_rank') and employee.guard_rank else None
        self.edit_medical_exam_field.value = self.format_date(getattr(employee, 'medical_exam_date', None)) if hasattr(employee, 'medical_exam_date') else ""
        self.edit_periodic_check_field.value = self.format_date(getattr(employee, 'periodic_check_date', None)) if hasattr(employee, 'periodic_check_date') else ""
        self.edit_payment_method_field.value = getattr(employee, 'payment_method', 'на карту')
        self.edit_company_field.value = getattr(employee, 'company', 'Легион')
    
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
        guard_rank = int(guard_rank_value) if guard_rank_value else None
        medical_exam_date = datetime.strptime(medical_exam_value, "%d.%m.%Y").date() if medical_exam_value else None
        periodic_check_date = datetime.strptime(periodic_check_value, "%d.%m.%Y").date() if periodic_check_value else None
        
        GuardEmployee.create(
            full_name=full_name,
            birth_date=birth_date,
            certificate_number=certificate_value or None,
            guard_license_date=guard_license_date,
            guard_rank=guard_rank,
            medical_exam_date=medical_exam_date,
            periodic_check_date=periodic_check_date,
            payment_method=payment_method_value or "на карту",
            company=self.company_field.value or "Легион"
        )
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
        
        self.current_employee.guard_rank = int(self.edit_guard_rank_field.value) if self.edit_guard_rank_field.value else None
        
        medical_exam_value = self.edit_medical_exam_field.value.strip()
        self.current_employee.medical_exam_date = datetime.strptime(medical_exam_value, "%d.%m.%Y").date() if medical_exam_value and medical_exam_value != "Не указано" else None
        
        periodic_check_value = self.edit_periodic_check_field.value.strip()
        self.current_employee.periodic_check_date = datetime.strptime(periodic_check_value, "%d.%m.%Y").date() if periodic_check_value and periodic_check_value != "Не указано" else None
        
        self.current_employee.payment_method = self.edit_payment_method_field.value or 'на карту'
        self.current_employee.company = self.edit_company_field.value or 'Легион'
        self.current_employee.save()
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
        self.refresh_table()
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
                    ft.dropdown.Option("3"),
                    ft.dropdown.Option("4"),
                    ft.dropdown.Option("5"),
                    ft.dropdown.Option("6"),
                ],
                on_change=self.on_rank_change,
                dense=True,
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)

# Функция-обертка для совместимости
def employees_page(page: ft.Page = None) -> ft.Column:
    return EmployeesPage(page).render()