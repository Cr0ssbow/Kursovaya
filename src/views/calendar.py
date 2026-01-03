import flet as ft
import datetime
from database.models import Assignment, Employee, Object, ChiefEmployee, ChiefObjectAssignment, CashWithdrawal, db
from peewee import *
from views.settings import load_cell_shape_from_db
from base.base_calendar import BaseCalendar

# Словарь русских названий месяцев
RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

class CalendarPage(BaseCalendar):
    """Страница календаря смен"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.current_assignment = None
        self.current_vzn = None
        self._init_calendar_specific_components()
    
    def _get_calendar_title(self):
        return "Календарь начальника охраны"
    
    def _get_shifts_dialog_title(self):
        return "Смены на дату"
    
    def _get_add_shift_dialog_title(self):
        return "Добавить смену"
    
    def _get_no_shifts_text(self):
        return "На эту дату смен и ВЗН нет"
    
    def _get_day_count_color(self):
        return ft.Colors.BLUE
    
    def _get_month_data(self, first_day, last_day):
        """Возвращает данные для месяца"""
        # Подсчитываем обычные смены
        assignments = Assignment.select(Assignment.date, fn.COUNT(Assignment.id).alias('count')).where(
            (Assignment.date >= first_day) & (Assignment.date <= last_day)
        ).group_by(Assignment.date)
        
        # Подсчитываем ВЗН
        vzn_records = CashWithdrawal.select(CashWithdrawal.date, fn.COUNT(CashWithdrawal.id).alias('count')).where(
            (CashWithdrawal.date >= first_day) & (CashWithdrawal.date <= last_day)
        ).group_by(CashWithdrawal.date)
        
        cache = {}
        # Добавляем обычные смены
        for assignment in assignments:
            cache[assignment.date] = assignment.count
        
        # Добавляем ВЗН к общему количеству
        for vzn in vzn_records:
            cache[vzn.date] = cache.get(vzn.date, 0) + vzn.count
        
        return cache
    
    def _get_shifts_for_date(self, date_obj):
        """Возвращает смены для даты"""
        assignments = Assignment.select().join(Employee).switch(Assignment).join(Object).where(Assignment.date == date_obj)
        vzn_records = CashWithdrawal.select().join(Employee).where(CashWithdrawal.date == date_obj)
        return list(assignments), list(vzn_records)
    
    def _create_shift_list_item(self, shift):
        """Создает элемент списка смены"""
        # Этот метод не используется, так как переопределен update_shifts_list
        pass
    
    def _init_calendar_specific_components(self):
        """Инициализация специфичных компонентов"""
        self._create_calendar_dialogs()
        self._create_calendar_form_fields()
        self.load_chiefs()
    
    def _create_calendar_dialogs(self):
        """Создает диалоги"""
        self.shifts_list_view = ft.ListView(expand=True, spacing=5, height=500)
        self.shifts_page_text = ft.Text("Страница 1")
        
        # Контролы поиска и фильтрации
        self.show_assignments_cb = ft.Checkbox(label="Обычные смены", value=True, on_change=lambda e: self.update_shifts_list())
        self.show_vzn_cb = ft.Checkbox(label="ВЗН", value=True, on_change=lambda e: self.update_shifts_list())
        self.employee_search_field = ft.TextField(label="Поиск по сотруднику", width=200, on_change=lambda e: self.reset_page_and_update())
        self.object_search_field = ft.TextField(label="Поиск по объекту", width=200, on_change=lambda e: self.reset_page_and_update())
        
        self.shifts_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Смены на дату"),
            content=ft.Column([
                ft.Row([
                    self.show_assignments_cb,
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
                ft.TextButton("Добавить смену", on_click=lambda e: self.open_add_shift_dialog()),
                ft.TextButton("Добавить ВЗН", on_click=lambda e: self.open_add_vzn_dialog()),
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
        
        self.add_vzn_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Добавить ВЗН"),
            content=ft.Column([], height=300, width=300, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Сохранить", on_click=lambda e: self.save_vzn()),
                ft.TextButton("Отмена", on_click=lambda e: self.close_add_vzn_dialog())
            ]
        )
        
        self.edit_vzn_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактирование ВЗН"),
            content=ft.Column([], height=300, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Сохранить", on_click=lambda e: self.save_vzn_changes()),
                ft.TextButton("Удалить", on_click=lambda e: self.delete_vzn_from_edit(), style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Отмена", on_click=lambda e: self.close_vzn_edit_dialog())
            ]
        )
    
    def _create_calendar_form_fields(self):
        """Создает поля форм"""
        # Поля редактирования смены
        self.absent_checkbox = ft.Checkbox(label="Пропуск", on_change=lambda e: self.toggle_absent_comment())
        self.absent_comment_field = ft.TextField(label="Комментарий к пропуску", visible=False, multiline=True)
        self.deduction_checkbox = ft.Checkbox(label="Удержание", on_change=lambda e: self.toggle_deduction_field())
        self.deduction_amount_field = ft.TextField(label="Сумма удержания", visible=False)
        self.bonus_amount_field = ft.TextField(label="Сумма премии", on_change=lambda e: self.toggle_bonus_comment())
        self.bonus_comment_field = ft.TextField(label="Комментарий к премии", visible=False, multiline=True)
        self.comment_field = ft.TextField(label="Комментарий", multiline=True)
        
        # Поля добавления смены
        self.chief_display = ft.Text("Начальник: не назначен", size=16)
        self.selected_chief_id = None
        
        # Поле для выбора адреса
        self.address_dropdown = ft.Dropdown(label="Выберите адрес", width=500, visible=False)
        self.selected_address_id = None
        
        # Поля для ВЗН (аналогично сменам)
        self.vzn_employee_search = ft.TextField(label="Поиск сотрудника", width=300, on_change=lambda e: self.search_vzn_employees(e.control.value))
        self.vzn_search_results = ft.Column(visible=False)
        self.vzn_object_search = ft.TextField(label="Поиск объекта", width=300, on_change=lambda e: self.search_vzn_objects(e.control.value))
        self.vzn_object_search_results = ft.Column(visible=False)
        self.vzn_chief_display = ft.Text("Начальник: не назначен", size=16)
        self.vzn_selected_chief_id = None
        self.vzn_hours_dropdown = ft.Dropdown(label="Количество часов", options=[ft.dropdown.Option("12"), ft.dropdown.Option("24")], value="12", width=200)
        self.vzn_address_dropdown = ft.Dropdown(label="Выберите адрес", width=500, visible=False)
        self.vzn_rate_dropdown = ft.Dropdown(label="Выберите ставку", width=500, visible=False)
        self.vzn_selected_object = None
        self.vzn_selected_address_id = None
        self.vzn_selected_rate_id = None
        self.vzn_comment_field = ft.TextField(label="Комментарий", multiline=True, width=500)
        
        # Поля для редактирования ВЗН
        self.vzn_absent_checkbox = ft.Checkbox(label="Пропуск", on_change=lambda e: self.toggle_vzn_absent_comment())
        self.vzn_absent_comment_field = ft.TextField(label="Комментарий к пропуску", visible=False, multiline=True)
        self.vzn_deduction_checkbox = ft.Checkbox(label="Удержание", on_change=lambda e: self.toggle_vzn_deduction_field())
        self.vzn_deduction_amount_field = ft.TextField(label="Сумма удержания", visible=False)
        self.vzn_bonus_amount_field = ft.TextField(label="Сумма премии", on_change=lambda e: self.toggle_vzn_bonus_comment())
        self.vzn_bonus_comment_field = ft.TextField(label="Комментарий к премии", visible=False, multiline=True)
        self.vzn_comment_edit = ft.TextField(label="Комментарий", multiline=True)
        self.current_vzn = None
        
        self.load_chiefs()
    
    def close_shifts_dialog(self):
        try:
            self.shifts_dialog.open = False
            self.page.update()
        except:
            pass
    
    def open_add_shift_dialog(self):
        self.setup_add_shift_form()
        self.page.dialog = self.add_shift_dialog
        self.add_shift_dialog.open = True
        self.page.update()
    
    def close_add_shift_dialog(self):
        try:
            self.add_shift_dialog.open = False
            self.page.dialog = self.shifts_dialog
            self.page.update()
        except:
            pass
    
    def open_add_vzn_dialog(self):
        self.setup_add_vzn_form()
        self.page.dialog = self.add_vzn_dialog
        self.add_vzn_dialog.open = True
        self.page.update()
    
    def close_add_vzn_dialog(self):
        try:
            self.add_vzn_dialog.open = False
            self.page.dialog = self.shifts_dialog
            self.page.update()
        except:
            pass
    
    def close_edit_dialog(self):
        try:
            self.edit_dialog.open = False
            self.page.update()
        except:
            pass
    
    def confirm_delete_shift(self):
        self.page.dialog = self.delete_confirm_dialog
        self.delete_confirm_dialog.open = True
        self.page.update()
    
    def close_delete_confirm(self):
        try:
            self.delete_confirm_dialog.open = False
            self.page.dialog = self.edit_dialog
            self.page.update()
        except:
            pass
    
    def delete_shift(self):
        if self.current_assignment:
            def operation():
                self.current_assignment.delete_instance()
                return True
            
            if self.safe_db_operation(operation):
                # Обновляем кеш для удаленной даты
                if hasattr(self, '_shifts_cache') and self.current_shift_date in self._shifts_cache:
                    self._shifts_cache[self.current_shift_date] = max(0, self._shifts_cache[self.current_shift_date] - 1)
                
                try:
                    self.delete_confirm_dialog.open = False
                    self.edit_dialog.open = False
                    self.update_calendar()
                    self.show_shifts_for_date(self.current_shift_date)
                except:
                    pass
    
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
    
    def toggle_vzn_absent_comment(self):
        self.vzn_absent_comment_field.visible = self.vzn_absent_checkbox.value
        self.update_vzn_bonus_fields_visibility()
        if self.page:
            self.page.update()
    
    def toggle_vzn_deduction_field(self):
        self.vzn_deduction_amount_field.visible = self.vzn_deduction_checkbox.value
        self.update_vzn_bonus_fields_visibility()
        if self.page:
            self.page.update()
    
    def update_vzn_bonus_fields_visibility(self):
        show_bonus = not self.vzn_absent_checkbox.value and not self.vzn_deduction_checkbox.value
        self.vzn_bonus_amount_field.visible = show_bonus
        self.vzn_bonus_comment_field.visible = show_bonus
    
    def toggle_vzn_bonus_comment(self):
        self.vzn_bonus_comment_field.visible = not self.vzn_absent_checkbox.value
        if self.page:
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
        self.comment_field.value = assignment.comment or ""
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
            self.bonus_comment_field,
            self.comment_field
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
                self.current_assignment.comment = self.comment_field.value or None
                self.current_assignment.save()
                return True
            
            if self.safe_db_operation(operation):
                self.close_edit_dialog()
                self.update_calendar()
                self.show_shifts_for_date(self.current_shift_date)
    
    def show_shifts_for_date(self, date_obj):
        self.current_shift_date = date_obj
        self.shifts_page = 0
        
        # Открываем диалог сразу с заглушкой
        self.shifts_dialog.title.value = f"Смены на {date_obj.strftime('%d.%m.%Y')}"
        self.shifts_list_view.controls.clear()
        self.shifts_list_view.controls.append(ft.Text("Загрузка...", size=16))
        self.shifts_page_text.value = "Страница 1"
        
        self.page.dialog = self.shifts_dialog
        self.shifts_dialog.open = True
        self.page.update()
        
        # Загружаем данные асинхронно
        def operation():
            assignments = Assignment.select().join(Employee).switch(Assignment).join(Object).where(Assignment.date == date_obj)
            vzn_records = CashWithdrawal.select().join(Employee).where(CashWithdrawal.date == date_obj)
            return list(assignments), list(vzn_records)
        
        result = self.safe_db_operation(operation)
        self.all_assignments = result[0] if result else []
        self.all_vzn_records = result[1] if result else []
        
        self.update_shifts_list()
    
    def reset_page_and_update(self):
        """Сбрасывает на первую страницу и обновляет список"""
        self.shifts_page = 0
        self.update_shifts_list()
    
    def update_shifts_list(self):
        """Обновляет список смен с пагинацией"""
        # Фильтрация по типу
        all_items = []
        if self.show_assignments_cb.value:
            all_items.extend(self.all_assignments)
        if self.show_vzn_cb.value:
            all_items.extend(self.all_vzn_records)
        
        # Поиск по сотруднику
        employee_query = self.employee_search_field.value.lower() if self.employee_search_field.value else ""
        if employee_query:
            all_items = [item for item in all_items if employee_query in item.employee.full_name.lower()]
        
        # Поиск по объекту
        object_query = self.object_search_field.value.lower() if self.object_search_field.value else ""
        if object_query:
            all_items = [item for item in all_items if object_query in item.object.name.lower()]
        
        self.shifts_list_view.controls.clear()
        
        if not all_items:
            self.shifts_list_view.controls.append(ft.Text("На эту дату смен и ВЗН нет", size=16, color=ft.Colors.GREY))
        else:
            start = self.shifts_page * self.shifts_page_size
            end = start + self.shifts_page_size
            page_items = all_items[start:end]
            
            for item in page_items:
                if isinstance(item, Assignment):
                    self.add_assignment_card(item)
                else:  # CashWithdrawal
                    self.add_vzn_card(item)
        
        total_pages = (len(all_items) + self.shifts_page_size - 1) // self.shifts_page_size if all_items else 1
        self.shifts_page_text.value = f"Страница {self.shifts_page + 1} из {total_pages}"
        
        self.page.update()
    
    def add_assignment_card(self, assignment):
        """Добавляет элемент смены"""
        subtitle_parts = [f"Объект: {assignment.object.name}", f"Часы: {assignment.hours}"]
        
        if assignment.is_absent:
            subtitle_parts.append("Пропуск")
        if float(assignment.bonus_amount) > 0:
            subtitle_parts.append(f"Премия: {assignment.bonus_amount} ₽")
        if float(assignment.deduction_amount) > 0:
            subtitle_parts.append(f"Удержание: {assignment.deduction_amount} ₽")
        
        self.shifts_list_view.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.WORK),
                title=ft.Text(assignment.employee.full_name, weight="bold"),
                subtitle=ft.Text(" | ".join(subtitle_parts)),
                trailing=ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e, a=assignment: self.edit_shift(a))
            )
        )
    
    def add_vzn_card(self, vzn):
        """Добавляет элемент ВЗН"""
        subtitle_parts = [f"Объект: {vzn.object.name}", f"Часы: {vzn.hours}", "ВЗН"]
        
        if vzn.is_absent:
            subtitle_parts.append("Пропуск")
        if float(vzn.bonus_amount) > 0:
            subtitle_parts.append(f"Премия: {vzn.bonus_amount} ₽")
        if float(vzn.deduction_amount) > 0:
            subtitle_parts.append(f"Удержание: {vzn.deduction_amount} ₽")
        
        self.shifts_list_view.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ATTACH_MONEY, color=ft.Colors.PURPLE),
                title=ft.Text(vzn.employee.full_name, weight="bold"),
                subtitle=ft.Text(" | ".join(subtitle_parts)),
                trailing=ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e, vzn_record=vzn: self.edit_vzn(vzn_record))
            )
        )
    
    def prev_shifts_page(self):
        """Предыдущая страница смен"""
        if self.shifts_page > 0:
            self.shifts_page -= 1
            self.update_shifts_list()
    
    def next_shifts_page(self):
        """Следующая страница смен"""
        all_items = self.all_assignments + self.all_vzn_records
        total_pages = (len(all_items) + self.shifts_page_size - 1) // self.shifts_page_size
        if self.shifts_page < total_pages - 1:
            self.shifts_page += 1
            self.update_shifts_list()
    
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
            
            # Подсчитываем обычные смены
            assignments = Assignment.select(Assignment.date, fn.COUNT(Assignment.id).alias('count')).where(
                (Assignment.date >= first_day) & (Assignment.date <= last_day)
            ).group_by(Assignment.date)
            
            # Подсчитываем ВЗН
            vzn_records = CashWithdrawal.select(CashWithdrawal.date, fn.COUNT(CashWithdrawal.id).alias('count')).where(
                (CashWithdrawal.date >= first_day) & (CashWithdrawal.date <= last_day)
            ).group_by(CashWithdrawal.date)
            
            cache = {}
            # Добавляем обычные смены
            for assignment in assignments:
                cache[assignment.date] = assignment.count
            
            # Добавляем ВЗН к общему количеству
            for vzn in vzn_records:
                cache[vzn.date] = cache.get(vzn.date, 0) + vzn.count
            
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
            if self.page:
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
        if self.page:
            self.page.update()
    
    def select_employee(self, employee):
        self.employee_search.value = employee.full_name
        self.search_results.visible = False
        if self.page:
            self.page.update()
    
    def select_object(self, obj):
        super().select_object(obj)
        self.load_object_addresses(obj)
        self.auto_assign_chief(obj)
        if self.page:
            self.page.update()
    
    def get_object_address(self, obj):
        """Получает адрес объекта"""
        from database.models import ObjectAddress
        primary_addr = ObjectAddress.select().where(
            (ObjectAddress.object == obj) & (ObjectAddress.is_primary == True)
        ).first()
        if primary_addr:
            return primary_addr.address
        first_addr = ObjectAddress.select().where(ObjectAddress.object == obj).first()
        return first_addr.address if first_addr else "не указан"
    
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
    
    def on_address_change(self, address_id):
        """Обработчик смены адреса"""
        if address_id:
            self.selected_address_id = int(address_id)
    
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
        self.description_field.value = ""
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
            self.hours_dropdown,
            self.description_field
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
                hourly_rate=rate.rate,
                comment=self.description_field.value or None
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
    
    def search_vzn_employees(self, query):
        if not query or len(query) < 2:
            self.vzn_search_results.visible = False
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
        self.page.update()
    
    def select_vzn_employee(self, employee):
        self.vzn_employee_search.value = employee.full_name
        self.vzn_search_results.visible = False
        self.page.update()
    
    def search_vzn_objects(self, query):
        if not query or len(query) < 2:
            self.vzn_object_search_results.visible = False
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
        self.page.update()
    
    def select_vzn_object(self, obj):
        self.vzn_object_search.value = obj.name
        self.vzn_object_search_results.visible = False
        self.vzn_selected_object = obj
        self.load_vzn_object_addresses(obj)
        self.load_vzn_object_rates(obj)
        self.auto_assign_vzn_chief(obj)
        self.page.update()
    
    def load_vzn_object_addresses(self, obj):
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
    
    def load_vzn_object_rates(self, obj):
        def operation():
            from database.models import ObjectRate
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
            default_rate = next((rate for rate in rates if rate.is_default), rates[0] if rates else None)
            if default_rate:
                self.vzn_rate_dropdown.value = str(default_rate.id)
                self.vzn_selected_rate_id = default_rate.id
            self.vzn_rate_dropdown.visible = True
            self.vzn_rate_dropdown.on_change = lambda e: self.on_vzn_rate_change(e.control.value)
        else:
            self.vzn_rate_dropdown.visible = False
    
    def on_vzn_address_change(self, address_id):
        if address_id:
            self.vzn_selected_address_id = int(address_id)
    
    def on_vzn_rate_change(self, rate_id):
        if rate_id:
            self.vzn_selected_rate_id = int(rate_id)
    
    def auto_assign_vzn_chief(self, obj):
        def operation():
            assignment = ChiefObjectAssignment.select().where(ChiefObjectAssignment.object == obj).first()
            if assignment and assignment.chief.termination_date is None:
                return assignment.chief
            return None
        
        chief = self.safe_db_operation(operation)
        if chief:
            self.vzn_chief_display.value = f"Начальник: {chief.full_name}"
            self.vzn_selected_chief_id = chief.id
        else:
            self.vzn_chief_display.value = "Начальник: не назначен"
            self.vzn_selected_chief_id = None
    
    def setup_add_vzn_form(self):
        self.vzn_employee_search.value = ""
        self.vzn_object_search.value = ""
        self.vzn_selected_chief_id = None
        self.vzn_selected_object = None
        self.vzn_selected_address_id = None
        self.vzn_selected_rate_id = None
        self.vzn_hours_dropdown.value = "12"
        self.vzn_comment_field.value = ""
        self.vzn_search_results.visible = False
        self.vzn_object_search_results.visible = False
        self.vzn_address_dropdown.visible = False
        self.vzn_rate_dropdown.visible = False
        self.vzn_chief_display.value = "Начальник: не назначен"
        
        self.add_vzn_dialog.content.controls = [
            ft.Text(f"Дата: {self.current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            self.vzn_employee_search,
            self.vzn_search_results,
            self.vzn_object_search,
            self.vzn_object_search_results,
            self.vzn_address_dropdown,
            self.vzn_rate_dropdown,
            self.vzn_chief_display,
            self.vzn_hours_dropdown,
            self.vzn_comment_field
        ]
    
    def save_vzn(self):
        if not self.vzn_employee_search.value or not self.vzn_object_search.value or not self.vzn_hours_dropdown.value or not self.vzn_selected_rate_id:
            return
        
        def operation():
            from database.models import ObjectRate
            
            employee = Employee.get(Employee.full_name == self.vzn_employee_search.value)
            obj = Object.get(Object.name == self.vzn_object_search.value)
            rate = ObjectRate.get_by_id(self.vzn_selected_rate_id)
            
            chief = None
            if self.vzn_selected_chief_id:
                chief = ChiefEmployee.get_by_id(self.vzn_selected_chief_id)
            
            CashWithdrawal.create(
                employee=employee,
                object=obj,
                chief=chief,
                date=self.current_shift_date,
                hours=int(self.vzn_hours_dropdown.value),
                hourly_rate=rate.rate,
                comment=self.vzn_comment_field.value or None
            )
            return True
        
        if self.safe_db_operation(operation):
            self.close_add_vzn_dialog()
            self.show_shifts_for_date(self.current_shift_date)
    
    def delete_vzn(self, vzn_record):
        def operation():
            vzn_record.delete_instance()
            return True
        
        if self.safe_db_operation(operation):
            self.show_shifts_for_date(self.current_shift_date)
    
    def edit_vzn(self, vzn_record):
        self.current_vzn = vzn_record
        
        self.vzn_absent_checkbox.value = vzn_record.is_absent
        self.vzn_absent_comment_field.value = vzn_record.absent_comment or ""
        self.vzn_absent_comment_field.visible = vzn_record.is_absent
        
        self.vzn_deduction_checkbox.value = float(vzn_record.deduction_amount) > 0
        self.vzn_deduction_amount_field.value = str(float(vzn_record.deduction_amount))
        self.vzn_deduction_amount_field.visible = float(vzn_record.deduction_amount) > 0
        
        self.vzn_bonus_amount_field.value = str(float(vzn_record.bonus_amount))
        self.vzn_bonus_comment_field.value = vzn_record.bonus_comment or ""
        self.vzn_comment_edit.value = vzn_record.comment or ""
        self.update_vzn_bonus_fields_visibility()
        
        self.edit_vzn_dialog.content.controls = [
            ft.Text(f"Сотрудник: {vzn_record.employee.full_name}", weight="bold"),
            ft.Text(f"Объект: {vzn_record.object.name}"),
            ft.Text(f"Дата: {vzn_record.date.strftime('%d.%m.%Y')}"),
            ft.Divider(),
            self.vzn_absent_checkbox,
            self.vzn_absent_comment_field,
            self.vzn_deduction_checkbox,
            self.vzn_deduction_amount_field,
            self.vzn_bonus_amount_field,
            self.vzn_bonus_comment_field,
            self.vzn_comment_edit
        ]
        
        self.page.dialog = self.edit_vzn_dialog
        self.edit_vzn_dialog.open = True
        self.page.update()
    
    def save_vzn_changes(self):
        if self.current_vzn:
            def operation():
                self.current_vzn.is_absent = self.vzn_absent_checkbox.value
                self.current_vzn.absent_comment = self.vzn_absent_comment_field.value if self.vzn_absent_checkbox.value else None
                self.current_vzn.deduction_amount = float(self.vzn_deduction_amount_field.value or "0") if self.vzn_deduction_checkbox.value else 0
                self.current_vzn.bonus_amount = float(self.vzn_bonus_amount_field.value or "0") if not self.vzn_absent_checkbox.value else 0
                self.current_vzn.bonus_comment = self.vzn_bonus_comment_field.value if float(self.vzn_bonus_amount_field.value or "0") > 0 and not self.vzn_absent_checkbox.value else None
                self.current_vzn.comment = self.vzn_comment_edit.value or None
                self.current_vzn.save()
                return True
            
            if self.safe_db_operation(operation):
                self.close_vzn_edit_dialog()
                self.show_shifts_for_date(self.current_shift_date)
    
    def delete_vzn_from_edit(self):
        if self.current_vzn:
            def operation():
                self.current_vzn.delete_instance()
                return True
            
            if self.safe_db_operation(operation):
                self.close_vzn_edit_dialog()
                self.show_shifts_for_date(self.current_shift_date)
    
    def close_vzn_edit_dialog(self):
        try:
            self.edit_vzn_dialog.open = False
            self.page.update()
        except:
            pass
    
    def render(self) -> ft.Column:
        """Возвращает интерфейс страницы"""
        # Добавляем диалоги в overlay страницы
        if self.edit_dialog not in self.page.overlay:
            self.page.overlay.append(self.edit_dialog)
        if self.delete_confirm_dialog not in self.page.overlay:
            self.page.overlay.append(self.delete_confirm_dialog)
        if self.add_shift_dialog not in self.page.overlay:
            self.page.overlay.append(self.add_shift_dialog)
        if self.add_vzn_dialog not in self.page.overlay:
            self.page.overlay.append(self.add_vzn_dialog)
        if self.edit_vzn_dialog not in self.page.overlay:
            self.page.overlay.append(self.edit_vzn_dialog)
        
        return ft.Column([
            ft.Text("Календарь начальника охраны", size=24, weight="bold"),
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