import flet as ft
from datetime import date
from base.base_calendar import BaseCalendar
from database.models import Assignment, CashWithdrawal, GuardEmployee, Object, ChiefEmployee
from peewee import fn

class ShiftsCalendar(BaseCalendar):
    """Календарь смен, наследующийся от базового класса"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
    
    def _get_day_data(self, date_obj):
        """Возвращает количество смен для конкретного дня"""
        def operation():
            assignments_count = Assignment.select().where(Assignment.date == date_obj).count()
            vzn_count = CashWithdrawal.select().where(CashWithdrawal.date == date_obj).count()
            return assignments_count + vzn_count
        
        return self.safe_db_operation(operation) or 0
    
    def _get_day_dialog_content(self, selected_date):
        """Возвращает содержимое диалога для дня"""
        def operation():
            assignments = list(Assignment.select().join(GuardEmployee).switch(Assignment).join(Object).where(Assignment.date == selected_date))
            vzn_records = list(CashWithdrawal.select().join(GuardEmployee).switch(CashWithdrawal).join(Object).where(CashWithdrawal.date == selected_date))
            return assignments, vzn_records
        
        result = self.safe_db_operation(operation)
        assignments, vzn_records = result if result else ([], [])
        
        content = []
        
        if not assignments and not vzn_records:
            content.append(ft.Text("На эту дату смен нет", size=16, color=ft.Colors.GREY))
        else:
            # Обычные смены
            if assignments:
                content.append(ft.Text("Обычные смены:", size=18, weight="bold"))
                for assignment in assignments:
                    content.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.WORK),
                            title=ft.Text(assignment.employee.full_name),
                            subtitle=ft.Text(f"Объект: {assignment.object.name} | Часы: {assignment.hours}")
                        )
                    )
                content.append(ft.Divider())
            
            # ВЗН
            if vzn_records:
                content.append(ft.Text("ВЗН:", size=18, weight="bold"))
                for vzn in vzn_records:
                    content.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.ATTACH_MONEY, color=ft.Colors.PURPLE),
                            title=ft.Text(vzn.employee.full_name),
                            subtitle=ft.Text(f"Объект: {vzn.object.name} | Часы: {vzn.hours}")
                        )
                    )
        
        return ft.Column(content, scroll=ft.ScrollMode.AUTO)
    
    def _get_calendar_title(self):
        """Возвращает заголовок календаря"""
        return "Календарь смен"

# Функция-обертка для совместимости
def shifts_calendar_page(page: ft.Page = None):
    calendar_instance = ShiftsCalendar(page)
    return calendar_instance.render()