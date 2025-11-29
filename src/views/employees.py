import flet as ft
from database.models import GuardEmployee
from datetime import datetime
from base.base_employee_page import BaseEmployeePage
import os

class EmployeesPage(BaseEmployeePage):
    """Страница сотрудников охраны"""
    
    def __init__(self, page: ft.Page):
        self.selected_rank = "Все разряды"
        super().__init__(page)
    
    def _create_form_fields(self):
        """Создает поля формы"""
        self.name_field = ft.TextField(label="ФИО", width=300)
        self.birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.certificate_field = ft.TextField(label="Номер удостоверения (буква№ 000000)", width=200, max_length=9, on_change=self._format_certificate_input)
        self.guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.medical_exam_field = ft.TextField(label="Дата прохождения медкомиссии (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.periodic_check_field = ft.TextField(label="Дата прохождения периодической проверки (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option(str(i)) for i in range(3, 7)])
        self.payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")
        self.company_field = ft.Dropdown(label="Компания", width=150, options=[ft.dropdown.Option("Легион"), ft.dropdown.Option("Норд")], value="Легион")
    
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        self.edit_name_field = ft.TextField(label="ФИО", width=300)
        self.edit_birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.edit_certificate_field = ft.TextField(label="Номер удостоверения (буква№ 000000)", width=200, max_length=9, on_change=self._format_certificate_input)
        self.edit_guard_license_field = ft.TextField(label="Дата выдачи УЧО (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.edit_medical_exam_field = ft.TextField(label="Дата прохождения медкомиссии (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.edit_periodic_check_field = ft.TextField(label="Дата прохождения периодической проверки (дд.мм.гггг)", width=250, on_change=self.format_date_input, max_length=10)
        self.edit_guard_rank_field = ft.Dropdown(label="Разряд охранника", width=180, options=[ft.dropdown.Option(str(i)) for i in range(3, 7)])
        self.edit_payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")])
        self.edit_company_field = ft.Dropdown(label="Компания", width=150, options=[ft.dropdown.Option("Легион"), ft.dropdown.Option("Норд")])
    
    def _create_table(self):
        """Создает таблицу"""
        self.employees_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ФИО", width=400)),
                ft.DataColumn(ft.Text("Разряд", width=100)),
            ],
            rows=[],
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            heading_row_height=70,
            data_row_min_height=50,
            data_row_max_height=50,
            column_spacing=10,
            width=4000,
            height=707
        )
    
    def _get_base_query(self):
        return GuardEmployee.select().where(GuardEmployee.termination_date.is_null())
    
    def _apply_search_filter(self, query):
        # Сначала применяем базовую фильтрацию
        query = super()._apply_search_filter(query)
        
        # Затем добавляем фильтр по разряду
        if self.selected_rank != "Все разряды":
            query = query.where(GuardEmployee.guard_rank == int(self.selected_rank))
        
        return query
    
    def _apply_name_filter(self, query):
        return query.where(GuardEmployee.full_name.contains(self.search_value))
    
    def _apply_company_filter(self, query, companies):
        return query.where(GuardEmployee.company.in_(companies))
    
    def _get_order_field(self):
        return GuardEmployee.full_name
    
    def _create_table_row(self, employee):
        guard_rank_text = str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else "Не указано"
        return ft.DataRow(cells=[
            ft.DataCell(ft.Text(employee.full_name), on_tap=lambda e, emp=employee: self.show_basic_info(emp)),
            ft.DataCell(ft.Text(guard_rank_text)),
        ])
    
    def _get_detail_title(self):
        return "Информация о сотруднике"
    
    def _get_detail_pages(self, employee):
        """Возвращает список страниц для диалога"""
        return [
            {
                'title': 'Основная информация',
                'content': self._get_detail_content(employee)
            },
            {
                'title': 'Личные карточки',
                'content': self._get_personal_cards_content(employee)
            }
        ]
    
    def _get_detail_content(self, employee):
        content = [
            ft.Row([
                ft.Column([
                    self.get_photo_widget(employee.full_name),
                    ft.Text(f"Дата рождения: {self.format_date(employee.birth_date)}", size=16),
                    ft.Text(f"Номер удостоверения: {getattr(employee, 'certificate_number', '') or 'Не указано'}", size=16),
                    ft.Text(f"Дата выдачи УЧО: {self.format_date(getattr(employee, 'guard_license_date', None))}", size=16),
                    ft.Text(f"Разряд охранника: {str(getattr(employee, 'guard_rank', '')) if getattr(employee, 'guard_rank', None) else 'Не указано'}", size=16),
                    ft.Text(f"Медкомиссия: {self.format_date(getattr(employee, 'medical_exam_date', None))}", size=16),
                    ft.Text(f"Периодическая проверка: {self.format_date(getattr(employee, 'periodic_check_date', None))}", size=16),
                    ft.Text(f"Способ выдачи зарплаты: {getattr(employee, 'payment_method', 'на карту')}", size=16),
                    ft.Text(f"Компания: {getattr(employee, 'company', 'Легион')}", size=16),
                ]),
                ft.Container(expand=True)
            ])
        ]
        return content
    
    def _get_personal_cards_content(self, employee, dialog_ref=None):
        """Возвращает содержимое страницы личных карточек"""
        from database.models import PersonalCard
        from datetime import date
        
        cards = list(PersonalCard.select().where(PersonalCard.guard_employee == employee).order_by(PersonalCard.issue_date.desc()))
        
        # Форма добавления
        date_field = ft.TextField(
            label="Дата (дд.мм.гггг)",
            value=date.today().strftime("%d.%m.%Y"),
            width=150,
            on_change=self.format_date_input,
            max_length=10
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
                
                from datetime import datetime
                date_value = date_field.value.strip()
                if not date_value:
                    self.show_snackbar("Дата обязательна!", True)
                    return
                
                issue_date = datetime.strptime(date_value, "%d.%m.%Y").date()
                saved_path = self.save_personal_card(employee, selected_file_path[0])
                
                card = PersonalCard.select().where(
                    PersonalCard.guard_employee == employee,
                    PersonalCard.photo_path == saved_path
                ).order_by(PersonalCard.created_at.desc()).first()
                
                if card:
                    card.issue_date = issue_date
                    card.save()
                
                # Очищаем форму
                date_field.value = date.today().strftime("%d.%m.%Y")
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
            ft.Row([date_field, file_button, ft.ElevatedButton("Сохранить", on_click=save_card, width=100)], spacing=10)
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
                        title=ft.Text(f"Карточка #{i+1}"),
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
    
    def get_employee_folder_type(self):
        return "Сотрудники охраны"
    
    def add_personal_card_simple(self, employee, dialog_to_update=None):
        """Упрощенное добавление личной карточки"""
        def on_result(e: ft.FilePickerResultEvent):
            if e.files:
                self.show_card_date_dialog(employee, e.files[0].path, dialog_to_update)
        
        file_picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            dialog_title="Выберите фото карточки",
            allowed_extensions=["jpg", "jpeg", "png", "pdf"]
        )
    
    def show_card_date_dialog(self, employee, file_path, dialog_to_update=None):
        from datetime import date
        
        date_field = ft.TextField(
            label="Дата выдачи (дд.мм.гггг)",
            value=date.today().strftime("%d.%m.%Y"),
            width=200,
            on_change=self.format_date_input,
            max_length=10
        )
        
        def save_card(e):
            try:
                from database.models import PersonalCard
                from datetime import datetime
                
                date_value = date_field.value.strip()
                if not date_value:
                    raise ValueError("Дата выдачи обязательна!")
                
                issue_date = datetime.strptime(date_value, "%d.%m.%Y").date()
                saved_path = self.save_personal_card(employee, file_path)
                
                # Обновляем дату в базе
                card = PersonalCard.select().where(
                    PersonalCard.guard_employee == employee,
                    PersonalCard.photo_path == saved_path
                ).order_by(PersonalCard.created_at.desc()).first()
                
                if card:
                    card.issue_date = issue_date
                    card.save()
                
                date_dialog.open = False
                self.page.update()
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
            except Exception as ex:
                self.show_snackbar(f"Ошибка: {ex}", True)
        
        date_dialog = ft.AlertDialog(
            title=ft.Text("Дата выдачи карточки"),
            content=date_field,
            actions=[
                ft.TextButton("Сохранить", on_click=save_card),
                ft.TextButton("Отмена", on_click=lambda e: setattr(date_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        
        self.page.overlay.append(date_dialog)
        date_dialog.open = True
        self.page.update()
    
    def delete_personal_card_simple(self, card, employee, dialog_to_update=None):
        """Упрощенное удаление личной карточки"""
        try:
            card.delete_instance()
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
        except:
            pass
    
    def show_basic_info(self, employee):
        """Показывает диалог с вкладками"""
        self.show_basic_info_with_tabs(employee)

    
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
    
    def show_personal_cards(self, employee):
        """Показывает диалог с личными карточками"""
        cards_dialog = ft.AlertDialog(
            title=ft.Text(f"Личные карточки: {employee.full_name}"),
            content=ft.Column([], height=600, width=800, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: setattr(cards_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        cards_dialog.content = ft.Column(self._get_personal_cards_content(employee, cards_dialog), height=600, width=800, scroll=ft.ScrollMode.AUTO)
        
        self.page.overlay.append(cards_dialog)
        cards_dialog.open = True
        self.page.update()
    
    def show_documents(self, employee):
        """Показывает диалог с документами"""
        docs_dialog = ft.AlertDialog(
            title=ft.Text(f"Документы: {employee.full_name}"),
            content=ft.Column([], height=600, width=800, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: setattr(docs_dialog, 'open', False) or self.page.update())
            ],
            modal=True
        )
        docs_dialog.content = ft.Column(self._get_documents_content(employee, docs_dialog), height=600, width=800, scroll=ft.ScrollMode.AUTO)
        
        self.page.overlay.append(docs_dialog)
        docs_dialog.open = True
        self.page.update()
    
    def _get_documents_content(self, employee, dialog_ref=None):
        """Возвращает содержимое страницы документов"""
        from database.models import EmployeeDocument
        
        docs = list(EmployeeDocument.select().where(EmployeeDocument.guard_employee == employee).order_by(EmployeeDocument.created_at.desc()))
        
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
        docs_folder = Path(f"storage/data/Сотрудники охраны/{safe_name}/документы")
        docs_folder.mkdir(parents=True, exist_ok=True)
        
        source_file = Path(file_path)
        doc_count = EmployeeDocument.select().where(EmployeeDocument.guard_employee == employee).count() + 1
        
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
        
        EmployeeDocument.create(
            guard_employee=employee,
            document_type=doc_name,
            page_number=1,
            file_path=str(dest_file)
        )
        
        return str(dest_file)
    
    def view_document(self, doc):
        if doc.file_path and os.path.exists(doc.file_path):
            self.open_pdf(doc.file_path)
        else:
            self.show_snackbar("Файл не найден", True)
    
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
    
    def add_personal_card(self, employee):
        """Добавляет личную карточку"""
        from database.models import PersonalCard
        from datetime import date, datetime
        
        # Поля для ввода даты
        date_field = ft.TextField(
            label="Дата выдачи (дд.мм.гггг)",
            value=date.today().strftime("%d.%m.%Y"),
            width=200,
            on_change=self.format_date_input,
            max_length=10
        )
        
        selected_file_path = None
        
        def on_file_result(e: ft.FilePickerResultEvent):
            nonlocal selected_file_path
            if e.files:
                selected_file_path = e.files[0].path
                file_button.text = f"Файл: {e.files[0].name}"
                self.page.update()
        
        def select_file(e):
            file_picker.pick_files(
                dialog_title="Выберите фото личной карточки",
                allowed_extensions=["jpg", "jpeg", "png", "pdf"]
            )
        
        def save_card(e):
            try:
                if not selected_file_path:
                    raise ValueError("Выберите файл!")
                
                date_value = date_field.value.strip()
                if not date_value:
                    raise ValueError("Дата выдачи обязательна!")
                
                issue_date = datetime.strptime(date_value, "%d.%m.%Y").date()
                
                card = PersonalCard.create(
                    guard_employee=employee,
                    issue_date=issue_date,
                    photo_path=selected_file_path
                )
                
                card_dialog.open = False
                # Обновляем страницу карточек
                all_cards_count = PersonalCard.select().where(PersonalCard.guard_employee == employee).count()
                self.cards_page = (all_cards_count - 1) // 13
                self._update_detail_dialog()
            except Exception as ex:
                self.show_snackbar(f"Ошибка: {ex}", True)
        
        def select_file(e):
            if not hasattr(self, 'card_file_picker'):
                self.card_file_picker = ft.FilePicker(on_result=on_file_result)
                if self.page:
                    self.page.overlay.append(self.card_file_picker)
                    self.page.update()
            else:
                self.card_file_picker.on_result = on_file_result
            
            self.card_file_picker.pick_files(
                dialog_title="Выберите фото личной карточки",
                allowed_extensions=["jpg", "jpeg", "png", "pdf"]
            )
        
        file_button = ft.ElevatedButton("Выбрать файл", on_click=select_file)
        
        card_dialog = ft.AlertDialog(
            title=ft.Text("Добавить личную карточку"),
            content=ft.Column([date_field, file_button], spacing=10),
            actions=[
                ft.TextButton("Сохранить", on_click=save_card),
                ft.TextButton("Отмена", on_click=lambda e: setattr(card_dialog, 'open', False))
            ],
            modal=True
        )
        
        if self.page:
            if card_dialog not in self.page.overlay:
                self.page.overlay.append(card_dialog)
            card_dialog.open = True
            self.page.update()
    
    def view_personal_card(self, card):
        """Просматривает личную карточку"""
        if card.photo_path and os.path.exists(card.photo_path):
            self.open_pdf(card.photo_path)
        else:
            self.show_snackbar("Файл не найден", True)
    
    def delete_personal_card(self, card, employee):
        """Удаляет личную карточку"""
        try:
            card.delete_instance()
            self._update_detail_dialog()
        except Exception as ex:
            self.show_snackbar(f"Ошибка: {ex}", True)
    
    def _get_add_title(self):
        return "Добавить сотрудника"
    
    def _get_form_fields(self):
        return [self.name_field, self.birth_field, self.certificate_field, self.guard_license_field, self.medical_exam_field, self.periodic_check_field, self.guard_rank_field, self.payment_method_field, self.company_field]
    
    def _get_edit_fields(self):
        return [self.edit_name_field, self.edit_birth_field, self.edit_certificate_field, self.edit_guard_license_field, self.edit_medical_exam_field, self.edit_periodic_check_field, self.edit_guard_rank_field, self.edit_payment_method_field, self.edit_company_field]
    
    def _populate_edit_fields(self, employee):
        self.edit_name_field.value = employee.full_name
        self.edit_birth_field.value = self.format_date(employee.birth_date)
        self.edit_certificate_field.value = getattr(employee, 'certificate_number', '') or ''
        self.edit_guard_license_field.value = self.format_date(getattr(employee, 'guard_license_date', None)) if hasattr(employee, 'guard_license_date') else ""
        self.edit_guard_rank_field.value = str(employee.guard_rank) if hasattr(employee, 'guard_rank') and employee.guard_rank else None
        self.edit_medical_exam_field.value = self.format_date(getattr(employee, 'medical_exam_date', None)) if hasattr(employee, 'medical_exam_date') else ""
        self.edit_periodic_check_field.value = self.format_date(getattr(employee, 'periodic_check_date', None)) if hasattr(employee, 'periodic_check_date') else ""
        self.edit_payment_method_field.value = getattr(employee, 'payment_method', 'на карту')
        self.edit_company_field.value = getattr(employee, 'company', 'Легион')
    
    def _save_operation(self):
        full_name = self.name_field.value.strip()
        birth_value = self.birth_field.value.strip()
        certificate_value = self.certificate_field.value.strip()
        guard_license_value = self.guard_license_field.value.strip()
        guard_rank_value = self.guard_rank_field.value
        medical_exam_value = self.medical_exam_field.value.strip()
        periodic_check_value = self.periodic_check_field.value.strip()
        payment_method_value = self.payment_method_field.value
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value:
            raise ValueError("Дата рождения обязательна!")
        
        birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        guard_license_date = datetime.strptime(guard_license_value, "%d.%m.%Y").date() if guard_license_value else None
        guard_rank = int(guard_rank_value) if guard_rank_value else None
        medical_exam_date = datetime.strptime(medical_exam_value, "%d.%m.%Y").date() if medical_exam_value else None
        periodic_check_date = datetime.strptime(periodic_check_value, "%d.%m.%Y").date() if periodic_check_value else None
        
        employee = GuardEmployee.create(
            full_name=full_name,
            birth_date=birth_date,
            certificate_number=certificate_value or None,
            guard_license_date=guard_license_date,
            guard_rank=guard_rank,
            medical_exam_date=medical_exam_date,
            periodic_check_date=periodic_check_date,
            payment_method=payment_method_value or "на карту",
            company=self.company_field.value or "Легион"
        )
        

        return True
    
    def _save_edit_operation(self):
        full_name = self.edit_name_field.value.strip()
        birth_value = self.edit_birth_field.value.strip()
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value or birth_value == "Не указано":
            raise ValueError("Дата рождения обязательна!")
        
        self.current_employee.full_name = full_name
        self.current_employee.birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        self.current_employee.certificate_number = self.edit_certificate_field.value.strip() or None
        
        guard_license_value = self.edit_guard_license_field.value.strip()
        self.current_employee.guard_license_date = datetime.strptime(guard_license_value, "%d.%m.%Y").date() if guard_license_value and guard_license_value != "Не указано" else None
        
        self.current_employee.guard_rank = int(self.edit_guard_rank_field.value) if self.edit_guard_rank_field.value else None
        
        medical_exam_value = self.edit_medical_exam_field.value.strip()
        self.current_employee.medical_exam_date = datetime.strptime(medical_exam_value, "%d.%m.%Y").date() if medical_exam_value and medical_exam_value != "Не указано" else None
        
        periodic_check_value = self.edit_periodic_check_field.value.strip()
        self.current_employee.periodic_check_date = datetime.strptime(periodic_check_value, "%d.%m.%Y").date() if periodic_check_value and periodic_check_value != "Не указано" else None
        
        self.current_employee.payment_method = self.edit_payment_method_field.value or 'на карту'
        self.current_employee.company = self.edit_company_field.value or 'Легион'
        
        self.current_employee.save()
        return True
    
    def _get_success_message(self):
        return "Сотрудник добавлен!"
    
    def _get_page_title(self):
        return "Сотрудники охраны"
    
    def _get_add_button_text(self):
        return "Добавить сотрудника"
    
    def _get_employee_type(self):
        return "сотрудника"
    
    def on_rank_change(self, e):
        """Обработчик изменения фильтра по разряду"""
        self.selected_rank = e.control.value
        self.current_page = 0
        self.refresh_table()
        if self.page:
            self.page.update()
    
    def _format_certificate_input(self, e):
        """Форматирует ввод номера удостоверения"""
        value = e.control.value.upper().replace("№", "").replace(" ", "")
        if len(value) > 0 and value[0].isalpha():
            letter = value[0]
            numbers = ''.join(filter(str.isdigit, value[1:]))[:6]
            if numbers:
                e.control.value = f"{letter}№ {numbers}"
            else:
                e.control.value = f"{letter}№ "
        elif len(value) > 0 and not value[0].isalpha():
            e.control.value = ""
        self.page.update()
    
    def _get_search_row(self):
        """Переопределяем строку поиска для добавления фильтра по разряду"""
        return ft.Row([
            ft.TextField(label="Поиск по ФИО", width=300, on_change=self.on_search_change, autofocus=False, dense=True),
            ft.Dropdown(
                label="Разряд",
                width=200,
                value="Все разряды",
                options=[
                    ft.dropdown.Option("Все разряды"),
                    ft.dropdown.Option("3"),
                    ft.dropdown.Option("4"),
                    ft.dropdown.Option("5"),
                    ft.dropdown.Option("6"),
                ],
                on_change=self.on_rank_change,
                dense=True,
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
    

    

    

    

    
    def _get_detail_actions(self, employee):
        """Возвращает кнопки действий для диалога"""
        return [
            ft.TextButton("Изменить фотографию", on_click=lambda e, emp=employee: self.change_photo(emp)),
            ft.TextButton("Редактировать", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_edit_dialog(emp))),
            ft.TextButton("Уволить", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_termination_dialog(emp)), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Закрыть", on_click=lambda e: self.close_detail_dialog())
        ]
    

    

    

    

    

    

    


# Функция-обертка для совместимости
def employees_page(page: ft.Page = None) -> ft.Column:
    return EmployeesPage(page).render()