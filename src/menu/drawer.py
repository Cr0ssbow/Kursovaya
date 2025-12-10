import flet as ft
from peewee import *

def drawer(on_change_handler, auth_manager=None):
    """Создаёт navigation drawer с обработчиком событий и проверкой доступа"""
    
    # Все пункты меню с их названиями страниц
    menu_items = [
        ("home", "Домашняя страница", ft.Icons.HOME, ft.Icons.HOME_OUTLINED),
        ("settings", "Настройки", ft.Icons.SETTINGS, ft.Icons.SETTINGS_OUTLINED),
        ("employees", "Сотрудники охраны", ft.Icons.SECURITY, ft.Icons.SECURITY_OUTLINED),
        ("chief_employees", "Начальники охраны", ft.Icons.SUPERVISOR_ACCOUNT, ft.Icons.SUPERVISOR_ACCOUNT_OUTLINED),
        ("office_employees", "Сотрудники офиса", ft.Icons.WORK, ft.Icons.WORK_OUTLINED),
        ("objects", "Объекты", ft.Icons.BUSINESS, ft.Icons.BUSINESS_OUTLINED),
        ("calendar", "Календарь смен", ft.Icons.SCHEDULE, ft.Icons.SCHEDULE_OUTLINED),
        ("statistics", "Статистика", ft.Icons.BAR_CHART, ft.Icons.BAR_CHART_OUTLINED),
        ("notes", "Заметки", ft.Icons.NOTE, ft.Icons.NOTE_OUTLINED),
        ("terminated", "Уволенные сотрудники", ft.Icons.PERSON_OFF, ft.Icons.PERSON_OFF_OUTLINED),
        ("discarded_cards", "Списанные карточки", ft.Icons.CREDIT_CARD_OFF, ft.Icons.CREDIT_CARD_OFF_OUTLINED),
        ("administration", "Администрирование", ft.Icons.ADMIN_PANEL_SETTINGS, ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED),
        ("logs", "Логи действий", ft.Icons.HISTORY, ft.Icons.HISTORY_OUTLINED)
    ]
    
    # Фильтруем пункты меню по доступу
    allowed_items = []
    for page_name, label, icon, selected_icon in menu_items:
        if not auth_manager or auth_manager.has_page_access(page_name):
            allowed_items.append((page_name, label, icon, selected_icon))
    
    # Сохраняем маппинг как атрибут функции
    on_change_handler.page_mapping = {i: page_name for i, (page_name, _, _, _) in enumerate(allowed_items)}
    
    controls = [ft.Container(height=12)]
    
    for i, (page_name, label, icon, selected_icon) in enumerate(allowed_items):
        # Добавляем разделитель перед настройками и администрированием
        if page_name == "settings" or page_name == "administration":
            controls.append(ft.Divider(thickness=2))
            
        controls.append(
            ft.NavigationDrawerDestination(
                label=label,
                icon=icon,
                selected_icon=selected_icon,
            )
        )
    
    return ft.NavigationDrawer(
        on_change=on_change_handler,
        controls=controls,
    )
