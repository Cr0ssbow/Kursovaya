from base.base_calendar import BaseCalendar

class ShiftsCalendar(BaseCalendar):
    """Календарь смен, наследующийся от базового класса"""
    
    def _get_calendar_title(self):
        """Возвращает заголовок календаря"""
        return "Календарь смен"

# Функция-обертка для совместимости
def shifts_calendar_page(page: ft.Page = None):
    calendar_instance = ShiftsCalendar(page)
    return calendar_instance.render()