import flet as ft
from abc import abstractmethod
from datetime import datetime
from base.base_page import BasePage

class BaseEmployeePage(BasePage):
    """Базовый класс для страниц управления сотрудниками"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.employees_table = None
        self.add_dialog = None
        self.detail_dialog = None
        self.show_nord = True
        self.show_legion = True
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
        self.detail_dialog.title = ft.Text(f"{self._get_detail_title()}: {employee.full_name}")
        self.detail_dialog.content = ft.Column(self._get_detail_content(employee), spacing=10, height=200)
        self.detail_dialog.actions = [
            ft.TextButton("Редактировать", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_edit_dialog(emp))),
            ft.TextButton("Уволить", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_termination_dialog(emp)), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Закрыть", on_click=lambda e: self.close_detail_dialog())
        ]
        self.detail_dialog.open = True
        if self.page and self.detail_dialog not in self.page.overlay:
            self.page.overlay.append(self.detail_dialog)
        if self.page:
            self.page.update()
    
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