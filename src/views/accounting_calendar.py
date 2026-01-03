from base.base_calendar import BaseCalendar
from database.models import Assignment, DutyShift, CashWithdrawal, GuardEmployee, Object
from peewee import fn
import flet as ft

class AccountingCalendarPage(BaseCalendar):
    """Календарь бухгалтерии"""
    
    def _get_calendar_title(self):
        return "Календарь бухгалтерии"
    
    def _get_shifts_dialog_title(self):
        return "Смены"
    
    def _get_add_shift_dialog_title(self):
        return "Добавить операцию"
    
    def _get_add_vzn_dialog_title(self):
        return "Добавить ВЗН операцию"
    
    def _get_no_shifts_text(self):
        return "На эту дату смен нет"
    
    def _get_day_count_color(self):
        return ft.Colors.GREEN
    
    def _get_month_data(self, first_day, last_day):
        """Возвращает данные для месяца"""
        cache = {}
        
        # Проходим по каждому дню месяца
        current_date = first_day
        while current_date <= last_day:
            # Получаем объединенные смены для даты
            merged_shifts = self._get_shifts_for_date(current_date)
            cache[current_date] = len(merged_shifts)
            
            # Переходим к следующему дню
            from datetime import timedelta
            current_date += timedelta(days=1)
        
        return cache
    
    def _get_shifts_for_date(self, date_obj):
        """Возвращает смены для даты"""
        # Получаем смены начальников охраны
        assignments = list(Assignment.select().join(GuardEmployee).switch(Assignment).join(Object).where(Assignment.date == date_obj))
        
        # Получаем смены дежурной части
        duty_shifts = list(DutyShift.select().join(GuardEmployee).where(DutyShift.date == date_obj))
        
        # Получаем ВЗН
        vzn_records = list(CashWithdrawal.select().join(GuardEmployee).switch(CashWithdrawal).join(Object).where(CashWithdrawal.date == date_obj))
        
        # Объединяем смены по сотрудникам
        merged_shifts = {}
        
        # Добавляем смены начальников
        for assignment in assignments:
            key = assignment.employee.id
            merged_shifts[key] = assignment
        
        # Добавляем смены дежурной части (если нет смены начальника)
        for duty in duty_shifts:
            key = duty.employee.id
            if key not in merged_shifts:
                merged_shifts[key] = duty
        
        # Добавляем ВЗН (если нет других смен)
        for vzn in vzn_records:
            key = vzn.employee.id
            if key not in merged_shifts:
                merged_shifts[key] = vzn
        
        return list(merged_shifts.values())
    
    def _create_shift_list_item(self, shift):
        """Создает элемент списка смены"""
        # Определяем тип смены
        if isinstance(shift, Assignment):
            shift_type = "Начальник охраны"
            icon = ft.Icons.SUPERVISOR_ACCOUNT
            color = ft.Colors.BLUE
            object_name = shift.object.name if hasattr(shift, 'object') and shift.object else "Нет объекта"
        elif isinstance(shift, DutyShift):
            if shift.description and "ВЗН" in shift.description:
                shift_type = "ВЗН (дежурная)"
                icon = ft.Icons.ATTACH_MONEY
                color = ft.Colors.PURPLE
            else:
                shift_type = "Дежурная часть"
                icon = ft.Icons.SECURITY
                color = ft.Colors.BLUE
            object_name = "Из описания" if shift.description else "Нет объекта"
        else:  # CashWithdrawal
            shift_type = "ВЗН (начальник)"
            icon = ft.Icons.ATTACH_MONEY
            color = ft.Colors.PURPLE
            object_name = shift.object.name if hasattr(shift, 'object') and shift.object else "Нет объекта"
        
        # Проверяем конфликты для этого сотрудника
        conflicts = self._get_shift_conflicts(shift)
        has_conflict = len(conflicts) > 0
        
        # Если есть конфликт, показываем только конфликт и объект
        if has_conflict:
            color = ft.Colors.RED
            subtitle_text = f"Конфликт | Объект: {object_name}"
        else:
            subtitle_text = f"{shift_type} | Объект: {object_name} | Часы: {shift.hours} | Ставка: {shift.hourly_rate}₽"
        
        return ft.ListTile(
            leading=ft.Icon(icon, color=color),
            title=ft.Text(shift.employee.full_name, weight="bold"),
            subtitle=ft.Text(subtitle_text),
            on_click=lambda e: self._show_shift_details(shift)
        )
    
    def _check_shift_conflict(self, shift):
        """Проверяет конфликт между сменами"""
        # Получаем все смены для этого сотрудника на эту дату
        employee_id = shift.employee.id
        date = shift.date
        
        # Получаем смены начальника охраны
        chief_shifts = list(Assignment.select().where(
            (Assignment.employee_id == employee_id) & (Assignment.date == date)
        ))
        
        # Получаем смены дежурной части
        duty_shifts = list(DutyShift.select().where(
            (DutyShift.employee_id == employee_id) & (DutyShift.date == date)
        ))
        
        # Получаем ВЗН
        vzn_records = list(CashWithdrawal.select().where(
            (CashWithdrawal.employee_id == employee_id) & (CashWithdrawal.date == date)
        ))
        
        # Проверяем наличие конфликтов (больше одной смены в одном календаре)
        if len(chief_shifts) > 1 or len(duty_shifts) > 1 or len(vzn_records) > 1:
            return True
        
        return False
    
    def save_new_shift(self):
        """Календарь бухгалтерии только отображает данные"""
        pass
    
    def save_vzn(self):
        """Календарь бухгалтерии только отображает данные"""
        pass
    
    def _get_add_shift_button_text(self):
        return None
    
    def _get_add_vzn_button_text(self):
        return None
    
    def _show_shift_details(self, shift):
        """Показывает детали смены"""
        # Определяем тип смены
        if isinstance(shift, Assignment):
            shift_type = "Начальник охраны"
            object_info = f"Объект: {shift.object.name}" if hasattr(shift, 'object') and shift.object else "Объект: не указан"
        elif isinstance(shift, DutyShift):
            shift_type = "Дежурная часть"
            object_info = f"Описание: {shift.description}" if shift.description else "Описание: нет"
        else:  # CashWithdrawal
            shift_type = "ВЗН"
            object_info = f"Объект: {shift.object.name}" if hasattr(shift, 'object') and shift.object else "Объект: не указан"
        
        # Проверяем конфликты
        conflicts = self._get_shift_conflicts(shift)
        
        content = [
            ft.Text(f"Тип: {shift_type}", size=16, weight="bold"),
            ft.Text(f"Сотрудник: {shift.employee.full_name}"),
            ft.Text(f"Дата: {shift.date.strftime('%d.%m.%Y')}"),
            ft.Text(f"Часы: {shift.hours}"),
            ft.Text(f"Ставка: {shift.hourly_rate}₽"),
            ft.Text(object_info),
            ft.Divider()
        ]
        
        if conflicts:
            content.append(ft.Text("Обнаружены конфликты:", size=16, weight="bold", color=ft.Colors.RED))
            for conflict in conflicts:
                content.append(ft.Text(f"• {conflict}", color=ft.Colors.RED))
        else:
            content.append(ft.Text("Конфликтов не обнаружено", color=ft.Colors.GREEN))
        
        details_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Детали смены"),
            content=ft.Column(content, height=400, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Закрыть", on_click=lambda e: self._close_details_dialog(details_dialog))]
        )
        
        self.page.overlay.append(details_dialog)
        details_dialog.open = True
        self.page.update()
    
    def _close_details_dialog(self, dialog):
        """Закрывает диалог деталей"""
        dialog.open = False
        self.page.update()
    
    def _get_shift_conflicts(self, shift):
        """Возвращает список конфликтов"""
        conflicts = []
        employee_id = shift.employee.id
        date = shift.date
        
        # Получаем все смены этого сотрудника на эту дату
        chief_shifts = list(Assignment.select().where(
            (Assignment.employee_id == employee_id) & (Assignment.date == date)
        ))
        
        duty_shifts = list(DutyShift.select().where(
            (DutyShift.employee_id == employee_id) & (DutyShift.date == date)
        ))
        
        vzn_records = list(CashWithdrawal.select().where(
            (CashWithdrawal.employee_id == employee_id) & (CashWithdrawal.date == date)
        ))
        
        # Проверяем соответствие между календарями
        if chief_shifts and duty_shifts:
            for chief_shift in chief_shifts:
                for duty_shift in duty_shifts:
                    if chief_shift.hours != duty_shift.hours:
                        conflicts.append(f"Несоответствие часов: {chief_shift.hours} (начальник) против {duty_shift.hours} (дежурная)")
                    
                    if abs(float(chief_shift.hourly_rate) - float(duty_shift.hourly_rate)) > 0.01:
                        conflicts.append(f"Несоответствие ставок: {chief_shift.hourly_rate}₽ (начальник) против {duty_shift.hourly_rate}₽ (дежурная)")
        
        # Проверяем дублирование смен (только если в одном календаре больше одной смены)
        if len(chief_shifts) > 1:
            conflicts.append(f"Несколько смен начальника охраны: {len(chief_shifts)}")
        if len(duty_shifts) > 1:
            conflicts.append(f"Несколько смен дежурной части: {len(duty_shifts)}")
        if len(vzn_records) > 1:
            conflicts.append(f"Несколько ВЗН: {len(vzn_records)}")
        
        return conflicts
    
    def update_shifts_list(self):
        """Обновляет список смен с пагинацией"""
        # Фильтрация по типу
        all_items = []
        if self.show_shifts_cb.value:
            # Обычные смены (начальники охраны и дежурная часть без ВЗН)
            for item in self.all_shifts:
                if isinstance(item, Assignment):
                    all_items.append(item)
                elif isinstance(item, DutyShift) and not (hasattr(item, 'description') and item.description and "ВЗН" in item.description):
                    all_items.append(item)
        
        if self.show_vzn_cb.value:
            # ВЗН (из обоих календарей)
            for item in self.all_shifts:
                if isinstance(item, CashWithdrawal):
                    all_items.append(item)
                elif isinstance(item, DutyShift) and hasattr(item, 'description') and item.description and "ВЗН" in item.description:
                    all_items.append(item)
        
        # Поиск по сотруднику
        employee_query = self.employee_search_field.value.lower() if self.employee_search_field.value else ""
        if employee_query:
            all_items = [item for item in all_items if employee_query in item.employee.full_name.lower()]
        
        # Поиск по объекту
        object_query = self.object_search_field.value.lower() if self.object_search_field.value else ""
        if object_query:
            filtered_items = []
            for item in all_items:
                if hasattr(item, 'object') and item.object and object_query in item.object.name.lower():
                    filtered_items.append(item)
                elif hasattr(item, 'description') and item.description and object_query in item.description.lower():
                    filtered_items.append(item)
            all_items = filtered_items
        
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

def accounting_calendar_page(page=None):
    calendar_instance = AccountingCalendarPage(page)
    content, dialog = calendar_instance.render()
    return content, dialog