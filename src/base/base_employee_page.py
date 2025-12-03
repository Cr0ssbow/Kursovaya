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
        self.employees_list = None
        self.add_dialog = None
        self.detail_dialog = None
        self.photo_manager = PhotoManager()
        self.current_page = 0
        self.page_size = 9
        self.sort_ascending = True
        self.sort_by_name = True
        self._init_components()
    
    def _init_components(self):
        """Инициализация компонентов"""
        self._create_dialogs()
        self._create_list()
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
    
    def refresh_list(self):
        """Обновляет данные в списке"""
        def operation():
            query = self._get_base_query()
            query = self._apply_search_filter(query)
            
            all_employees = list(query)
            
            # Сортируем в Python
            if self.sort_by_name:
                all_employees.sort(key=lambda x: x.full_name.strip().lower(), reverse=not self.sort_ascending)
            else:
                # Сортировка по дополнительному полю (переопределяется в дочерних классах)
                all_employees.sort(key=self._get_sort_key, reverse=not self.sort_ascending)
            
            # Пагинация
            start_idx = self.current_page * self.page_size
            end_idx = start_idx + self.page_size
            page_employees = all_employees[start_idx:end_idx]
            
            self.employees_list.controls.clear()
            for employee in page_employees:
                self.employees_list.controls.append(self._create_list_item(employee))
            
            # Обновляем кнопки пагинации
            total_pages = (len(all_employees) + self.page_size - 1) // self.page_size
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
                self.refresh_list()
                self.show_snackbar(self._get_success_message())
        except ValueError as ex:
            self.show_snackbar(str(ex), True)
    
    def show_edit_dialog(self, employee):
        """Показывает диалог редактирования"""
        self.current_employee = employee
        self._populate_edit_fields(employee)
        self.edit_dialog.title = ft.Text(f"Редактировать {self._get_employee_type()}")
        self.edit_dialog.content = ft.Column(self._get_edit_fields(), spacing=15)
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
                self.refresh_list()
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
                self.refresh_list()
                self.show_snackbar(f"{self._get_employee_type().capitalize()} уволен!")
        except ValueError as ex:
            self.show_snackbar(str(ex), True)
    
    def on_search_change(self, e):
        """Обработчик изменения поиска"""
        self.search_value = e.control.value.strip()
        self.current_page = 0
        self.refresh_list()
        if self.page:
            self.page.update()
    
    def prev_page(self, e):
        """Предыдущая страница"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_list()
            if self.page:
                self.page.update()
    
    def next_page(self, e):
        """Следующая страница"""
        self.current_page += 1
        self.refresh_list()
        if self.page:
            self.page.update()
    
    def sort_by_name_click(self, e):
        """Сортировка по имени"""
        if self.sort_by_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_by_name = True
            self.sort_ascending = True
        self.current_page = 0
        self.refresh_list()
        if self.page:
            self.page.update()
    
    def sort_by_secondary_click(self, e):
        """Сортировка по дополнительному полю"""
        if not self.sort_by_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_by_name = False
            self.sort_ascending = True
        self.current_page = 0
        self.refresh_list()
        if self.page:
            self.page.update()
    
    def on_company_filter_change(self, e):
        """Обработчик изменения фильтра по компании"""
        self.current_page = 0
        self.refresh_list()
        if self.page:
            self.page.update()
    

    
    def get_photo_widget(self, employee_name: str) -> ft.Control:
        """Возвращает виджет с фотографией сотрудника"""
        # Всегда создаем новый виджет для корректного обновления
        return self.photo_manager.get_photo_widget(employee_name, self.open_pdf)
    
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
    
    def save_personal_card(self, employee, file_path, company):
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
                dest_file = cards_folder / f"card_{card_count}{source_file.suffix}"
                shutil.copy2(source_file, dest_file)
        else:
            dest_file = cards_folder / f"card_{card_count}{source_file.suffix}"
            shutil.copy2(source_file, dest_file)
        
        # Создаем запись в БД с компанией
        if hasattr(employee, 'guard_rank'):
            PersonalCard.create(guard_employee=employee, company=company, issue_date=date.today(), photo_path=str(dest_file))
        else:
            PersonalCard.create(chief_employee=employee, company=company, issue_date=date.today(), photo_path=str(dest_file))
        
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
                    
                    # Принудительно обновляем диалог
                    # Закрываем все открытые диалоги
                    for dialog in self.page.overlay[:]:
                        if hasattr(dialog, 'open') and dialog.open:
                            dialog.open = False
                    self.page.update()
                    # Открываем заново
                    self.show_basic_info_with_tabs(employee)
                    
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
    
    def create_company_filter_dropdown(self):
        """Создает dropdown с чекбоксами для фильтрации компаний"""
        from database.models import Company
        
        # Инициализируем фильтры для всех компаний
        companies = list(Company.select())
        for company in companies:
            attr_name = f"show_{company.name.lower().replace(' ', '_')}"
            if not hasattr(self, attr_name):
                setattr(self, attr_name, True)
        
        def update_company_filter(company_name, value):
            attr_name = f"show_{company_name.lower().replace(' ', '_')}"
            setattr(self, attr_name, value)
            self.on_company_filter_change(None)
            
            # Обновляем текст кнопки
            selected = []
            for company in companies:
                attr_name = f"show_{company.name.lower().replace(' ', '_')}"
                if getattr(self, attr_name, True):
                    selected.append(company.name)
            
            if len(selected) == len(companies):
                self.company_button.text = "Все компании"
            elif len(selected) == 0:
                self.company_button.text = "Нет компаний"
            else:
                self.company_button.text = f"Выбрано: {len(selected)}"
            self.page.update()
        
        # Создаем элементы меню
        menu_items = []
        for company in companies:
            attr_name = f"show_{company.name.lower().replace(' ', '_')}"
            
            def make_checkbox_handler(comp_name):
                def handler(e):
                    update_company_filter(comp_name, e.control.value)
                return handler
            
            checkbox = ft.Checkbox(
                label=company.name,
                value=getattr(self, attr_name, True),
                on_change=make_checkbox_handler(company.name)
            )
            
            menu_items.append(
                ft.PopupMenuItem(
                    content=checkbox,
                    on_click=lambda e, cb=checkbox: setattr(cb, 'value', not cb.value) or cb.on_change(type('Event', (), {'control': cb})())
                )
            )
        
        # Создаем кнопку с меню
        self.company_button = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Row([
                    ft.Text("Все ЧОПЫ", size=14),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=20)
                ], tight=True),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.all(1, ft.Colors.BLACK87),
                border_radius=8,
                width=180, 
                height=47,
            ),
            items=menu_items,
            tooltip="Фильтр по компаниям"
        )
        
        return self.company_button
    
    def create_edit_company_dropdown(self):
        """Создает dropdown с чекбоксами для редактирования компаний"""
        from database.models import Company
        
        companies = list(Company.select())
        
        def update_company_selection(company_name, value):
            for checkbox in self.edit_company_checkboxes:
                if checkbox.label == company_name:
                    checkbox.value = value
                    break
            
            selected = [cb.label for cb in self.edit_company_checkboxes if cb.value]
            
            if len(selected) == len(companies):
                self.edit_company_button.content.content.controls[0].value = "Все компании"
            elif len(selected) == 0:
                self.edit_company_button.content.content.controls[0].value = "Нет компаний"
            else:
                self.edit_company_button.content.content.controls[0].value = f"Выбрано: {len(selected)}"
            self.page.update()
        
        menu_items = []
        for company in companies:
            def make_checkbox_handler(comp_name):
                def handler(e):
                    update_company_selection(comp_name, e.control.value)
                return handler
            
            checkbox_value = False
            for checkbox in self.edit_company_checkboxes:
                if checkbox.label == company.name:
                    checkbox_value = checkbox.value
                    break
            
            checkbox = ft.Checkbox(
                label=company.name,
                value=checkbox_value,
                on_change=make_checkbox_handler(company.name)
            )
            
            menu_items.append(
                ft.PopupMenuItem(
                    content=checkbox,
                    on_click=lambda e, cb=checkbox: setattr(cb, 'value', not cb.value) or cb.on_change(type('Event', (), {'control': cb})())
                )
            )
        
        selected = [cb.label for cb in self.edit_company_checkboxes if cb.value]
        if len(selected) == len(companies):
            initial_text = "Все компании"
        elif len(selected) == 0:
            initial_text = "Нет компаний"
        else:
            initial_text = f"Выбрано: {len(selected)}"
        
        self.edit_company_button = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Row([
                    ft.Text(initial_text, size=14),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=20)
                ], tight=True),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.all(1, ft.Colors.BLACK87),
                border_radius=8,
                width=500, 
                height=47,
            ),
            items=menu_items,
            tooltip="Выбор компаний"
        )
        
        return self.edit_company_button
    
    def _create_company_checkboxes(self, first_checked=True):
        """Создает чекбоксы для компаний"""
        from database.models import Company
        checkboxes = []
        for i, company in enumerate(Company.select()):
            checkboxes.append(ft.Checkbox(
                label=company.name, 
                value=first_checked and i == 0
            ))
        return checkboxes
    
    def _create_list(self):
        """Создает список"""
        self.employees_list = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            height=500
        )
    
    def render(self) -> ft.Column:
        """Возвращает интерфейс страницы"""
        self.refresh_list()
        
        search_row = self._get_search_row()
        # Вставляем фильтр по компании перед кнопками сортировки
        company_filter = self.create_company_filter_dropdown()
        if len(search_row.controls) >= 2:
            search_row.controls.insert(-2, company_filter)
        else:
            search_row.controls.append(company_filter)
        
        return ft.Column([
            ft.Row([
                ft.Text(self._get_page_title(), size=24, weight="bold"),
                ft.ElevatedButton(self._get_add_button_text(), icon=ft.Icons.ADD, on_click=self.show_add_dialog),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            search_row,
            self.employees_list,
            ft.Row([self.prev_btn, self.page_info, self.next_btn], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=10, expand=True)
    
    def _get_search_row(self):
        """Возвращает строку с поиском (можно переопределить в дочерних классах)"""
        return ft.Row([
            ft.TextField(label="Поиск по ФИО", width=300, on_change=self.on_search_change, autofocus=False, dense=True),
            ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD if (self.sort_by_name and self.sort_ascending) else ft.Icons.ARROW_DOWNWARD if self.sort_by_name else ft.Icons.ABC,
                tooltip=f"По имени {'↑' if self.sort_ascending else '↓'}" if self.sort_by_name else "Сортировка по имени",
                on_click=self.sort_by_name_click
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD if (not self.sort_by_name and self.sort_ascending) else ft.Icons.ARROW_DOWNWARD if not self.sort_by_name else self._get_secondary_sort_icon(),
                tooltip=f"По {self._get_secondary_sort_name()} {'↑' if self.sort_ascending else '↓'}" if not self.sort_by_name else f"Сортировка по {self._get_secondary_sort_name()}",
                on_click=self.sort_by_secondary_click
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
    
    # Абстрактные методы для переопределения в дочерних классах
    @abstractmethod
    def _create_form_fields(self):
        """Создает поля формы"""
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
        from database.models import Company
        companies = []
        all_companies = list(Company.select())
        
        for company in all_companies:
            attr_name = f"show_{company.name.lower().replace(' ', '_')}"
            if getattr(self, attr_name, True):
                companies.append(company.name)
        
        # Применяем фильтр только если выбрана не вся компания
        if len(companies) < len(all_companies) and len(companies) > 0:
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
    def _create_list_item(self, employee):
        """Создает элемент списка"""
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
    
    def _get_sort_key(self, employee):
        """Возвращает ключ для сортировки по дополнительному полю (переопределяется в дочерних классах)"""
        return employee.full_name.lower()
    
    def _get_secondary_sort_icon(self):
        """Возвращает иконку для дополнительной сортировки (переопределяется в дочерних классах)"""
        return ft.Icons.SORT
    
    def _get_secondary_sort_name(self):
        """Возвращает название дополнительного поля сортировки (переопределяется в дочерних классах)"""
        return "полю"
    
    def show_basic_info_with_tabs(self, employee):
        """Показывает диалог с вкладками"""
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Основная информация",
                    content=ft.Column(self._get_detail_content(employee), scroll=ft.ScrollMode.AUTO)
                ),
                ft.Tab(
                    text="Личные карточки",
                    content=ft.Column([], scroll=ft.ScrollMode.AUTO)
                ),
                ft.Tab(
                    text="Документы",
                    content=ft.Column([], scroll=ft.ScrollMode.AUTO)
                )
            ],
            expand=True
        )
        
        tabs_dialog = ft.AlertDialog(
            title=ft.Text(f"Информация о сотруднике: {employee.full_name}"),
            content=tabs,
            actions=[
                ft.TextButton("Изменить фотографию", on_click=lambda e: self.change_photo(employee)),
                ft.TextButton("Редактировать", on_click=lambda e: self.show_edit_dialog(employee)),
                ft.TextButton("Уволить", on_click=lambda e: self.show_termination_dialog(employee), style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Закрыть", on_click=lambda e: setattr(tabs_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        
        # Сохраняем ссылку на tabs в диалоге
        tabs_dialog.tabs_ref = tabs
        
        def on_tab_change(e):
            if e.control.selected_index == 1:  # Карточки
                tabs.tabs[1].content = ft.Column(self._get_personal_cards_content(employee, tabs_dialog), scroll=ft.ScrollMode.AUTO)
            elif e.control.selected_index == 2:  # Документы
                tabs.tabs[2].content = ft.Column(self._get_documents_content(employee, tabs_dialog), scroll=ft.ScrollMode.AUTO)
            self.page.update()
        
        tabs.on_change = on_tab_change
        
        self.page.overlay.append(tabs_dialog)
        tabs_dialog.open = True
        self.page.update()
    
    def _get_personal_cards_content(self, employee, dialog_ref=None):
        """Возвращает содержимое страницы личных карточек"""
        from database.models import PersonalCard
        from datetime import date
        
        # Определяем тип сотрудника для правильного запроса
        if hasattr(employee, 'guard_rank'):
            cards = list(PersonalCard.select().where((PersonalCard.guard_employee == employee) & (PersonalCard.is_discarded == False)).order_by(PersonalCard.issue_date.desc()))
        else:
            cards = list(PersonalCard.select().where((PersonalCard.chief_employee == employee) & (PersonalCard.is_discarded == False)).order_by(PersonalCard.issue_date.desc()))
        
        # Форма добавления
        date_field = ft.TextField(
            label="Дата (дд.мм.гггг)",
            value=date.today().strftime("%d.%m.%Y"),
            width=150,
            on_change=self.format_date_input,
            max_length=10
        )
        
        from database.models import Company
        company_dropdown = ft.Dropdown(
            label="Компания",
            width=150,
            options=[ft.dropdown.Option(c.name) for c in Company.select()],
            value=Company.select().first().name if Company.select().exists() else None
        )
        
        selected_file_path = [None]
        file_button = ft.ElevatedButton("Выбрать файл", width=120)
        
        def on_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                selected_file_path[0] = e.files[0].path
                file_button.text = f"Файл: {e.files[0].name[:10]}..."
                self.page.update()
        
        def select_file(e):
            file_picker = ft.FilePicker(on_result=on_file_result)
            self.page.overlay.append(file_picker)
            self.page.update()
            file_picker.pick_files(
                dialog_title="Выберите фото карточки",
                allowed_extensions=["jpg", "jpeg", "png", "pdf"]
            )
        
        def save_card(e):
            try:
                if not selected_file_path[0]:
                    self.show_snackbar("Выберите файл!", True)
                    return
                
                if not company_dropdown.value:
                    self.show_snackbar("Выберите компанию!", True)
                    return
                
                from datetime import datetime
                date_value = date_field.value.strip()
                if not date_value:
                    self.show_snackbar("Дата обязательна!", True)
                    return
                
                issue_date = datetime.strptime(date_value, "%d.%m.%Y").date()
                from database.models import Company
                company = Company.get(Company.name == company_dropdown.value)
                saved_path = self.save_personal_card(employee, selected_file_path[0], company)
                
                # Очищаем форму
                date_field.value = date.today().strftime("%d.%m.%Y")
                company_dropdown.value = Company.select().first().name if Company.select().exists() else None
                selected_file_path[0] = None
                file_button.text = "Выбрать файл"
                
                if dialog_ref:
                    if hasattr(dialog_ref, 'tabs_ref'):
                        dialog_ref.tabs_ref.tabs[1].content = ft.Column(self._get_personal_cards_content(employee, dialog_ref), scroll=ft.ScrollMode.AUTO)
                    else:
                        dialog_ref.content.controls.clear()
                        new_content = self._get_personal_cards_content(employee, dialog_ref)
                        dialog_ref.content.controls.extend(new_content)
                        dialog_ref.content.update()
                    self.page.update()
            except Exception as ex:
                self.show_snackbar(f"Ошибка: {ex}", True)
        
        file_button.on_click = select_file
        
        add_form = ft.Column([
            ft.Text("Добавить карточку", weight="bold"),
            ft.Row([date_field, company_dropdown], spacing=10),
            ft.Row([file_button, ft.ElevatedButton("Сохранить", on_click=save_card, width=100)], spacing=10)
        ], spacing=5)
        
        cards_list = []
        if cards:
            for i, card in enumerate(cards):
                def make_view_handler(card_to_view):
                    return lambda e: self.view_personal_card(card_to_view)
                
                def make_delete_handler(card_to_delete):
                    return lambda e: self.delete_personal_card_simple(card_to_delete, employee, dialog_ref)
                
                cards_list.append(
                    ft.ListTile(
                        title=ft.Text(f"Карточка #{i+1} ({card.company.name})"),
                        subtitle=ft.Text(f"Дата: {self.format_date(card.issue_date)}"),
                        trailing=ft.Row([
                            ft.IconButton(ft.Icons.VISIBILITY, on_click=make_view_handler(card)),
                            ft.IconButton(ft.Icons.DELETE, on_click=make_delete_handler(card))
                        ], tight=True)
                    )
                )
        else:
            cards_list.append(ft.Text("Нет карточек", size=16, color=ft.Colors.GREY))
        
        return [
            ft.Text("Личные карточки", size=20, weight="bold"),
            add_form,
            ft.Column(cards_list, spacing=5, scroll=ft.ScrollMode.AUTO, height=450)
        ]
    
    def _get_documents_content(self, employee, dialog_ref=None):
        """Возвращает содержимое страницы документов"""
        from database.models import EmployeeDocument
        
        # Определяем тип сотрудника для правильного запроса
        if hasattr(employee, 'guard_rank'):
            docs = list(EmployeeDocument.select().where(EmployeeDocument.guard_employee == employee).order_by(EmployeeDocument.created_at.desc()))
        else:
            docs = list(EmployeeDocument.select().where(EmployeeDocument.chief_employee == employee).order_by(EmployeeDocument.created_at.desc()))
        
        # Форма добавления
        doc_name_field = ft.TextField(
            label="Название документа",
            width=200
        )
        
        selected_file_path = [None]
        file_button = ft.ElevatedButton("Выбрать файл", width=120)
        
        def on_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                selected_file_path[0] = e.files[0].path
                file_button.text = f"Файл: {e.files[0].name[:10]}..."
                self.page.update()
        
        def select_file(e):
            file_picker = ft.FilePicker(on_result=on_file_result)
            self.page.overlay.append(file_picker)
            self.page.update()
            file_picker.pick_files(
                dialog_title="Выберите документ",
                allowed_extensions=["jpg", "jpeg", "png", "pdf"]
            )
        
        def save_document(e):
            try:
                if not selected_file_path[0]:
                    self.show_snackbar("Выберите файл!", True)
                    return
                
                doc_name = doc_name_field.value.strip()
                if not doc_name:
                    self.show_snackbar("Название документа обязательно!", True)
                    return
                
                saved_path = self.save_document(employee, selected_file_path[0], doc_name)
                
                # Очищаем форму
                doc_name_field.value = ""
                selected_file_path[0] = None
                file_button.text = "Выбрать файл"
                
                if dialog_ref:
                    if hasattr(dialog_ref, 'tabs_ref'):
                        dialog_ref.tabs_ref.tabs[2].content = ft.Column(self._get_documents_content(employee, dialog_ref), scroll=ft.ScrollMode.AUTO)
                        self.page.update()
                    else:
                        dialog_ref.content.controls.clear()
                        new_content = self._get_documents_content(employee, dialog_ref)
                        dialog_ref.content.controls.extend(new_content)
                        dialog_ref.content.update()
                        self.page.update()
            except Exception as ex:
                self.show_snackbar(f"Ошибка: {ex}", True)
        
        file_button.on_click = select_file
        
        add_form = ft.Column([
            ft.Text("Добавить документ", weight="bold"),
            ft.Row([doc_name_field, file_button, ft.ElevatedButton("Сохранить", on_click=save_document, width=100)], spacing=10)
        ], spacing=5)
        
        docs_list = []
        if docs:
            for i, doc in enumerate(docs):
                def make_view_handler(doc_to_view):
                    return lambda e: self.view_document(doc_to_view)
                
                def make_delete_handler(doc_to_delete):
                    return lambda e: self.delete_document_simple(doc_to_delete, employee, dialog_ref)
                
                docs_list.append(
                    ft.ListTile(
                        title=ft.Text(doc.document_type),
                        subtitle=ft.Text(f"Добавлен: {doc.created_at.strftime('%d.%m.%Y')}"),
                        trailing=ft.Row([
                            ft.IconButton(ft.Icons.VISIBILITY, on_click=make_view_handler(doc)),
                            ft.IconButton(ft.Icons.DELETE, on_click=make_delete_handler(doc))
                        ], tight=True)
                    )
                )
        else:
            docs_list.append(ft.Text("Нет документов", size=16, color=ft.Colors.GREY))
        
        return [
            ft.Text("Документы", size=20, weight="bold"),
            add_form,
            ft.Column(docs_list, spacing=5, scroll=ft.ScrollMode.AUTO, height=450)
        ]
    
    def save_document(self, employee, file_path, doc_name):
        from database.models import EmployeeDocument
        import shutil
        from pathlib import Path
        from PIL import Image
        
        safe_name = "".join(c for c in employee.full_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        folder_type = self.get_employee_folder_type()
        docs_folder = Path(f"storage/data/{folder_type}/{safe_name}/документы")
        docs_folder.mkdir(parents=True, exist_ok=True)
        
        source_file = Path(file_path)
        
        # Определяем тип сотрудника для правильного подсчета
        if hasattr(employee, 'guard_rank'):
            doc_count = EmployeeDocument.select().where(EmployeeDocument.guard_employee == employee).count() + 1
        else:
            doc_count = EmployeeDocument.select().where(EmployeeDocument.chief_employee == employee).count() + 1
        
        # Конвертируем JPG в PNG
        if source_file.suffix.lower() in ['.jpg', '.jpeg']:
            dest_file = docs_folder / f"doc_{doc_count}.png"
            try:
                with Image.open(source_file) as img:
                    img.save(dest_file, 'PNG')
            except:
                dest_file = docs_folder / f"doc_{doc_count}{source_file.suffix}"
                shutil.copy2(source_file, dest_file)
        else:
            dest_file = docs_folder / f"doc_{doc_count}{source_file.suffix}"
            shutil.copy2(source_file, dest_file)
        
        # Создаем запись в БД в зависимости от типа сотрудника
        if hasattr(employee, 'guard_rank'):
            EmployeeDocument.create(
                guard_employee=employee,
                document_type=doc_name,
                page_number=1,
                file_path=str(dest_file)
            )
        else:
            EmployeeDocument.create(
                chief_employee=employee,
                document_type=doc_name,
                page_number=1,
                file_path=str(dest_file)
            )
        
        return str(dest_file)
    
    def view_personal_card(self, card):
        """Просматривает личную карточку"""
        if card.photo_path and os.path.exists(card.photo_path):
            self.open_pdf(card.photo_path)
        else:
            self.show_snackbar("Файл не найден", True)
    
    def view_document(self, doc):
        if doc.file_path and os.path.exists(doc.file_path):
            self.open_pdf(doc.file_path)
        else:
            self.show_snackbar("Файл не найден", True)
    
    def delete_personal_card_simple(self, card, employee, dialog_to_update=None):
        """Показывает диалог для списания карточки"""
        from datetime import date
        
        discard_date_field = ft.TextField(
            label="Дата списания (дд.мм.гггг)",
            value=date.today().strftime("%d.%m.%Y"),
            width=200,
            on_change=self.format_date_input,
            max_length=10
        )
        
        def confirm_discard(e):
            try:
                from datetime import datetime
                discard_date = datetime.strptime(discard_date_field.value, "%d.%m.%Y").date()
                card.is_discarded = True
                card.discarded_date = discard_date
                card.save()
                
                discard_dialog.open = False
                if dialog_to_update:
                    if hasattr(dialog_to_update, 'tabs_ref'):
                        dialog_to_update.tabs_ref.tabs[1].content = ft.Column(self._get_personal_cards_content(employee, dialog_to_update), scroll=ft.ScrollMode.AUTO)
                        self.page.update()
                    else:
                        dialog_to_update.content.controls.clear()
                        new_content = self._get_personal_cards_content(employee, dialog_to_update)
                        dialog_to_update.content.controls.extend(new_content)
                        dialog_to_update.content.update()
                        self.page.update()
            except ValueError:
                self.show_snackbar("Неверный формат даты!", True)
            except Exception as ex:
                self.show_snackbar(f"Ошибка: {ex}", True)
        
        discard_dialog = ft.AlertDialog(
            title=ft.Text("Списание карточки"),
            content=ft.Column([
                ft.Text("Укажите дату списания:"),
                discard_date_field
            ], height=100),
            actions=[
                ft.TextButton("Списать", on_click=confirm_discard),
                ft.TextButton("Отмена", on_click=lambda e: setattr(discard_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        
        self.page.overlay.append(discard_dialog)
        discard_dialog.open = True
        self.page.update()
    
    def delete_document_simple(self, doc, employee, dialog_to_update=None):
        try:
            doc.delete_instance()
            if dialog_to_update:
                if hasattr(dialog_to_update, 'tabs_ref'):
                    dialog_to_update.tabs_ref.tabs[2].content = ft.Column(self._get_documents_content(employee, dialog_to_update), scroll=ft.ScrollMode.AUTO)
                    self.page.update()
                else:
                    dialog_to_update.content.controls.clear()
                    new_content = self._get_documents_content(employee, dialog_to_update)
                    dialog_to_update.content.controls.extend(new_content)
                    dialog_to_update.content.update()
                    self.page.update()
        except:
            pass
