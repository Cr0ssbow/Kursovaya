import flet as ft
from abc import abstractmethod
from datetime import datetime, date, timedelta
from base.base_page import BasePage
import calendar
from peewee import fn

# Словарь русских названий месяцев
RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

class BaseCalendar(BasePage):
    """Базовый класс для календарей"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.current_date = date.today()
        self.selected_date = None
        self.calendar_container = None
        self.dialog = None
        self.current_shift_date = None
        self._init_components()
    
    def _init_components(self):
        """Инициализация компонентов календаря"""
        self.current_month_display = ft.Text("", size=24, weight="bold")
        self.calendar_grid_container = ft.Column()
        self._shifts_cache = {}
        self._create_dialogs()
        self._create_form_fields()
        self.update_calendar()
    
    def _create_dialogs(self):
        """Создает диалоги"""
        self.shifts_list_view = ft.ListView(expand=True, spacing=5, height=500)
        
        # Контролы поиска и фильтрации
        self.show_shifts_cb = ft.Checkbox(label="Обычные смены", value=True, on_change=lambda e: self.update_shifts_list())
        self.show_vzn_cb = ft.Checkbox(label="ВЗН", value=True, on_change=lambda e: self.update_shifts_list())
        self.employee_search_field = ft.TextField(label="Поиск по сотруднику", width=200, on_change=lambda e: self.reset_page_and_update())
        self.object_search_field = ft.TextField(label="Поиск по объекту", width=200, on_change=lambda e: self.reset_page_and_update())
        self.shifts_page = 0
        self.shifts_page_size = 12
        self.shifts_page_text = ft.Text("Страница 1")
        
        self.shifts_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self._get_shifts_dialog_title()),
            content=ft.Column([
                ft.Row([
                    self.show_shifts_cb,
                    self.show_vzn_cb
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    self.employee_search_field,
                    self.object_search_field
                ], alignment=ft.MainAxisAlignment.START),
                ft.Divider(),
                self.shifts_list_view,
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.prev_shifts_page()),
                    self.shifts_page_text,
                    ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=lambda e: self.next_shifts_page())
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], height=650, width=900),
            actions=[
                *([ft.TextButton(self._get_add_shift_button_text(), on_click=lambda e: self.open_add_shift_dialog())] if self._get_add_shift_button_text() else []),
                *([ft.TextButton(self._get_add_vzn_button_text(), on_click=lambda e: self.open_add_vzn_dialog())] if self._get_add_vzn_button_text() else []),
                ft.TextButton("Закрыть", on_click=lambda e: self.close_shifts_dialog())
            ]
        )
        
        self.add_shift_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self._get_add_shift_dialog_title()),
            content=ft.Column([], height=500, width=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Сохранить", on_click=lambda e: self.save_new_shift()),
                ft.TextButton("Отмена", on_click=lambda e: self.close_add_shift_dialog())
            ]
        )
        
        self.add_vzn_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self._get_add_vzn_dialog_title()),
            content=ft.Column([], height=500, width=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Сохранить", on_click=lambda e: self.save_vzn()),
                ft.TextButton("Отмена", on_click=lambda e: self.close_add_vzn_dialog())
            ]
        )
    
    def _create_form_fields(self):
        """Создает поля форм"""
        # Поля для добавления смены
        self.employee_search = ft.TextField(label="Поиск сотрудника", width=500, on_change=lambda e: self.search_employees(e.control.value))
        self.search_results = ft.Column(visible=False)
        self.object_search = ft.TextField(label="Поиск объекта", width=500, on_change=lambda e: self.search_objects(e.control.value))
        self.object_search_results = ft.Column(visible=False)
        self.rate_dropdown = ft.Dropdown(label="Выберите ставку", width=500, visible=False, on_change=lambda e: self.on_rate_change(e.control.value))
        self.selected_object = None
        self.selected_rate_id = None
        self.hours_dropdown = ft.Dropdown(label="Количество часов", options=[ft.dropdown.Option("12"), ft.dropdown.Option("24")], value="12", width=500)
        self.description_field = ft.TextField(label="Описание", multiline=True, width=500)
        
        # Поля для ВЗН
        self.vzn_employee_search = ft.TextField(label="Поиск сотрудника", width=500, on_change=lambda e: self.search_vzn_employees(e.control.value))
        self.vzn_search_results = ft.Column(visible=False)
        self.vzn_hours_dropdown = ft.Dropdown(label="Количество часов", options=[ft.dropdown.Option("12"), ft.dropdown.Option("24")], value="12", width=500)
        self.vzn_description_field = ft.TextField(label="Описание", multiline=True, width=500)
    
    def get_calendar_grid(self, year, month):
        """Создает сетку календаря"""
        first_day = date(year, month, 1)
        if month == 12:
            days_in_month = (date(year + 1, 1, 1) - first_day).days
        else:
            days_in_month = (date(year, month + 1, 1) - first_day).days
        
        start_weekday = first_day.weekday()
        empty_slots = start_weekday
        
        days = []
        for _ in range(empty_slots):
            days.append(ft.Container(width=50, height=50))
        
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
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
        """Обновляет календарь"""
        if hasattr(self, '_shifts_cache'):
            delattr(self, '_shifts_cache')
        
        self.current_month_display.value = f"{RUSSIAN_MONTHS[self.current_month]} {self.current_year}"
        self.calendar_grid_container.controls = [self.get_calendar_grid(self.current_year, self.current_month)]
        if self.page:
            self.page.update()
    
    def change_month(self, direction):
        """Смена месяца"""
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
    
    def create_day_cell(self, day, date_obj):
        """Создает ячейку дня"""
        shifts_count = self.get_shifts_count_for_date(date_obj)
        
        return ft.Container(
            content=ft.Column([
                ft.Text(str(day), size=14, weight="bold"),
                ft.Text(f"{shifts_count}" if shifts_count > 0 else "", size=10, color=self._get_day_count_color())
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
            width=50,
            height=50,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            on_click=lambda e: self.show_shifts_for_date(date_obj),
            alignment=ft.alignment.center
        )
    
    def get_shifts_count_for_date(self, date_obj):
        """Получает количество смен для даты"""
        if not hasattr(self, '_shifts_cache'):
            self._load_shifts_cache()
        return self._shifts_cache.get(date_obj, 0)
    
    def _load_shifts_cache(self):
        """Загружает кеш смен для месяца"""
        def operation():
            first_day = date(self.current_year, self.current_month, 1)
            if self.current_month == 12:
                last_day = date(self.current_year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(self.current_year, self.current_month + 1, 1) - timedelta(days=1)
            
            return self._get_month_data(first_day, last_day)
        
        self._shifts_cache = self.safe_db_operation(operation) or {}
    
    def _create_day_content(self, day, cell_date, day_data, is_today):
        """Создает содержимое ячейки дня (переопределяется в дочерних классах)"""
        return ft.Column([
            ft.Text(
                str(day),
                weight="bold" if is_today else "normal",
                size=14
            ),
            ft.Text(
                str(len(day_data)) if day_data and hasattr(day_data, '__len__') else str(day_data) if day_data else "",
                size=10,
                color=ft.Colors.BLUE
            )
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
    
    def _prev_month(self, e):
        """Переход к предыдущему месяцу"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self._create_calendar()
        self.page.update()
    
    def _next_month(self, e):
        """Переход к следующему месяцу"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self._create_calendar()
        self.page.update()
    
    def show_shifts_for_date(self, date_obj):
        """Показывает смены для даты"""
        self.current_shift_date = date_obj
        self.shifts_page = 0
        
        # Открываем диалог сразу с заглушкой
        self.shifts_dialog.title.value = f"{self._get_shifts_dialog_title()} на {date_obj.strftime('%d.%m.%Y')}"
        self.shifts_list_view.controls.clear()
        self.shifts_list_view.controls.append(ft.Text("Загрузка...", size=16))
        self.shifts_page_text.value = "Страница 1"
        
        self.shifts_dialog.open = True
        self.page.update()
        
        # Загружаем данные асинхронно
        shifts_data = self._get_shifts_for_date(date_obj)
        self.all_shifts = shifts_data if shifts_data else []
        
        self.update_shifts_list()
    
    def close_shifts_dialog(self):
        """Закрывает диалог смен"""
        self.shifts_dialog.open = False
        self.page.update()
    
    def open_add_shift_dialog(self):
        """Открывает диалог добавления смены"""
        self.setup_add_shift_form()
        self.shifts_dialog.open = False
        self.add_shift_dialog.open = True
        self.page.update()
    
    def close_add_shift_dialog(self):
        """Закрывает диалог добавления смены"""
        self.add_shift_dialog.open = False
        self.shifts_dialog.open = True
        self.page.update()
    
    def open_add_vzn_dialog(self):
        """Открывает диалог добавления ВЗН"""
        self.setup_add_vzn_form()
        self.shifts_dialog.open = False
        self.add_vzn_dialog.open = True
        self.page.update()
    
    def close_add_vzn_dialog(self):
        """Закрывает диалог добавления ВЗН"""
        self.add_vzn_dialog.open = False
        self.shifts_dialog.open = True
        self.page.update()
    
    def setup_add_shift_form(self):
        """Настраивает форму добавления смены"""
        self.employee_search.value = ""
        self.hours_dropdown.value = "12"
        self.hourly_rate_field.value = "500"
        self.description_field.value = ""
        self.search_results.visible = False
        
        self.add_shift_dialog.content.controls = [
            ft.Text(f"Дата: {self.current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            self.employee_search,
            self.search_results,
            self.hours_dropdown,
            self.hourly_rate_field,
            self.description_field
        ]
    
    def setup_add_vzn_form(self):
        """Настраивает форму добавления ВЗН"""
        self.vzn_employee_search.value = ""
        self.vzn_hours_dropdown.value = "12"
        self.vzn_description_field.value = ""
        self.vzn_search_results.visible = False
        
        # Основные поля
        controls = [
            ft.Text(f"Дата: {self.current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            self.vzn_employee_search,
            self.vzn_search_results,
        ]
        
        # Добавляем поля объекта и ставки, если они есть
        if hasattr(self, 'vzn_object_search'):
            controls.extend([
                self.vzn_object_search,
                self.vzn_object_search_results,
                self.vzn_rate_dropdown,
            ])
        
        controls.extend([
            self.vzn_hours_dropdown,
            self.vzn_description_field
        ])
        
        self.add_vzn_dialog.content.controls = controls
    
    def search_employees(self, query):
        """Поиск сотрудников"""
        if not query or len(query) < 2:
            self.search_results.visible = False
            if self.page:
                self.page.update()
            return
        
        def operation():
            from database.models import GuardEmployee
            return list(GuardEmployee.select().where(
                (GuardEmployee.full_name.contains(query)) & 
                (GuardEmployee.termination_date.is_null())
            )[:5])
        
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
        if self.page:
            self.page.update()
    
    def select_employee(self, employee):
        """Выбор сотрудника"""
        self.employee_search.value = employee.full_name
        self.search_results.visible = False
        if self.page:
            self.page.update()
    
    def search_vzn_employees(self, query):
        """Поиск сотрудников для ВЗН"""
        if not query or len(query) < 2:
            self.vzn_search_results.visible = False
            if self.page:
                self.page.update()
            return
        
        def operation():
            from database.models import GuardEmployee
            return list(GuardEmployee.select().where(
                (GuardEmployee.full_name.contains(query)) & 
                (GuardEmployee.termination_date.is_null())
            )[:5])
        
        employees = self.safe_db_operation(operation) or []
        
        self.vzn_search_results.controls.clear()
        if employees:
            for emp in employees:
                self.vzn_search_results.controls.append(
                    ft.ListTile(title=ft.Text(emp.full_name), on_click=lambda e, employee=emp: self.select_vzn_employee(employee))
                )
            self.vzn_search_results.visible = True
        else:
            self.vzn_search_results.controls.append(ft.Text("Сотрудник не найден", color=ft.Colors.ERROR))
            self.vzn_search_results.visible = True
        if self.page:
            self.page.update()
    
    def select_vzn_employee(self, employee):
        """Выбор сотрудника для ВЗН"""
        self.vzn_employee_search.value = employee.full_name
        self.vzn_search_results.visible = False
        if self.page:
            self.page.update()
    
    def reset_page_and_update(self):
        """Сбрасывает на первую страницу и обновляет список"""
        self.shifts_page = 0
        self.update_shifts_list()
    
    def update_shifts_list(self):
        """Обновляет список смен с пагинацией"""
        # Фильтрация по типу
        all_items = []
        if self.show_shifts_cb.value:
            # Обычные смены (не ВЗН)
            all_items.extend([item for item in self.all_shifts if not (hasattr(item, 'description') and item.description and "ВЗН" in item.description)])
        if self.show_vzn_cb.value:
            # ВЗН
            all_items.extend([item for item in self.all_shifts if hasattr(item, 'description') and item.description and "ВЗН" in item.description])
        
        # Поиск по сотруднику
        employee_query = self.employee_search_field.value.lower() if self.employee_search_field.value else ""
        if employee_query:
            all_items = [item for item in all_items if employee_query in item.employee.full_name.lower()]
        
        # Поиск по объекту (из описания)
        object_query = self.object_search_field.value.lower() if self.object_search_field.value else ""
        if object_query:
            all_items = [item for item in all_items if object_query in (getattr(item, 'description', '') or "").lower()]
        
        self.shifts_list_view.controls.clear()
        
        if not all_items:
            self.shifts_list_view.controls.append(ft.Text(self._get_no_shifts_text(), size=16, color=ft.Colors.GREY))
        else:
            start = self.shifts_page * self.shifts_page_size
            end = start + self.shifts_page_size
            page_items = all_items[start:end]
            
            for item in page_items:
                self.shifts_list_view.controls.append(self._create_shift_list_item(item))
        
        total_pages = (len(all_items) + self.shifts_page_size - 1) // self.shifts_page_size if all_items else 1
        self.shifts_page_text.value = f"Страница {self.shifts_page + 1} из {total_pages}"
        
        if self.page:
            self.page.update()
    
    def prev_shifts_page(self):
        """Предыдущая страница смен"""
        if self.shifts_page > 0:
            self.shifts_page -= 1
            self.update_shifts_list()
    
    def next_shifts_page(self):
        """Следующая страница смен"""
        # Получаем отфильтрованные элементы
        all_items = []
        if self.show_shifts_cb.value:
            all_items.extend([item for item in self.all_shifts if not (hasattr(item, 'description') and item.description and "ВЗН" in item.description)])
        if self.show_vzn_cb.value:
            all_items.extend([item for item in self.all_shifts if hasattr(item, 'description') and item.description and "ВЗН" in item.description])
        
        employee_query = self.employee_search_field.value.lower() if self.employee_search_field.value else ""
        if employee_query:
            all_items = [item for item in all_items if employee_query in item.employee.full_name.lower()]
        
        object_query = self.object_search_field.value.lower() if self.object_search_field.value else ""
        if object_query:
            all_items = [item for item in all_items if object_query in (item.description or "").lower()]
        
        total_pages = (len(all_items) + self.shifts_page_size - 1) // self.shifts_page_size
        if self.shifts_page < total_pages - 1:
            self.shifts_page += 1
            self.update_shifts_list()
    
    def search_objects(self, query):
        """Поиск объектов"""
        if not query or len(query) < 2:
            self.object_search_results.visible = False
            if self.page:
                self.page.update()
            return
        
        def operation():
            from database.models import Object
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
        if self.page:
            self.page.update()
    
    def select_object(self, obj):
        """Выбор объекта"""
        self.object_search.value = obj.name
        self.object_search_results.visible = False
        self.selected_object = obj
        self.load_object_rates(obj)
        if self.page:
            self.page.update()
    
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
        else:
            self.rate_dropdown.visible = False
    
    def on_rate_change(self, rate_id):
        """Обработчик смены ставки"""
        if rate_id:
            self.selected_rate_id = int(rate_id)
    
    def render(self):
        """Возвращает интерфейс календаря"""
        # Добавляем диалоги в overlay
        if self.shifts_dialog not in self.page.overlay:
            self.page.overlay.append(self.shifts_dialog)
        if self.add_shift_dialog not in self.page.overlay:
            self.page.overlay.append(self.add_shift_dialog)
        if self.add_vzn_dialog not in self.page.overlay:
            self.page.overlay.append(self.add_vzn_dialog)
        
        return ft.Column([
            ft.Text(self._get_calendar_title(), size=24, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: self.change_month(-1)),
                self.current_month_display,
                ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: self.change_month(1))
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.calendar_grid_container
        ], spacing=10, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER), self.shifts_dialog
    
    # Абстрактные методы для переопределения в дочерних классах
    @abstractmethod
    def _get_month_data(self, first_day, last_day):
        """Возвращает данные для месяца"""
        pass
    
    @abstractmethod
    def _get_shifts_for_date(self, date_obj):
        """Возвращает смены для даты"""
        pass
    
    @abstractmethod
    def _create_shift_list_item(self, shift):
        """Создает элемент списка смены"""
        pass
    
    @abstractmethod
    def save_new_shift(self):
        """Сохраняет новую смену"""
        pass
    
    @abstractmethod
    def save_vzn(self):
        """Сохраняет новую ВЗН"""
        pass
    
    # Методы для переопределения в дочерних классах
    def _get_day_count_color(self):
        """Возвращает цвет для отображения количества"""
        return ft.Colors.BLUE
    
    def _get_shifts_dialog_title(self):
        """Возвращает заголовок диалога смен"""
        return "Смены"
    
    def _get_add_shift_button_text(self):
        """Возвращает текст кнопки добавления смены"""
        return "Добавить смену"
    
    def _get_add_vzn_button_text(self):
        """Возвращает текст кнопки добавления ВЗН"""
        return "Добавить ВЗН"
    
    def _get_add_shift_dialog_title(self):
        """Возвращает заголовок диалога добавления смены"""
        return "Добавить смену"
    
    def _get_add_vzn_dialog_title(self):
        """Возвращает заголовок диалога добавления ВЗН"""
        return "Добавить ВЗН"
    
    def _get_no_shifts_text(self):
        """Возвращает текст отсутствия смен"""
        return "На эту дату смен нет"
    
    # Абстрактный метод - должен быть переопределен в дочерних классах
    @abstractmethod
    def _get_calendar_title(self):
        """Возвращает заголовок календаря"""
        pass