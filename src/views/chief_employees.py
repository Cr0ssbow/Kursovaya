import flet as ft
from database.models import ChiefEmployee, Object, ChiefObjectAssignment, db
from datetime import datetime
from base.base_employee_page import BaseEmployeePage

class ChiefEmployeesPage(BaseEmployeePage):
    """Страница начальников охраны"""
    
    def _create_form_fields(self):
        """Создает поля формы"""
        self.name_field = ft.TextField(label="ФИО", width=300)
        self.birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.position_field = ft.TextField(label="Должность", width=250)
        self.salary_field = ft.TextField(label="Зарплата", width=150)
        self.payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")], value="на карту")
        self.company_field = ft.Dropdown(label="Компания", width=150, options=[ft.dropdown.Option("Легион"), ft.dropdown.Option("Норд")], value="Легион")
    
    def _create_table(self):
        """Создает таблицу"""
        self.employees_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ФИО", width=400)),
                ft.DataColumn(ft.Text("Должность", width=200)),
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
        return ChiefEmployee.select().where(ChiefEmployee.termination_date.is_null())
    
    def _apply_name_filter(self, query):
        return query.where(ChiefEmployee.full_name.contains(self.search_value))
    
    def _apply_company_filter(self, query, companies):
        return query.where(ChiefEmployee.company.in_(companies))
    
    def _get_order_field(self):
        return ChiefEmployee.full_name
    
    def _create_table_row(self, employee):
        return ft.DataRow(cells=[
            ft.DataCell(ft.Text(employee.full_name), on_tap=lambda e, emp=employee: self.show_detail_dialog(emp)),
            ft.DataCell(ft.Text(employee.position)),
        ])
    
    def _get_detail_title(self):
        return "Карточка начальника"
    
    def _get_detail_content(self, employee):
        # Получаем закрепленные объекты
        assigned_objects = []
        try:
            if db.is_closed():
                db.connect()
            assignments = ChiefObjectAssignment.select().where(ChiefObjectAssignment.chief == employee)
            assigned_objects = [assignment.object.name for assignment in assignments]
        except Exception as e:
            print(f"Ошибка получения объектов: {e}")
        finally:
            if not db.is_closed():
                db.close()
        
        objects_text = ", ".join(assigned_objects) if assigned_objects else "Нет закрепленных объектов"
        
        content = [
            ft.Row([
                ft.Column([
                    self.get_photo_widget(employee.full_name),
                    ft.Text(f"Дата рождения: {self.format_date(employee.birth_date)}", size=16),
                    ft.Text(f"Должность: {employee.position}", size=16),
                    ft.Text(f"Зарплата: {employee.salary} ₽", size=16),
                    ft.Text(f"Способ выдачи зарплаты: {employee.payment_method}", size=16),
                    ft.Text(f"Компания: {getattr(employee, 'company', 'Легион')}", size=16),
                    ft.Text(f"Закрепленные объекты: {objects_text}", size=16),
                ]),
                ft.Container(expand=True)
            ])
        ]
        return content
    
    def _get_add_title(self):
        return "Добавить начальника охраны"
    
    def _get_form_fields(self):
        return [self.name_field, self.birth_field, self.position_field, self.salary_field, self.payment_method_field, self.company_field]
    
    def _save_operation(self):
        full_name = self.name_field.value.strip()
        birth_value = self.birth_field.value.strip()
        position_value = self.position_field.value.strip()
        salary_value = self.salary_field.value.strip()
        payment_method_value = self.payment_method_field.value
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value:
            raise ValueError("Дата рождения обязательна!")
        if not position_value:
            raise ValueError("Должность обязательна!")
        
        birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        salary = float(salary_value) if salary_value else 0
        
        employee = ChiefEmployee.create(
            full_name=full_name,
            birth_date=birth_date,
            position=position_value,
            salary=salary,
            payment_method=payment_method_value or "на карту",
            company=self.company_field.value or "Легион"
        )
        

        return True
    
    def _get_success_message(self):
        return "Начальник добавлен!"
    
    def _get_page_title(self):
        return "Начальники охраны"
    
    def _get_add_button_text(self):
        return "Добавить начальника"
    
    def _create_edit_fields(self):
        """Создает поля редактирования"""
        self.edit_name_field = ft.TextField(label="ФИО", width=300)
        self.edit_birth_field = ft.TextField(label="Дата рождения (дд.мм.гггг)", width=180, on_change=self.format_date_input, max_length=10)
        self.edit_position_field = ft.TextField(label="Должность", width=250)
        self.edit_salary_field = ft.TextField(label="Зарплата", width=150)
        self.edit_payment_method_field = ft.Dropdown(label="Способ выдачи зарплаты", width=250, options=[ft.dropdown.Option("на карту"), ft.dropdown.Option("на руки")])
        self.edit_company_field = ft.Dropdown(label="Компания", width=150, options=[ft.dropdown.Option("Легион"), ft.dropdown.Option("Норд")])
    
    def _get_edit_fields(self):
        return [self.edit_name_field, self.edit_birth_field, self.edit_position_field, self.edit_salary_field, self.edit_payment_method_field, self.edit_company_field]
    
    def _populate_edit_fields(self, employee):
        self.edit_name_field.value = employee.full_name
        self.edit_birth_field.value = self.format_date(employee.birth_date)
        self.edit_position_field.value = employee.position
        self.edit_salary_field.value = str(employee.salary)
        self.edit_payment_method_field.value = employee.payment_method
        self.edit_company_field.value = getattr(employee, 'company', 'Легион')
    
    def _save_edit_operation(self):
        full_name = self.edit_name_field.value.strip()
        birth_value = self.edit_birth_field.value.strip()
        position_value = self.edit_position_field.value.strip()
        salary_value = self.edit_salary_field.value.strip()
        payment_method_value = self.edit_payment_method_field.value
        
        if not full_name:
            raise ValueError("ФИО обязательно!")
        if not birth_value or birth_value == "Не указано":
            raise ValueError("Дата рождения обязательна!")
        if not position_value:
            raise ValueError("Должность обязательна!")
        
        birth_date = datetime.strptime(birth_value, "%d.%m.%Y").date()
        salary = float(salary_value) if salary_value else 0
        
        self.current_employee.full_name = full_name
        self.current_employee.birth_date = birth_date
        self.current_employee.position = position_value
        self.current_employee.salary = salary
        self.current_employee.payment_method = payment_method_value or "на карту"
        self.current_employee.company = self.edit_company_field.value or "Легион"
        
        self.current_employee.save()
        return True
    
    def _get_employee_type(self):
        return "начальника"
    
    def show_detail_dialog(self, employee):
        """Переопределяем для добавления кнопки управления объектами"""
        self.detail_dialog.title = ft.Text(f"{self._get_detail_title()}: {employee.full_name}")
        self.detail_dialog.content = ft.Column(self._get_detail_content(employee), spacing=10, height=500, width=600)
        self.detail_dialog.actions = [
            ft.TextButton("Изменить фотографию", on_click=lambda e, emp=employee: self.change_photo(emp)),
            ft.TextButton("Управление объектами", on_click=lambda e: self.show_objects_dialog(employee)),
            ft.TextButton("Редактировать", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_edit_dialog(emp))),
            ft.TextButton("Уволить", on_click=lambda e, emp=employee: (self.close_detail_dialog(), self.show_termination_dialog(emp)), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Закрыть", on_click=lambda e: self.close_detail_dialog())
        ]
        self.detail_dialog.open = True
        if self.page and self.detail_dialog not in self.page.overlay:
            self.page.overlay.append(self.detail_dialog)
        if self.page:
            self.page.update()
    
    def show_objects_dialog(self, chief):
        """Показывает диалог управления объектами"""
        try:
            if db.is_closed():
                db.connect()
            
            # Получаем все объекты
            all_objects = list(Object.select())
            
            # Получаем уже назначенные объекты
            assigned_objects = set()
            assignments = ChiefObjectAssignment.select().where(ChiefObjectAssignment.chief == chief)
            for assignment in assignments:
                assigned_objects.add(assignment.object.id)
            
            # Создаем чекбоксы для объектов
            object_checkboxes = []
            for obj in all_objects:
                checkbox = ft.Checkbox(
                    label=obj.name,
                    value=obj.id in assigned_objects,
                    data=obj.id
                )
                object_checkboxes.append(checkbox)
            
            def save_assignments():
                try:
                    if db.is_closed():
                        db.connect()
                    
                    # Удаляем все текущие назначения
                    ChiefObjectAssignment.delete().where(ChiefObjectAssignment.chief == chief).execute()
                    
                    # Добавляем новые назначения
                    for checkbox in object_checkboxes:
                        if checkbox.value:
                            obj = Object.get_by_id(checkbox.data)
                            ChiefObjectAssignment.create(chief=chief, object=obj)
                    
                    self.page.close(objects_dialog)
                    self.show_snackbar("Объекты обновлены!")
                    
                except Exception as e:
                    self.show_snackbar(f"Ошибка: {str(e)}", True)
                finally:
                    if not db.is_closed():
                        db.close()
            
            objects_dialog = ft.AlertDialog(
                title=ft.Text(f"Управление объектами - {chief.full_name}"),
                content=ft.Container(
                    content=ft.Column(object_checkboxes, scroll=ft.ScrollMode.AUTO),
                    width=400,
                    height=300
                ),
                actions=[
                    ft.TextButton("Сохранить", on_click=lambda e: save_assignments()),
                    ft.TextButton("Отмена", on_click=lambda e: self.page.close(objects_dialog))
                ]
            )
            
            self.page.overlay.append(objects_dialog)
            self.page.update()
            self.page.open(objects_dialog)
            
        except Exception as e:
            self.show_snackbar(f"Ошибка: {str(e)}", True)
        finally:
            if not db.is_closed():
                db.close()

    def change_photo(self, employee):
        """Изменение фотографии сотрудника"""
        def on_result(e: ft.FilePickerResultEvent):
            if e.files:
                try:
                    photo_path = self.photo_manager.save_photo(employee.full_name, e.files[0].path)
                    employee.photo_path = photo_path
                    employee.save()
                    self.show_snackbar("Фотография обновлена!")
                    self.close_detail_dialog()
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
    

    


# Функция-обертка для совместимости
def chief_employees_page(page: ft.Page = None) -> ft.Column:
    return ChiefEmployeesPage(page).render()