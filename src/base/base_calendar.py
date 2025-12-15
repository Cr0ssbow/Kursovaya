import flet as ft
from abc import abstractmethod
from datetime import datetime, date, timedelta
from base.base_page import BasePage
import calendar
from peewee import fn

class BaseCalendar(BasePage):
    """Базовый класс для календарей"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.current_date = date.today()
        self.selected_date = None
        self.calendar_container = None
        self.dialog = None
        self._init_components()
    
    def _init_components(self):
        """Инициализация компонентов календаря"""
        self.calendar_container = ft.Container(expand=True)
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(""),
            content=ft.Text(""),
            actions=[ft.TextButton("Закрыть", on_click=self._close_dialog)]
        )
        self._shifts_cache = {}
        self._create_calendar()
    
    def _create_calendar(self):
        """Создает календарь"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Сбрасываем кеш при смене месяца
        self._shifts_cache = {}
        
        # Заголовок с навигацией
        header = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self._prev_month
            ),
            ft.Text(
                self._get_month_name(month, year),
                size=20,
                weight="bold",
                expand=True,
                text_align=ft.TextAlign.CENTER
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                on_click=self._next_month
            )
        ])
        
        # Дни недели
        weekdays = ft.Row([
            ft.Container(
                content=ft.Text(day, weight="bold", text_align=ft.TextAlign.CENTER),
                width=100,
                height=30,
                alignment=ft.alignment.center
            )
            for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        ])
        
        # Дни месяца
        cal = calendar.monthcalendar(year, month)
        days_grid = ft.Column([
            ft.Row([
                self._create_day_cell(day if day != 0 else None, year, month)
                for day in week
            ])
            for week in cal
        ])
        
        self.calendar_container.content = ft.Column([
            header,
            weekdays,
            days_grid
        ])
    
    def _create_day_cell(self, day, year, month):
        """Создает ячейку дня"""
        if day is None:
            return ft.Container(width=100, height=80)
        
        cell_date = date(year, month, day)
        is_today = cell_date == date.today()
        
        # Получаем данные для этого дня
        day_data = self._get_day_data(cell_date)
        
        # Создаем содержимое ячейки
        cell_content = self._create_day_content(day, cell_date, day_data, is_today)
        
        return ft.Container(
            content=cell_content,
            width=100,
            height=80,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            bgcolor=ft.Colors.BLUE_50 if is_today else None,
            on_click=lambda e, d=cell_date: self._on_day_click(d)
        )
    
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
    
    def _on_day_click(self, selected_date):
        """Обработчик клика по дню"""
        self.selected_date = selected_date
        self._show_day_dialog(selected_date)
    
    def _show_day_dialog(self, selected_date):
        """Показывает диалог для выбранного дня"""
        self.dialog.title = ft.Text(f"События на {selected_date.strftime('%d.%m.%Y')}")
        self.dialog.content = ft.Container(
            content=self._get_day_dialog_content(selected_date),
            width=600,
            height=400
        )
        self.dialog.actions = [
            ft.TextButton("Закрыть", on_click=self._close_dialog)
        ]
        
        if self.dialog not in self.page.overlay:
            self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()
    
    def _close_dialog(self, e=None):
        """Закрывает диалог"""
        self.dialog.open = False
        self.page.update()
    
    def _get_month_name(self, month, year):
        """Возвращает название месяца (переопределяется в дочерних классах)"""
        return f"{calendar.month_name[month]} {year}"
    
    def _get_shifts_count_for_date(self, date_obj):
        """Получает количество смен для даты с кешированием"""
        if not self._shifts_cache:
            self._load_shifts_cache()
        return self._shifts_cache.get(date_obj, 0)
    
    def _load_shifts_cache(self):
        """Загружает кеш смен для месяца (переопределяется в дочерних классах)"""
        pass
    
    def render(self):
        """Возвращает интерфейс календаря"""
        return ft.Column([
            ft.Text(self._get_calendar_title(), size=24, weight="bold"),
            ft.Divider(),
            self.calendar_container
        ], expand=True), self.dialog
    
    # Абстрактные методы для переопределения в дочерних классах
    @abstractmethod
    def _get_day_data(self, date):
        """Возвращает данные для конкретного дня"""
        pass
    
    @abstractmethod
    def _get_day_dialog_content(self, date):
        """Возвращает содержимое диалога для дня"""
        pass
    
    @abstractmethod
    def _get_calendar_title(self):
        """Возвращает заголовок календаря"""
        pass