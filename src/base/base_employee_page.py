import flet as ft
from abc import abstractmethod
from datetime import datetime
from base.base_page import BasePage
from utils.photo_manager import PhotoManager
import os

class BaseEmployeePage(BasePage):
    """Базовый класс для страниц управления сотрудниками"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.employees_table = None
        self.add_dialog = None
        self.detail_dialog = None
        self.show_nord = True
        self.show_legion = True
        self.photo_manager = PhotoManager()
        self._init_components()
    
    def _init_components(self):
        """Инициализация компонентов"""
        self._create_dialogs()
        self._create_table()
        self._create_pagination()
    
    def _create_dialogs(self):
        """Создает диалоги"""
        self.add_dialog = ft.AlertDialog(modal=True)
        self.detail_dialog = ft.AlertDialog(modal=True)
        self.edit_dialog = ft.AlertDialog(modal=True)
        self.termination_dialog = ft.AlertDialog(modal=True)
        self._create_form_fields()
        self._create_edit_fields()
        self._create_termination_fields()
    
    def _create_pagination(self):
        """Создает элементы пагинации"""
        self.prev_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.prev_page)
        self.next_btn = ft.IconButton(icon=ft.Icons.ARROW_FORWARD, on_click=self.next_page)
        self.page_info = ft.Text("Страница 1 из 1")
    
    def refresh_table(self):
        """Обновляет данные в таблице"""
        def operation():
            query = self._get_base_query()
            query = self._apply_search_filter(query)
            
            employees_list = list(query.order_by(self._get_order_field()))
            
            # Пагинация
            start_idx = self.current_page * self.page_size
            end_idx = start_idx + self.page_size
            page_employees = employees_list[start_idx:end_idx]
            
            self.employees_table.rows.clear()
            for employee in page_employees:
                self.employees_table.rows.append(self._create_table_row(employee))
            
            # Обновляем кнопки пагинации
            total_pages = (len(employees_list) + self.page_size - 1) // self.page_size
            self.prev_btn.disabled = self.current_page == 0
            self.next_btn.disabled = self.current_page >= total_pages - 1
            self.page_info.value = f"Страница {self.current_page + 1} из {max(1, total_pages)}"
            
            return True
        
        self.safe_db_operation(operation)
    
    def show_detail_dialog(self, employee):
        """Показывает диалог с детальной информацией"""
        self.current_detail_employee = employee
        self.detail_page_index = 0
        self.detail_pages = self._get_detail_pages(employee)
        
        self._update_detail_dialog()
    
    def _get_detail_pages(self, employee):
        """Возвращает список страниц для диалога"""
        # По умолчанию одна страница - основная информация
        return [{
            'title': 'Основная информация',
            'content': self._get_detail_content(employee)
        }]
    
    def _update_detail_dialog(self):
        """Обновляет содержимое диалога"""
        employee = self.current_detail_employee
        self.detail_pages = self._get_detail_pages(employee)
        current_page = self.detail_pages[self.detail_page_index]
        
        # Кнопки навигации
        prev_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self.navigate_detail_page(-1),
            disabled=self.detail_page_index == 0
        )
        next_btn = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=lambda e: self.navigate_detail_page(1),
            disabled=self.detail_page_index >= len(self.detail_pages) - 1
        )
        
        # Индикатор страниц
        page_indicator = ft.Text(f"{self.detail_page_index + 1} / {len(self.detail_pages)}", size=12)
        
        self.detail_dialog.title = ft.Column([
            ft.Row([
                prev_btn,
                ft.Text(f"{self._get_detail_title()}: {employee.full_name}", expand=True),
                next_btn
            ]),
            ft.Row([
                ft.Text(current_page['title'], weight="bold", expand=True),
                page_indicator
            ])
        ], spacing=5)
        
        self.detail_dialog.content = ft.Column(current_page['content'], spacing=10, height=800, width=1300)
        # Получаем кнопки действий для диалога
        self.detail_dialog.actions = self._get_detail_actions(employee)
        
        if not self.detail_dialog.open:
            self.detail_dialog.open = True
            if self.page and self.detail_dialog not in self.page.overlay:
                self.page.overlay.append(self.detail_dialog)
        
        if self.page:
            self.page.update()
    
    def navigate_detail_page(self, direction):
        """Навигация между страницами диалога"""
        new_index = self.detail_page_index + direction
        if 0 <= new_index < len(self.detail_pages):
            self.detail_page_index = new_index
            self._update_detail_dialog()
    
    def _get_detail_actions(self, employee):
        """Возвращает кнопки действий для диалога"""
        return [
            ft.TextButton("Изменить фотографию", on_click=lambda e, emp=employee: self.change_photo(emp)),
            ft.TextButton("Редактировать", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_edit_dialog(emp))),
            ft.TextButton("Уволить", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_termination_dialog(emp)), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Закрыть", on_click=lambda e: self.close_detail_dialog())
        ]
    
    def close_detail_dialog(self):
        """Закрывает диалог детальной информации"""
        self.detail_dialog.open = False
        if self.page:
            self.page.update()
    
    def show_add_dialog(self, e):
        """Показывает диалог добавления"""
        self.add_dialog.title = ft.Text(self._get_add_title())
        self.add_dialog.content = ft.Column(self._get_form_fields(), spacing=10)
        self.add_dialog.actions = [
            ft.TextButton("Сохранить", on_click=self.save_employee),
            ft.TextButton("Отмена", on_click=self.close_add_dialog),
        ]
        self.add_dialog.open = True
        if self.page and self.add_dialog not in self.page.overlay:
            self.page.overlay.append(self.add_dialog)
        if self.page:
            self.page.update()
    
    def close_add_dialog(self, e):
        """Закрывает диалог добавления"""
        self.add_dialog.open = False
        if self.page:
            self.page.update()
    
    def save_employee(self, e):
        """Сохраняет нового сотрудника"""
        try:
            result = self.safe_db_operation(self._save_operation)
            if result:
                self.close_add_dialog(e)
                self.refresh_table()
                self.show_snackbar(self._get_success_message())
        except ValueError as ex:
            self.show_snackbar(str(ex), True)
    
    def show_edit_dialog(self, employee):
        """Показывает диалог редактирования"""
        self.current_employee = employee
        self._populate_edit_fields(employee)
        self.edit_dialog.title = ft.Text(f"Редактировать {self._get_employee_type()}")
        self.edit_dialog.content = ft.Column(self._get_edit_fields(), spacing=10)
        self.edit_dialog.actions = [
            ft.TextButton("Сохранить", on_click=self.save_edit_employee),
            ft.TextButton("Отмена", on_click=self.close_edit_dialog),
        ]
        self.edit_dialog.open = True
        if self.page and self.edit_dialog not in self.page.overlay:
            self.page.overlay.append(self.edit_dialog)
        if self.page:
            self.page.update()
    
    def close_edit_dialog(self, e=None):
        """Закрывает диалог редактирования"""
        self.edit_dialog.open = False
        if self.page:
            self.page.update()
    
    def save_edit_employee(self, e):
        """Сохраняет изменения сотрудника"""
        try:
            result = self.safe_db_operation(self._save_edit_operation)
            if result:
                self.close_edit_dialog(e)
                self.refresh_table()
                self.show_snackbar("Изменения сохранены!")
        except ValueError as ex:
            self.show_snackbar(str(ex), True)
    
    def _create_termination_fields(self):
        """Создает поля для увольнения"""
        self.termination_date_field = ft.TextField(label="Дата увольнения (дд.мм.гггг)", width=200, on_change=self.format_date_input, max_length=10)
        self.termination_reason_field = ft.TextField(label="Причина увольнения (необязательно)", width=300, multiline=True)
    
    def show_termination_dialog(self, employee):
        """Показывает диалог увольнения"""
        self.current_employee = employee
        
        # Устанавливаем текущую дату по умолчанию
        from datetime import date
        today = date.today()
        self.termination_date_field.value = today.strftime("%d.%m.%Y")
        self.termination_reason_field.value = ""
        
        self.termination_dialog.title = ft.Text(f"Уволить {self._get_employee_type()}: {employee.full_name}")
        self.termination_dialog.content = ft.Column([
            self.termination_date_field,
            self.termination_reason_field
        ], spacing=10)
        self.termination_dialog.actions = [
            ft.TextButton("Уволить", on_click=self.terminate_employee, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Отмена", on_click=self.close_termination_dialog),
        ]
        self.termination_dialog.open = True
        if self.page and self.termination_dialog not in self.page.overlay:
            self.page.overlay.append(self.termination_dialog)
        if self.page:
            self.page.update()
    
    def close_termination_dialog(self, e=None):
        """Закрывает диалог увольнения"""
        self.termination_dialog.open = False
        if self.page:
            self.page.update()
    
    def terminate_employee(self, e):
        """Увольняет сотрудника"""
        def operation():
            termination_date_value = self.termination_date_field.value.strip()
            termination_reason_value = self.termination_reason_field.value.strip()
            
            if not termination_date_value:
                raise ValueError("Дата увольнения обязательна!")
            
            from datetime import datetime
            termination_date = datetime.strptime(termination_date_value, "%d.%m.%Y").date()
            
            self.current_employee.termination_date = termination_date
            self.current_employee.termination_reason = termination_reason_value or None
            self.current_employee.save()
            return True
        
        try:
            result = self.safe_db_operation(operation)
            if result:
                self.close_termination_dialog(e)
                self.refresh_table()
                self.show_snackbar(f"{self._get_employee_type().capitalize()} уволен!")
        except ValueError as ex:
            self.show_snackbar(str(ex), True)
    
    def on_search_change(self, e):
        """Обработчик изменения поиска"""
        self.search_value = e.control.value.strip()
        self.current_page = 0
        self.refresh_table()
        if self.page:
            self.page.update()
    
    def prev_page(self, e):
        """Предыдущая страница"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()
            if self.page:
                self.page.update()
    
    def next_page(self, e):
        """Следующая страница"""
        self.current_page += 1
        self.refresh_table()
        if self.page:
            self.page.update()
    
    def on_company_filter_change(self, e):
        """Обработчик изменения фильтра по компании"""
        self.current_page = 0
        self.refresh_table()
        if self.page:
            self.page.update()
    

    
    def get_photo_widget(self, employee_name: str) -> ft.Control:
        """Возвращает виджет с фотографией сотрудника"""
        widget = self.photo_manager.get_photo_widget(employee_name, self.open_pdf)
        if hasattr(widget, 'src_base64'):
            self.current_photo_widget = widget
        return widget
    
    def open_pdf(self, pdf_path):
        """Открывает PDF файл в системном приложении"""
        import os
        import subprocess
        import platform
        
        try:
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path])
        except Exception as e:
            self.show_snackbar(f"Ошибка открытия PDF: {e}", True)
    
    def get_employee_folder_type(self):
        """Возвращает тип папки для сотрудника"""
        # Переопределяется в дочерних классах
        return "Сотрудник охраны"
    
    def save_personal_card(self, employee, file_path):
        """Сохраняет личную карточку в правильную структуру папок"""
        from database.models import PersonalCard
        from datetime import date
        import shutil
        from pathlib import Path
        from PIL import Image
        
        # Создаем структуру папок
        safe_name = "".join(c for c in employee.full_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        folder_type = self.get_employee_folder_type()
        cards_folder = Path(f"storage/data/{folder_type}/{safe_name}/карточки")
        cards_folder.mkdir(parents=True, exist_ok=True)
        
        source_file = Path(file_path)
        card_count = PersonalCard.select().where(
            (PersonalCard.guard_employee == employee) if hasattr(PersonalCard, 'guard_employee') else
            (PersonalCard.chief_employee == employee) if hasattr(PersonalCard, 'chief_employee') else
            False
        ).count() + 1
        
        # Конвертируем JPG в PNG
        if source_file.suffix.lower() in ['.jpg', '.jpeg']:
            dest_file = cards_folder / f"card_{card_count}.png"
            try:
                with Image.open(source_file) as img:
                    img.save(dest_file, 'PNG')
            except:
                # Если конвертация не удалась, копируем как есть
                dest_file = cards_folder / f"card_{card_count}{source_file.suffix}"
                shutil.copy2(source_file, dest_file)
        else:
            dest_file = cards_folder / f"card_{card_count}{source_file.suffix}"
            shutil.copy2(source_file, dest_file)
        
        # Создаем запись в БД
        if hasattr(PersonalCard, 'guard_employee') and hasattr(employee, 'guard_rank'):
            PersonalCard.create(guard_employee=employee, issue_date=date.today(), photo_path=str(dest_file))
        elif hasattr(PersonalCard, 'chief_employee') and hasattr(employee, 'position'):
            PersonalCard.create(chief_employee=employee, issue_date=date.today(), photo_path=str(dest_file))
        
        return str(dest_file)
    
    def change_photo(self, employee, photo_name=None, callback=None):
        """Изменение фотографии сотрудника"""
        def on_result(e: ft.FilePickerResultEvent):
            if e.files:
                try:
                    name = photo_name or employee.full_name
                    photo_path = self.photo_manager.save_photo(name, e.files[0].path)
                    
                    if callback:
                        callback(photo_path)
                    else:
                        employee.photo_path = photo_path
                        employee.save()
                    
                    self.show_snackbar("Фотография обновлена!")
                    # Обновляем изображение через src_base64
                    if hasattr(self, 'current_photo_widget') and self.current_photo_widget:
                        try:
                            import base64
                            with open(photo_path, "rb") as f:
                                img_data = base64.b64encode(f.read()).decode()
                            self.current_photo_widget.src_base64 = img_data
                            self.current_photo_widget.update()
                        except:
                            pass
                except Exception as ex:
                    self.show_snackbar(f"Ошибка сохранения фото: {ex}", True)
        
        file_picker = ft.FilePicker(on_result=on_result)
        if self.page and file_picker not in self.page.overlay:
            self.page.overlay.append(file_picker)
            self.page.update()
        file_picker.pick_files(
            dialog_title="Выберите фотографию или PDF",
            allowed_extensions=["jpg", "jpeg", "png", "bmp", "pdf"]
        )
    
    def render(self) -> ft.Column:
        """Возвращает интерфейс страницы"""
        self.refresh_table()
        
        # Создаем галочки для фильтрации
        nord_checkbox = ft.Checkbox(label="Норд", value=self.show_nord, on_change=lambda e: (setattr(self, 'show_nord', e.control.value), self.on_company_filter_change(e)))
        legion_checkbox = ft.Checkbox(label="Легион", value=self.show_legion, on_change=lambda e: (setattr(self, 'show_legion', e.control.value), self.on_company_filter_change(e)))
        
        search_row = self._get_search_row()
        search_row.controls.extend([nord_checkbox, legion_checkbox])
        
        return ft.Column([
            ft.Row([
                ft.Text(self._get_page_title(), size=24, weight="bold"),
                ft.ElevatedButton(self._get_add_button_text(), icon=ft.Icons.ADD, on_click=self.show_add_dialog),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            search_row,
            ft.Container(
                content=ft.Column([self.employees_table], scroll=ft.ScrollMode.AUTO),
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10,
                expand=True,
            ),
            ft.Row([self.prev_btn, self.page_info, self.next_btn], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=10, expand=True)
    
    def _get_search_row(self):
        """Возвращает строку с поиском (можно переопределить в дочерних классах)"""
        return ft.Row([
            ft.TextField(label="Поиск по ФИО", width=300, on_change=self.on_search_change, autofocus=False, dense=True),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
    
    # Абстрактные методы для переопределения в дочерних классах
    @abstractmethod
    def _create_form_fields(self):
        """Создает поля формы"""
        pass
    
    @abstractmethod
    def _create_table(self):
        """Создает таблицу"""
        pass
    
    @abstractmethod
    def _get_base_query(self):
        """Возвращает базовый запрос"""
        pass
    
    def _apply_search_filter(self, query):
        """Применяет фильтр поиска"""
        if self.search_value:
            query = self._apply_name_filter(query)
        
        # Применяем фильтр по компаниям
        companies = []
        if self.show_nord:
            companies.append("Норд")
        if self.show_legion:
            companies.append("Легион")
        
        # Применяем фильтр только если выбрана не вся компания
        if len(companies) == 1:
            query = self._apply_company_filter(query, companies)
        elif len(companies) == 0:
            # Если ни одна компания не выбрана, ничего не показываем
            query = query.where(False)
        
        return query
    
    @abstractmethod
    def _apply_name_filter(self, query):
        """Применяет фильтр по имени"""
        pass
    
    @abstractmethod
    def _apply_company_filter(self, query, companies):
        """Применяет фильтр по компании"""
        pass
    
    @abstractmethod
    def _get_order_field(self):
        """Возвращает поле для сортировки"""
        pass
    
    @abstractmethod
    def _create_table_row(self, employee):
        """Создает строку таблицы"""
        pass
    
    @abstractmethod
    def _get_detail_title(self):
        """Возвращает заголовок диалога деталей"""
        pass
    
    @abstractmethod
    def _get_detail_content(self, employee):
        """Возвращает содержимое диалога деталей"""
        pass
    
    @abstractmethod
    def _get_add_title(self):
        """Возвращает заголовок диалога добавления"""
        pass
    
    @abstractmethod
    def _get_form_fields(self):
        """Возвращает поля формы"""
        pass
    
    @abstractmethod
    def _save_operation(self):
        """Операция сохранения"""
        pass
    
    @abstractmethod
    def _get_success_message(self):
        """Возвращает сообщение об успехе"""
        pass
    
    @abstractmethod
    def _get_page_title(self):
        """Возвращает заголовок страницы"""
        pass
    
    @abstractmethod
    def _get_add_button_text(self):
        """Возвращает текст кнопки добавления"""
        pass
    
    @abstractmethod
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        pass
    
    @abstractmethod
    def _get_edit_fields(self):
        """Возвращает поля редактирования"""
        pass
    
    @abstractmethod
    def _populate_edit_fields(self, employee):
        """Заполняет поля редактирования"""
        pass
    
    @abstractmethod
    def _save_edit_operation(self):
        """Операция сохранения изменений"""
        pass
    
    @abstractmethod
    def _get_employee_type(self):
        """Возвращает тип сотрудника"""
        pass
    

    

    

    

    

    
