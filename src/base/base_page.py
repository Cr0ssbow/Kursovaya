import flet as ft
from abc import ABC, abstractmethod
from database.models import db
from datetime import datetime

class BasePage(ABC):
    """Базовый класс для всех страниц приложения"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page = 0
        self.page_size = 13
        self.search_value = ""
        
    def format_date(self, date):
        """Форматирует дату в строку дд.мм.гггг"""
        return date.strftime("%d.%m.%Y") if date else "Не указано"
    
    def format_date_input(self, e):
        """Автоматически форматирует ввод даты"""
        value = e.control.value.replace(".", "")
        if len(value) == 8 and value.isdigit():
            day = int(value[:2])
            month = int(value[2:4])
            year = int(value[4:])
            
            if day > 31:
                day = 31
            if month > 12:
                month = 12
            if year > 2100:
                year = 2100
                
            formatted = f"{day:02d}.{month:02d}.{year}"
            e.control.value = formatted
            if self.page:
                self.page.update()
    
    def safe_db_operation(self, operation):
        """Безопасное выполнение операций с БД"""
        try:
            if db.is_closed():
                db.connect()
            return operation()
        except UnicodeDecodeError as ex:
            print(f"Ошибка кодировки БД: {ex}")
            return []
        except Exception as ex:
            print(f"Ошибка БД: {ex}")
            return None
        finally:
            if not db.is_closed():
                db.close()
    
    def show_snackbar(self, message, is_error=False):
        """Показывает уведомление"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if is_error else ft.Colors.GREEN,
            duration=3000
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    @abstractmethod
    def render(self) -> ft.Column:
        """Возвращает интерфейс страницы"""
        pass