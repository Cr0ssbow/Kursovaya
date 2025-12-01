import flet as ft
import datetime
from database.models import Assignment, Employee, Object, ChiefEmployee, ChiefObjectAssignment, db
from peewee import *
from views.settings import load_cell_shape_from_db
from base.base_page import BasePage

# Словарь русских названий месяцев
RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

class CalendarPage(BasePage):
    """Страница календаря смен"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.current_year = datetime.date.today().year
        self.current_month = datetime.date.today().month
        self.current_assignment = None
        self.current_shift_date = None
        self._init_components()
    
    def _init_components(self):
        """Инициализация компонентов"""
        self.current_month_display = ft.Text("", size=24, weight="bold")
        self.calendar_grid_container = ft.Column()
        self._create_dialogs()
        self._create_form_fields()
        self.update_calendar()
    
    def _create_dialogs(self):
        """Создает диалоги"""
        self.shifts_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Смены на дату"),
            content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=400),
            actions=[
                ft.TextButton("Добавить смену", on_click=lambda e: self.open_add_shift_dialog()),
                ft.TextButton("Закрыть", on_click=lambda e: self.close_shifts_dialog())
            ]
        )
        
        self.add_shift_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Добавить смену"),
            content=ft.Column([], height=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Сохранить", on_click=lambda e: self.save_new_shift()),
                ft.TextButton("Отмена", on_click=lambda e: self.close_add_shift_dialog())
            ]
        )
        
        self.edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактирование смены"),
            content=ft.Column([], height=300, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Сохранить", on_click=lambda e: self.save_shift_changes()),
                ft.TextButton("Удалить", on_click=lambda e: self.confirm_delete_shift(), style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Отмена", on_click=lambda e: self.close_edit_dialog())
            ]
        )
        
        self.delete_confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Подтвердите удаление"),
            content=ft.Text("Вы уверены, что хотите удалить эту смену?"),
            actions=[
                ft.TextButton("Да", on_click=lambda e: self.delete_shift()),
                ft.TextButton("Отмена", on_click=lambda e: self.close_delete_confirm())
            ]
        )
    
    def _create_form_fields(self):
        """Создает поля форм"""
        # Поля редактирования смены
        self.absent_checkbox = ft.Checkbox(label="Пропуск", on_change=lambda e: self.toggle_absent_comment())
        self.absent_comment_field = ft.TextField(label="Комментарий к пропуску", visible=False, multiline=True)
        self.deduction_checkbox = ft.Checkbox(label="Удержание", on_change=lambda e: self.toggle_deduction_field())
        self.deduction_amount_field = ft.TextField(label="Сумма удержания", visible=False)
        self.bonus_amount_field = ft.TextField(label="Сумма премии", on_change=lambda e: self.toggle_bonus_comment())
        self.bonus_comment_field = ft.TextField(label="Комментарий к премии", visible=False, multiline=True)
        
        # Поля добавления смены
        self.employee_search = ft.TextField(label="Поиск сотрудника", width=300, on_change=lambda e: self.search_employees(e.control.value))
        self.search_results = ft.Column(visible=False)
        self.object_search = ft.TextField(label="Поиск объекта", width=300, on_change=lambda e: self.search_objects(e.control.value))
        self.object_search_results = ft.Column(visible=False)
        self.chief_display = ft.Text("Начальник: не назначен", size=16)
        self.selected_chief_id = None
        self.hours_dropdown = ft.Dropdown(label="Количество часов", options=[ft.dropdown.Option("12"), ft.dropdown.Option("24")], value="12", width=200)
        
        # Новые поля для выбора адреса и ставки
        self.address_dropdown = ft.Dropdown(label="Выберите адрес", width=400, visible=False)
        self.rate_dropdown = ft.Dropdown(label="Выберите ставку", width=300, visible=False)
        self.selected_object = None
        self.selected_address_id = None
        self.selected_rate_id = None
        
        self.load_chiefs()
    
    def close_shifts_dialog(self):
        self.shifts_dialog.open = False
        self.page.dialog = None
        self.page.update()
    
    def open_add_shift_dialog(self):
        self.setup_add_shift_form()
        self.page.dialog = self.add_shift_dialog
        self.add_shift_dialog.open = True
        self.page.update()
    
    def close_add_shift_dialog(self):
        self.add_shift_dialog.open = False
        self.page.dialog = self.shifts_dialog
        self.page.update()
    
    def close_edit_dialog(self):
        self.edit_dialog.open = False
        self.page.dialog = None
        self.page.update()
    
    def confirm_delete_shift(self):
        self.page.dialog = self.delete_confirm_dialog
        self.delete_confirm_dialog.open = True
        self.page.update()
    
    def close_delete_confirm(self):
        self.delete_confirm_dialog.open = False
        self.page.dialog = self.edit_dialog
        self.page.update()
    
    def delete_shift(self):
        if self.current_assignment:
            def operation():
                self.current_assignment.delete_instance()
                return True
            
            if self.safe_db_operation(operation):
                # Обновляем кеш для удаленной даты
                if hasattr(self, '_shifts_cache') and self.current_shift_date in self._shifts_cache:
                    self._shifts_cache[self.current_shift_date] = max(0, self._shifts_cache[self.current_shift_date] - 1)
                
                self.delete_confirm_dialog.open = False
                self.edit_dialog.open = False
                self.page.dialog = None
                self.update_calendar()
                self.show_shifts_for_date(self.current_shift_date)
    
    def toggle_absent_comment(self):
        self.absent_comment_field.visible = self.absent_checkbox.value
        self.update_bonus_fields_visibility()
        self.page.update()
    
    def toggle_deduction_field(self):
        self.deduction_amount_field.visible = self.deduction_checkbox.value
        self.update_bonus_fields_visibility()
        self.page.update()
    
    def update_bonus_fields_visibility(self):
        show_bonus = not self.absent_checkbox.value and not self.deduction_checkbox.value
        self.bonus_amount_field.visible = show_bonus
        self.bonus_comment_field.visible = show_bonus
    
    def toggle_bonus_comment(self):
        self.bonus_comment_field.visible = not self.absent_checkbox.value
        self.page.update()
    
    def edit_shift(self, assignment):
        self.current_assignment = assignment
        
        self.absent_checkbox.value = assignment.is_absent
        self.absent_comment_field.value = assignment.absent_comment or ""
        self.absent_comment_field.visible = assignment.is_absent
        
        self.deduction_checkbox.value = float(assignment.deduction_amount) > 0
        self.deduction_amount_field.value = str(float(assignment.deduction_amount))
        self.deduction_amount_field.visible = float(assignment.deduction_amount) > 0
        
        self.bonus_amount_field.value = str(float(assignment.bonus_amount))
        self.bonus_comment_field.value = assignment.bonus_comment or ""
        self.update_bonus_fields_visibility()
        
        self.edit_dialog.content.controls = [
            ft.Text(f"Сотрудник: {assignment.employee.full_name}", weight="bold"),
            ft.Text(f"Объект: {assignment.object.name}"),
            ft.Text(f"Дата: {assignment.date.strftime('%d.%m.%Y')}"),
            ft.Divider(),
            self.absent_checkbox,
            self.absent_comment_field,
            self.deduction_checkbox,
            self.deduction_amount_field,
            self.bonus_amount_field,
            self.bonus_comment_field
        ]
        
        self.page.dialog = self.edit_dialog
        self.edit_dialog.open = True
        self.page.update()
    
    def save_shift_changes(self):
        if self.current_assignment:
            def operation():
                self.current_assignment.is_absent = self.absent_checkbox.value
                self.current_assignment.absent_comment = self.absent_comment_field.value if self.absent_checkbox.value else None
                self.current_assignment.deduction_amount = float(self.deduction_amount_field.value or "0") if self.deduction_checkbox.value else 0
                self.current_assignment.bonus_amount = float(self.bonus_amount_field.value or "0") if not self.absent_checkbox.value else 0
                self.current_assignment.bonus_comment = self.bonus_comment_field.value if float(self.bonus_amount_field.value or "0") > 0 and not self.absent_checkbox.value else None
                self.current_assignment.save()
                return True
            
            if self.safe_db_operation(operation):
                self.close_edit_dialog()
                self.update_calendar()
                self.show_shifts_for_date(self.current_shift_date)
    
    def show_shifts_for_date(self, date_obj):
        self.current_shift_date = date_obj
        
        def operation():
            assignments = Assignment.select().join(Employee).switch(Assignment).join(Object).where(Assignment.date == date_obj)
            return list(assignments)
        
        assignments = self.safe_db_operation(operation) or []
        
        self.shifts_dialog.title.value = f"Смены на {date_obj.strftime('%d.%m.%Y')}"
        self.shifts_dialog.content.controls.clear()
        
        if assignments:
            for assignment in assignments:
                # Получаем адрес объекта
                def get_object_address(obj):
                    from database.models import ObjectAddress
                    primary_addr = ObjectAddress.select().where(
                        (ObjectAddress.object == obj) & (ObjectAddress.is_primary == True)
                    ).first()
                    if primary_addr:
                        return primary_addr.address
                    first_addr = ObjectAddress.select().where(ObjectAddress.object == obj).first()
                    return first_addr.address if first_addr else "не указан"
                
                object_address = self.safe_db_operation(lambda: get_object_address(assignment.object)) or "не указан"
                
                description_lines = [
                    ft.Text(f"Сотрудник: {assignment.employee.full_name}", weight="bold"),
                    ft.Text(f"Объект: {assignment.object.name}"),
                    ft.Text(f"Адрес: {object_address}"),
                    ft.Text(f"Начальник: {assignment.chief.full_name if assignment.chief else 'Не назначен'}"),
                    ft.Text(f"Часы: {assignment.hours}"),
                    ft.Text(f"Ставка: {assignment.hourly_rate} ₽/час")
                ]
                
                if assignment.is_absent:
                    if assignment.absent_comment:
                        description_lines.append(ft.Text(f"Пропуск: {assignment.absent_comment}", color=ft.Colors.RED))
                    else:
                        description_lines.append(ft.Text("Пропуск", color=ft.Colors.RED))
                
                if float(assignment.deduction_amount) > 0:
                    description_lines.append(ft.Text(f"Удержание: {assignment.deduction_amount} ₽", color=ft.Colors.ORANGE))
                
                if not assignment.is_absent and float(assignment.bonus_amount) > 0:
                    if assignment.bonus_comment:
                        description_lines.append(ft.Text(f"Премия: {assignment.bonus_amount} ₽ - {assignment.bonus_comment}", color=ft.Colors.GREEN))
                    else:
                        description_lines.append(ft.Text(f"Премия: {assignment.bonus_amount} ₽", color=ft.Colors.GREEN))
                
                self.shifts_dialog.content.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Column(description_lines, expand=True),
                                    ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e, a=assignment: self.edit_shift(a))
                                ])
                            ], spacing=5),
                            padding=10
                        )
                    )
                )
        else:
            self.shifts_dialog.content.controls.append(ft.Text("На эту дату смен нет", size=16, color=ft.Colors.GREY))
        
        self.page.dialog = self.shifts_dialog
        self.shifts_dialog.open = True
        self.page.update()
    
    def get_shifts_count_for_date(self, date_obj):
        if not hasattr(self, '_shifts_cache'):
            self._load_shifts_cache()
        return self._shifts_cache.get(date_obj, 0)
    
    def _load_shifts_cache(self):
        """Загружает количество смен для всего месяца одним запросом"""
        def operation():
            first_day = datetime.date(self.current_year, self.current_month, 1)
            if self.current_month == 12:
                last_day = datetime.date(self.current_year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                last_day = datetime.date(self.current_year, self.current_month + 1, 1) - datetime.timedelta(days=1)
            
            assignments = Assignment.select(Assignment.date, fn.COUNT(Assignment.id).alias('count')).where(
                (Assignment.date >= first_day) & (Assignment.date <= last_day)
            ).group_by(Assignment.date)
            
            cache = {}
            for assignment in assignments:
                cache[assignment.date] = assignment.count
            return cache
        
        self._shifts_cache = self.safe_db_operation(operation) or {}
    
    def create_day_cell(self, day, date_obj):
        shifts_count = self.get_shifts_count_for_date(date_obj)
        cell_shape = load_cell_shape_from_db()
        border_radius = 25 if cell_shape == "round" else 5
        
        return ft.Container(
            content=ft.Column([
                ft.Text(str(day), size=14, weight="bold"),
                ft.Text(f"{shifts_count}" if shifts_count > 0 else "", size=10, color=ft.Colors.BLUE)
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
            width=50,
            height=50,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=border_radius,
            on_click=lambda e: self.show_shifts_for_date(date_obj),
            alignment=ft.alignment.center
        )
    
    def get_calendar_grid(self, year, month):
        first_day = datetime.date(year, month, 1)
        if month == 12:
            days_in_month = (datetime.date(year + 1, 1, 1) - first_day).days
        else:
            days_in_month = (datetime.date(year, month + 1, 1) - first_day).days
        
        start_weekday = first_day.weekday()
        empty_slots = start_weekday
        
        days = []
        for _ in range(empty_slots):
            days.append(ft.Container(width=50, height=50))
        
        for day in range(1, days_in_month + 1):
            current_date = datetime.date(year, month, day)
            days.append(self.create_day_cell(day, current_date))
        
        while len(days) % 7 != 0:
            days.append(ft.Container(width=50, height=50))
        
        return ft.Column([
            ft.Row([
                ft.Text("Пн", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Вт", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Ср", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Чт", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Пт", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Сб", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Вс", weight="bold", width=50, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Row(days[i:i+7], alignment=ft.MainAxisAlignment.CENTER)
                for i in range(0, len(days), 7)
            ])
        ])
    
    def update_calendar(self):
        # Сбрасываем кеш при смене месяца
        if hasattr(self, '_shifts_cache'):
            delattr(self, '_shifts_cache')
        
        self.current_month_display.value = f"{RUSSIAN_MONTHS[self.current_month]} {self.current_year}"
        self.calendar_grid_container.controls = [self.get_calendar_grid(self.current_year, self.current_month)]
        if self.page:
            self.page.update()
    
    def change_month(self, direction):
        if direction == -1:
            self.current_month -= 1
            if self.current_month < 1:
                self.current_month = 12
                self.current_year -= 1
        else:
            self.current_month += 1
            if self.current_month > 12:
                self.current_month = 1
                self.current_year += 1
        self.update_calendar()
    
    def search_employees(self, query):
        if not query or len(query) < 2:
            self.search_results.visible = False
            self.page.update()
            return
        
        def operation():
            from datetime import date
            today = date.today()
            
            employees = []
            all_employees = Employee.select().where(
                (Employee.full_name.contains(query)) & 
                (Employee.termination_date.is_null())
            )
            
            for emp in all_employees:
                valid = True
                
                if emp.guard_license_date:
                    guard_expiry = emp.guard_license_date.replace(year=emp.guard_license_date.year + 5)
                    if guard_expiry < today:
                        valid = False
                
                if emp.medical_exam_date:
                    medical_expiry = emp.medical_exam_date.replace(year=emp.medical_exam_date.year + 1)
                    if medical_expiry < today:
                        valid = False
                
                if emp.periodic_check_date:
                    periodic_expiry = emp.periodic_check_date.replace(year=emp.periodic_check_date.year + 1)
                    if periodic_expiry < today:
                        valid = False
                
                if valid:
                    employees.append(emp)
            
            return employees[:5]
        
        employees = self.safe_db_operation(operation) or []
        
        self.search_results.controls.clear()
        if employees:
            for emp in employees:
                self.search_results.controls.append(
                    ft.ListTile(title=ft.Text(emp.full_name), on_click=lambda e, employee=emp: self.select_employee(employee))
                )
            self.search_results.visible = True
        else:
            self.search_results.controls.append(ft.Text("Сотрудник не найден", color=ft.Colors.ERROR))
            self.search_results.visible = True
        self.page.update()
    
    def select_employee(self, employee):
        self.employee_search.value = employee.full_name
        self.search_results.visible = False
        self.page.update()
    
    def search_objects(self, query):
        if not query or len(query) < 2:
            self.object_search_results.visible = False
            self.page.update()
            return
        
        def operation():
            return list(Object.select().where(Object.name.contains(query))[:5])
        
        objects = self.safe_db_operation(operation) or []
        
        self.object_search_results.controls.clear()
        if objects:
            for obj in objects:
                self.object_search_results.controls.append(
                    ft.ListTile(title=ft.Text(obj.name), on_click=lambda e, object_item=obj: self.select_object(object_item))
                )
            self.object_search_results.visible = True
        else:
            self.object_search_results.controls.append(ft.Text("Объект не найден", color=ft.Colors.ERROR))
            self.object_search_results.visible = True
        self.page.update()
    
    def select_object(self, obj):
        self.object_search.value = obj.name
        self.object_search_results.visible = False
        self.selected_object = obj
        self.load_object_addresses(obj)
        self.load_object_rates(obj)
        self.auto_assign_chief(obj)
        self.page.update()
    
    def load_chiefs(self):
        """Загружает список начальников"""
        pass  # Не нужно, так как начальник назначается автоматически
    
    def load_object_addresses(self, obj):
        """Загружает адреса объекта"""
        def operation():
            from database.models import ObjectAddress
            return list(ObjectAddress.select().where(ObjectAddress.object == obj))
        
        addresses = self.safe_db_operation(operation) or []
        
        self.address_dropdown.options.clear()
        if addresses:
            for addr in addresses:
                label = addr.address
                if addr.is_primary:
                    label += " (основной)"
                self.address_dropdown.options.append(
                    ft.dropdown.Option(key=str(addr.id), text=label)
                )
            # Выбираем основной адрес по умолчанию
            primary_addr = next((addr for addr in addresses if addr.is_primary), addresses[0] if addresses else None)
            if primary_addr:
                self.address_dropdown.value = str(primary_addr.id)
                self.selected_address_id = primary_addr.id
            self.address_dropdown.on_change = lambda e: self.on_address_change(e.control.value)
            self.address_dropdown.visible = True
        else:
            self.address_dropdown.visible = False
    
    def load_object_rates(self, obj):
        """Загружает ставки объекта"""
        def operation():
            from database.models import ObjectRate
            return list(ObjectRate.select().where(ObjectRate.object == obj))
        
        rates = self.safe_db_operation(operation) or []
        
        self.rate_dropdown.options.clear()
        if rates:
            for rate in rates:
                label = f"{rate.rate} ₽/ч"
                if rate.description:
                    label += f" - {rate.description}"
                if rate.is_default:
                    label += " (по умолчанию)"
                self.rate_dropdown.options.append(
                    ft.dropdown.Option(key=str(rate.id), text=label)
                )
            # Выбираем ставку по умолчанию
            default_rate = next((rate for rate in rates if rate.is_default), rates[0] if rates else None)
            if default_rate:
                self.rate_dropdown.value = str(default_rate.id)
                self.selected_rate_id = default_rate.id
            self.rate_dropdown.visible = True
            self.rate_dropdown.on_change = lambda e: self.on_rate_change(e.control.value)
        else:
            self.rate_dropdown.visible = False
    
    def on_address_change(self, address_id):
        """Обработчик смены адреса"""
        if address_id:
            self.selected_address_id = int(address_id)
    
    def on_rate_change(self, rate_id):
        """Обработчик смены ставки"""
        if rate_id:
            self.selected_rate_id = int(rate_id)
    
    def auto_assign_chief(self, obj):
        """Автоматически назначает начальника на основе объекта"""
        def operation():
            # Получаем первого начальника, закрепленного за этим объектом
            assignment = ChiefObjectAssignment.select().where(ChiefObjectAssignment.object == obj).first()
            if assignment and assignment.chief.termination_date is None:
                return assignment.chief
            return None
        
        chief = self.safe_db_operation(operation)
        if chief:
            self.chief_display.value = f"Начальник: {chief.full_name}"
            self.selected_chief_id = chief.id
        else:
            self.chief_display.value = "Начальник: не назначен"
            self.selected_chief_id = None
    
    def setup_add_shift_form(self):
        self.employee_search.value = ""
        self.object_search.value = ""
        self.selected_chief_id = None
        self.selected_object = None
        self.selected_address_id = None
        self.selected_rate_id = None
        self.hours_dropdown.value = "12"
        self.search_results.visible = False
        self.object_search_results.visible = False
        self.address_dropdown.visible = False
        self.rate_dropdown.visible = False
        self.chief_display.value = "Начальник: не назначен"
        
        self.add_shift_dialog.content.controls = [
            ft.Text(f"Дата: {self.current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            self.employee_search,
            self.search_results,
            self.object_search,
            self.object_search_results,
            self.address_dropdown,
            self.rate_dropdown,
            self.chief_display,
            self.hours_dropdown
        ]
    
    def save_new_shift(self):
        if not self.employee_search.value or not self.object_search.value or not self.hours_dropdown.value or not self.selected_rate_id:
            return
        
        def operation():
            from database.models import ObjectRate
            employee = Employee.get(Employee.full_name == self.employee_search.value)
            obj = Object.get(Object.name == self.object_search.value)
            rate = ObjectRate.get_by_id(self.selected_rate_id)
            
            chief = None
            if self.selected_chief_id:
                chief = ChiefEmployee.get_by_id(self.selected_chief_id)
            
            Assignment.create(
                employee=employee,
                object=obj,
                chief=chief,
                date=self.current_shift_date,
                hours=int(self.hours_dropdown.value),
                hourly_rate=rate.rate
            )
            
            salary_increase = float(rate.rate) * int(self.hours_dropdown.value)
            new_salary = float(employee.salary) + salary_increase
            new_hours = employee.hours_worked + int(self.hours_dropdown.value)
            
            employee.salary = new_salary
            employee.hours_worked = new_hours
            employee.save()
            return True
        
        if self.safe_db_operation(operation):
            # Обновляем кеш для добавленной даты
            if hasattr(self, '_shifts_cache'):
                self._shifts_cache[self.current_shift_date] = self._shifts_cache.get(self.current_shift_date, 0) + 1
            
            self.close_add_shift_dialog()
            self.update_calendar()
            self.show_shifts_for_date(self.current_shift_date)
    
    def render(self) -> ft.Column:
        """Возвращает интерфейс страницы"""
        # Добавляем диалоги в overlay страницы
        if self.edit_dialog not in self.page.overlay:
            self.page.overlay.append(self.edit_dialog)
        if self.delete_confirm_dialog not in self.page.overlay:
            self.page.overlay.append(self.delete_confirm_dialog)
        if self.add_shift_dialog not in self.page.overlay:
            self.page.overlay.append(self.add_shift_dialog)
        
        return ft.Column([
            ft.Text("Календарь смен", size=24, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: self.change_month(-1)),
                self.current_month_display,
                ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: self.change_month(1))
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.calendar_grid_container
        ], spacing=10, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

# Функция-обертка для совместимости
def calendar_page(page: ft.Page = None):
    calendar_instance = CalendarPage(page)
    return calendar_instance.render(), calendar_instance.shifts_dialog