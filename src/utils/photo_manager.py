import os
import shutil
from pathlib import Path

class PhotoManager:
    """Класс для управления фотографиями сотрудников"""
    
    def __init__(self):
        self.base_path = Path("storage/data/photos")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Создает необходимые директории если их нет"""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_employee_folder(self, employee_name: str) -> Path:
        """Возвращает путь к папке сотрудника"""
        # Очищаем имя от недопустимых символов для имени папки
        safe_name = "".join(c for c in employee_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return self.base_path / safe_name
    
    def create_employee_folder(self, employee_name: str) -> Path:
        """Создает папку для сотрудника"""
        folder_path = self.get_employee_folder(employee_name)
        folder_path.mkdir(exist_ok=True)
        return folder_path
    
    def save_photo(self, employee_name: str, source_path: str) -> str:
        """Сохраняет фотографию сотрудника"""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Файл {source_path} не найден")
        
        employee_folder = self.create_employee_folder(employee_name)
        
        # Получаем расширение файла
        file_extension = Path(source_path).suffix.lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.bmp', '.pdf']:
            raise ValueError("Поддерживаются файлы: JPG, PNG, BMP, PDF")
        
        # Создаем имя файла
        photo_filename = f"photo{file_extension}"
        photo_path = employee_folder / photo_filename
        
        # Копируем файл
        shutil.copy2(source_path, photo_path)
        
        return str(photo_path)
    
    def get_photo_path(self, employee_name: str) -> str:
        """Возвращает путь к фотографии сотрудника"""
        employee_folder = self.get_employee_folder(employee_name)
        
        # Ищем фото с разными расширениями
        for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.pdf']:
            photo_path = employee_folder / f"photo{ext}"
            if photo_path.exists():
                return str(photo_path)
        
        return None
    
    def delete_photo(self, employee_name: str):
        """Удаляет фотографию сотрудника"""
        photo_path = self.get_photo_path(employee_name)
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
    
    def delete_employee_folder(self, employee_name: str):
        """Удаляет папку сотрудника"""
        employee_folder = self.get_employee_folder(employee_name)
        if employee_folder.exists():
            shutil.rmtree(employee_folder)
    
    def get_photo_widget(self, employee_name: str, open_pdf_callback=None):
        """Возвращает виджет с фотографией сотрудника"""
        import flet as ft
        
        photo_path = self.get_photo_path(employee_name)
        if photo_path:
            if photo_path.lower().endswith('.pdf'):
                return ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, size=50, color=ft.Colors.RED),
                        ft.Text("PDF", size=12),
                        ft.ElevatedButton("Открыть", on_click=lambda e: open_pdf_callback(photo_path) if open_pdf_callback else None, height=30)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                    width=150,
                    height=150,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=ft.border_radius.all(10),
                    alignment=ft.alignment.center
                )
            else:
                import base64
                try:
                    with open(photo_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    widget = ft.Image(
                        src_base64=img_data,
                        width=150,
                        height=150,
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.all(10)
                    )
                    return widget
                except Exception as e:
                    pass
        
        return ft.Container(
            content=ft.Icon(ft.Icons.PERSON, size=75),
            width=150,
            height=150,
            bgcolor=ft.Colors.GREY_300,
            border_radius=ft.border_radius.all(10),
            alignment=ft.alignment.center
        )