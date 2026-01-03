from base.base_calendar import BaseCalendar
from database.models import DutyShift, GuardEmployee, Object, ObjectRate
from peewee import fn
import flet as ft

class DutyCalendarPage(BaseCalendar):
    """Календарь дежурной части"""
    
    def __init__(self, page):
        super().__init__(page)
        self.selected_object = None
        self.selected_rate_id = None
        self._create_object_fields()
    
    def _create_object_fields(self):
        """Создает поля для работы с объектами"""
        # Поля для адреса
        self.address_dropdown = ft.Dropdown(label="Выберите адрес", width=500, visible=False)
        self.selected_address_id = None
        
        # Поля для ВЗН
        self.vzn_object_search = ft.TextField(label="Поиск объекта", width=500, on_change=lambda e: self.search_vzn_objects(e.control.value))
        self.vzn_object_search_results = ft.Column(visible=False)
        self.vzn_address_dropdown = ft.Dropdown(label="Выберите адрес", width=500, visible=False)
        self.vzn_rate_dropdown = ft.Dropdown(label="Выберите ставку", width=500, visible=False, on_change=lambda e: self.on_vzn_rate_change(e.control.value))
        self.vzn_selected_object = None
        self.vzn_selected_address_id = None
        self.vzn_selected_rate_id = None
    
    def select_vzn_object(self, obj):
        """Выбор объекта для ВЗН"""
        self.vzn_object_search.value = obj.name
        self.vzn_object_search_results.visible = False
        self.vzn_selected_object = obj
        self.load_vzn_object_addresses(obj)
        self.load_vzn_object_rates(obj)
        if self.page:
            self.page.update()
    
    def load_vzn_object_addresses(self, obj):
        """Загружает адреса объекта для ВЗН"""
        def operation():
            from database.models import ObjectAddress
            return list(ObjectAddress.select().where(ObjectAddress.object == obj))
        
        addresses = self.safe_db_operation(operation) or []
        
        self.vzn_address_dropdown.options.clear()
        if addresses:
            for addr in addresses:
                label = addr.address
                if addr.is_primary:
                    label += " (основной)"
                self.vzn_address_dropdown.options.append(
                    ft.dropdown.Option(key=str(addr.id), text=label)
                )
            primary_addr = next((addr for addr in addresses if addr.is_primary), addresses[0] if addresses else None)
            if primary_addr:
                self.vzn_address_dropdown.value = str(primary_addr.id)
                self.vzn_selected_address_id = primary_addr.id
            self.vzn_address_dropdown.on_change = lambda e: self.on_vzn_address_change(e.control.value)
            self.vzn_address_dropdown.visible = True
        else:
            self.vzn_address_dropdown.visible = False
    
    def on_vzn_address_change(self, address_id):
        """Обработчик смены адреса для ВЗН"""
        if address_id:
            self.vzn_selected_address_id = int(address_id)
    
    def _get_calendar_title(self):
        return "Календарь дежурной части"
    
    def _get_shifts_dialog_title(self):
        return "Дежурства"
    
    def _get_add_shift_dialog_title(self):
        return "Добавить дежурство"
    
    def _get_no_shifts_text(self):
        return "На эту дату дежурств нет"
    
    def _get_day_count_color(self):
        return ft.Colors.BLUE
    
    def _get_month_data(self, first_day, last_day):
        """Возвращает данные для месяца"""
        shifts = DutyShift.select(DutyShift.date, fn.COUNT(DutyShift.id).alias('count')).where(
            (DutyShift.date >= first_day) & (DutyShift.date <= last_day)
        ).group_by(DutyShift.date)
        
        cache = {}
        for shift in shifts:
            cache[shift.date] = shift.count
        
        return cache
    
    def _get_shifts_for_date(self, date_obj):
        """Возвращает смены для даты"""
        return list(DutyShift.select().join(GuardEmployee).where(DutyShift.date == date_obj))
    
    def _create_shift_list_item(self, shift):
        """Создает элемент списка смены"""
        is_vzn = shift.description and "ВЗН" in shift.description
        icon = ft.Icons.ATTACH_MONEY if is_vzn else ft.Icons.SECURITY
        color = ft.Colors.PURPLE if is_vzn else ft.Colors.BLUE
        
        return ft.ListTile(
            leading=ft.Icon(icon, color=color),
            title=ft.Text(shift.employee.full_name, weight="bold"),
            subtitle=ft.Text(f"Часы: {shift.hours} | Ставка: {shift.hourly_rate}₽ | {shift.description or ''}")
        )
    

    
    def search_vzn_objects(self, query):
        """Поиск объектов для ВЗН"""
        if not query or len(query) < 2:
            self.vzn_object_search_results.visible = False
            if self.page:
                self.page.update()
            return
        
        def operation():
            return list(Object.select().where(Object.name.contains(query))[:5])
        
        objects = self.safe_db_operation(operation) or []
        
        self.vzn_object_search_results.controls.clear()
        if objects:
            for obj in objects:
                self.vzn_object_search_results.controls.append(
                    ft.ListTile(title=ft.Text(obj.name), on_click=lambda e, object_item=obj: self.select_vzn_object(object_item))
                )
            self.vzn_object_search_results.visible = True
        else:
            self.vzn_object_search_results.controls.append(ft.Text("Объект не найден", color=ft.Colors.ERROR))
            self.vzn_object_search_results.visible = True
        if self.page:
            self.page.update()
    
    def select_vzn_object(self, obj):
        """Выбор объекта для ВЗН"""
        self.vzn_object_search.value = obj.name
        self.vzn_object_search_results.visible = False
        self.vzn_selected_object = obj
        self.load_vzn_object_rates(obj)
        if self.page:
            self.page.update()
    
    def load_vzn_object_rates(self, obj):
        """Загружает ставки объекта для ВЗН"""
        def operation():
            return list(ObjectRate.select().where(ObjectRate.object == obj))
        
        rates = self.safe_db_operation(operation) or []
        
        self.vzn_rate_dropdown.options.clear()
        if rates:
            for rate in rates:
                label = f"{rate.rate} ₽/ч"
                if rate.description:
                    label += f" - {rate.description}"
                if rate.is_default:
                    label += " (по умолчанию)"
                self.vzn_rate_dropdown.options.append(
                    ft.dropdown.Option(key=str(rate.id), text=label)
                )
            # Выбираем ставку по умолчанию
            default_rate = next((rate for rate in rates if rate.is_default), rates[0] if rates else None)
            if default_rate:
                self.vzn_rate_dropdown.value = str(default_rate.id)
                self.vzn_selected_rate_id = default_rate.id
            self.vzn_rate_dropdown.visible = True
        else:
            self.vzn_rate_dropdown.visible = False
    
    def on_vzn_rate_change(self, rate_id):
        """Обработчик смены ставки для ВЗН"""
        if rate_id:
            self.vzn_selected_rate_id = int(rate_id)
    
    def select_object(self, obj):
        """Выбор объекта"""
        super().select_object(obj)
        self.load_object_addresses(obj)
    
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
            primary_addr = next((addr for addr in addresses if addr.is_primary), addresses[0] if addresses else None)
            if primary_addr:
                self.address_dropdown.value = str(primary_addr.id)
                self.selected_address_id = primary_addr.id
            self.address_dropdown.on_change = lambda e: self.on_address_change(e.control.value)
            self.address_dropdown.visible = True
        else:
            self.address_dropdown.visible = False
        
        if self.page:
            self.page.update()
    
    def on_address_change(self, address_id):
        """Обработчик смены адреса"""
        if address_id:
            self.selected_address_id = int(address_id)
    
    def setup_add_shift_form(self):
        """Настраивает форму добавления смены"""
        self.object_search.value = ""
        self.employee_search.value = ""
        self.hours_dropdown.value = "12"
        self.description_field.value = ""
        self.search_results.visible = False
        self.object_search_results.visible = False
        self.rate_dropdown.visible = False
        self.selected_object = None
        self.selected_rate_id = None
        
        self.add_shift_dialog.content.controls = [
            ft.Text(f"Дата: {self.current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            self.object_search,
            self.object_search_results,
            self.address_dropdown,
            self.rate_dropdown,
            self.employee_search,
            self.search_results,
            self.hours_dropdown,
            self.description_field
        ]
    
    def save_new_shift(self):
        """Сохраняет новую смену"""
        if not self.employee_search.value or not self.hours_dropdown.value or not self.selected_object or not self.selected_rate_id:
            return
        
        def operation():
            employee = GuardEmployee.get(GuardEmployee.full_name == self.employee_search.value)
            rate = ObjectRate.get_by_id(self.selected_rate_id)
            
            DutyShift.create(
                employee=employee,
                date=self.current_shift_date,
                hours=int(self.hours_dropdown.value),
                hourly_rate=rate.rate,
                description=f"Объект: {self.selected_object.name}. {self.description_field.value or ''}"
            )
            return True
        
        if self.safe_db_operation(operation):
            self.close_add_shift_dialog()
            self.update_calendar()
            self.show_shifts_for_date(self.current_shift_date)
    
    def save_vzn(self):
        """Сохраняет новую ВЗН"""
        if not self.vzn_employee_search.value or not self.vzn_hours_dropdown.value or not self.vzn_selected_object or not self.vzn_selected_rate_id:
            return
        
        def operation():
            employee = GuardEmployee.get(GuardEmployee.full_name == self.vzn_employee_search.value)
            rate = ObjectRate.get_by_id(self.vzn_selected_rate_id)
            
            DutyShift.create(
                employee=employee,
                date=self.current_shift_date,
                hours=int(self.vzn_hours_dropdown.value),
                hourly_rate=rate.rate,
                description=f"ВЗН - Объект: {self.vzn_selected_object.name}. {self.vzn_description_field.value or ''}"
            )
            return True
        
        if self.safe_db_operation(operation):
            self.close_add_vzn_dialog()
            self.update_calendar()
            self.show_shifts_for_date(self.current_shift_date)
    
    def setup_add_vzn_form(self):
        """Настраивает форму добавления ВЗН"""
        self.vzn_employee_search.value = ""
        self.vzn_object_search.value = ""
        self.vzn_hours_dropdown.value = "12"
        self.vzn_description_field.value = ""
        self.vzn_search_results.visible = False
        self.vzn_object_search_results.visible = False
        self.vzn_rate_dropdown.visible = False
        self.vzn_selected_object = None
        self.vzn_selected_rate_id = None
        
        self.add_vzn_dialog.content.controls = [
            ft.Text(f"Дата: {self.current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            self.vzn_object_search,
            self.vzn_object_search_results,
            self.vzn_address_dropdown,
            self.vzn_rate_dropdown,
            self.vzn_employee_search,
            self.vzn_search_results,
            self.vzn_hours_dropdown,
            self.vzn_description_field
        ]

def duty_calendar_page(page=None):
    calendar_instance = DutyCalendarPage(page)
    return calendar_instance.render()