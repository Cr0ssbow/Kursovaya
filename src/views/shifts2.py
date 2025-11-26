import flet as ft
import datetime
from database.models import Assignment, Employee, Object, db
from peewee import *
from views.settings import load_cell_shape_from_db

# Словарь русских названий месяцев
RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

def shifts2_page(page: ft.Page = None):
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    
    current_month_display = ft.Text("", size=24, weight="bold")
    calendar_grid_container = ft.Column()
    
    # Диалог для отображения смен дня
    shifts_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Смены на дату"),
        content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=400),
        actions=[
            ft.TextButton("Добавить смену", on_click=lambda e: open_add_shift_dialog()),
            ft.TextButton("Закрыть", on_click=lambda e: close_shifts_dialog())
        ]
    )
    
    # Диалог добавления смены
    add_shift_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Добавить смену"),
        content=ft.Column([], height=400, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton("Сохранить", on_click=lambda e: save_new_shift()),
            ft.TextButton("Отмена", on_click=lambda e: close_add_shift_dialog())
        ]
    )
    
    # Диалог редактирования смены
    edit_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Редактирование смены"),
        content=ft.Column([], height=300, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton("Сохранить", on_click=lambda e: save_shift_changes()),
            ft.TextButton("Удалить", on_click=lambda e: confirm_delete_shift(), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Отмена", on_click=lambda e: close_edit_dialog())
        ]
    )
    
    # Диалог подтверждения удаления
    delete_confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Подтвердите удаление"),
        content=ft.Text("Вы уверены, что хотите удалить эту смену?"),
        actions=[
            ft.TextButton("Да", on_click=lambda e: delete_shift()),
            ft.TextButton("Отмена", on_click=lambda e: close_delete_confirm())
        ]
    )
    
    def close_shifts_dialog():
        shifts_dialog.open = False
        page.dialog = None
        page.update()
    
    def open_add_shift_dialog():
        setup_add_shift_form()
        page.dialog = add_shift_dialog
        add_shift_dialog.open = True
        page.update()
    
    def close_add_shift_dialog():
        add_shift_dialog.open = False
        page.dialog = shifts_dialog
        page.update()
    
    def close_edit_dialog():
        edit_dialog.open = False
        page.dialog = None
        page.update()
    
    def confirm_delete_shift():
        page.dialog = delete_confirm_dialog
        delete_confirm_dialog.open = True
        page.update()
    
    def close_delete_confirm():
        delete_confirm_dialog.open = False
        page.dialog = edit_dialog
        page.update()
    
    def delete_shift():
        if current_assignment:
            try:
                if db.is_closed():
                    db.connect()
                current_assignment.delete_instance()
                delete_confirm_dialog.open = False
                edit_dialog.open = False
                page.dialog = None
                update_calendar()
                show_shifts_for_date(current_shift_date)
            except Exception as e:
                print(f"Ошибка удаления: {e}")
            finally:
                if not db.is_closed():
                    db.close()
    
    current_assignment = None
    current_shift_date = None
    absent_checkbox = ft.Checkbox(label="Пропуск", on_change=lambda e: toggle_absent_comment())
    absent_comment_field = ft.TextField(label="Комментарий к пропуску", visible=False, multiline=True)
    deduction_checkbox = ft.Checkbox(label="Удержание", on_change=lambda e: toggle_deduction_field())
    deduction_amount_field = ft.TextField(label="Сумма удержания", visible=False)
    bonus_amount_field = ft.TextField(label="Сумма премии", on_change=lambda e: toggle_bonus_comment())
    bonus_comment_field = ft.TextField(label="Комментарий к премии", visible=False, multiline=True)
    
    # Поля для добавления смены
    employee_search = ft.TextField(label="Поиск сотрудника", width=300, on_change=lambda e: search_employees(e.control.value))
    search_results = ft.Column(visible=False)
    object_search = ft.TextField(label="Поиск объекта", width=300, on_change=lambda e: search_objects(e.control.value))
    object_search_results = ft.Column(visible=False)
    hours_dropdown = ft.Dropdown(label="Количество часов", options=[ft.dropdown.Option("12"), ft.dropdown.Option("24")], value="12", width=200)
    hourly_rate_display = ft.Text("Почасовая ставка: не выбрано", size=16)
    address_display = ft.Text("Адрес: не выбрано", size=16)
    
    def toggle_absent_comment():
        absent_comment_field.visible = absent_checkbox.value
        update_bonus_fields_visibility()
        page.update()
    
    def toggle_deduction_field():
        deduction_amount_field.visible = deduction_checkbox.value
        update_bonus_fields_visibility()
        page.update()
    
    def update_bonus_fields_visibility():
        # Поля премии показываются только если нет пропуска и нет удержания
        show_bonus = not absent_checkbox.value and not deduction_checkbox.value
        bonus_amount_field.visible = show_bonus
        bonus_comment_field.visible = show_bonus
    
    def toggle_bonus_comment():
        bonus_comment_field.visible = not absent_checkbox.value
        page.update()
    
    def edit_shift(assignment):
        nonlocal current_assignment
        current_assignment = assignment
        
        absent_checkbox.value = assignment.is_absent
        absent_comment_field.value = assignment.absent_comment or ""
        absent_comment_field.visible = assignment.is_absent
        
        deduction_checkbox.value = float(assignment.deduction_amount) > 0
        deduction_amount_field.value = str(float(assignment.deduction_amount))
        deduction_amount_field.visible = float(assignment.deduction_amount) > 0
        
        bonus_amount_field.value = str(float(assignment.bonus_amount))
        bonus_comment_field.value = assignment.bonus_comment or ""
        # Обновляем видимость полей премии
        update_bonus_fields_visibility()
        
        edit_dialog.content.controls = [
            ft.Text(f"Сотрудник: {assignment.employee.full_name}", weight="bold"),
            ft.Text(f"Объект: {assignment.object.name}"),
            ft.Text(f"Дата: {assignment.date.strftime('%d.%m.%Y')}"),
            ft.Divider(),
            absent_checkbox,
            absent_comment_field,
            deduction_checkbox,
            deduction_amount_field,
            bonus_amount_field,
            bonus_comment_field
        ]
        
        page.dialog = edit_dialog
        edit_dialog.open = True
        page.update()
    
    def save_shift_changes():
        if current_assignment:
            try:
                if db.is_closed():
                    db.connect()
                
                current_assignment.is_absent = absent_checkbox.value
                current_assignment.absent_comment = absent_comment_field.value if absent_checkbox.value else None
                current_assignment.deduction_amount = float(deduction_amount_field.value or "0") if deduction_checkbox.value else 0
                current_assignment.bonus_amount = float(bonus_amount_field.value or "0") if not absent_checkbox.value else 0
                current_assignment.bonus_comment = bonus_comment_field.value if float(bonus_amount_field.value or "0") > 0 and not absent_checkbox.value else None
                current_assignment.save()
                
                close_edit_dialog()
                update_calendar()
                show_shifts_for_date(current_shift_date)
                
            except Exception as e:
                print(f"Ошибка сохранения: {e}")
            finally:
                if not db.is_closed():
                    db.close()
    
    def show_shifts_for_date(date_obj):
        nonlocal current_shift_date
        current_shift_date = date_obj
        try:
            if db.is_closed():
                db.connect()
            
            assignments = Assignment.select().join(Employee).switch(Assignment).join(Object).where(
                Assignment.date == date_obj
            )
            
            shifts_dialog.title.value = f"Смены на {date_obj.strftime('%d.%m.%Y')}"
            shifts_dialog.content.controls.clear()
            
            if assignments:
                for assignment in assignments:
                    status_text = ""
                    description_lines = [
                        ft.Text(f"Сотрудник: {assignment.employee.full_name}", weight="bold"),
                        ft.Text(f"Объект: {assignment.object.name}"),
                        ft.Text(f"Часы: {assignment.hours}"),
                        ft.Text(f"Ставка: {assignment.hourly_rate} ₽/час")
                    ]
                    
                    if assignment.is_absent:
                        if assignment.absent_comment:
                            description_lines.append(ft.Text(f"Пропуск: {assignment.absent_comment}", color=ft.Colors.RED))
                        else:
                            description_lines.append(ft.Text("Пропуск", color=ft.Colors.RED))
                    
                    # Отображаем удержания отдельно
                    if float(assignment.deduction_amount) > 0:
                        description_lines.append(ft.Text(f"Удержание: {assignment.deduction_amount} ₽", color=ft.Colors.ORANGE))
                    
                    # Отображаем премии только для отработанных смен
                    if not assignment.is_absent and float(assignment.bonus_amount) > 0:
                        if assignment.bonus_comment:
                            description_lines.append(ft.Text(f"Премия: {assignment.bonus_amount} ₽ - {assignment.bonus_comment}", color=ft.Colors.GREEN))
                        else:
                            description_lines.append(ft.Text(f"Премия: {assignment.bonus_amount} ₽", color=ft.Colors.GREEN))
                    
                    shifts_dialog.content.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Column(description_lines, expand=True),
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            on_click=lambda e, a=assignment: edit_shift(a)
                                        )
                                    ])
                                ], spacing=5),
                                padding=10
                            )
                        )
                    )
            else:
                shifts_dialog.content.controls.append(
                    ft.Text("На эту дату смен нет", size=16, color=ft.Colors.GREY)
                )
            
            page.dialog = shifts_dialog
            shifts_dialog.open = True
            page.update()
            
        except Exception as e:
            print(f"Ошибка загрузки смен: {e}")
        finally:
            if not db.is_closed():
                db.close()
    
    def get_shifts_count_for_date(date_obj):
        try:
            if db.is_closed():
                db.connect()
            count = Assignment.select().where(Assignment.date == date_obj).count()
            return count
        except:
            return 0
        finally:
            if not db.is_closed():
                db.close()
    
    def create_day_cell(day, date_obj):
        shifts_count = get_shifts_count_for_date(date_obj)
        cell_shape = load_cell_shape_from_db()
        border_radius = 25 if cell_shape == "round" else 5
        
        return ft.Container(
            content=ft.Column([
                ft.Text(str(day), size=14, weight="bold"),
                ft.Text(f"{shifts_count}" if shifts_count > 0 else "", size=10, color=ft.Colors.BLUE)
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
            width=50,
            height=50,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=border_radius,
            on_click=lambda e: show_shifts_for_date(date_obj),
            alignment=ft.alignment.center
        )
    
    def get_calendar_grid(year, month):
        first_day = datetime.date(year, month, 1)
        if month == 12:
            days_in_month = (datetime.date(year + 1, 1, 1) - first_day).days
        else:
            days_in_month = (datetime.date(year, month + 1, 1) - first_day).days
        
        start_weekday = first_day.weekday()
        empty_slots = start_weekday
        
        days = []
        for _ in range(empty_slots):
            days.append(ft.Container(width=50, height=50))
        
        for day in range(1, days_in_month + 1):
            current_date = datetime.date(year, month, day)
            days.append(create_day_cell(day, current_date))
        
        while len(days) % 7 != 0:
            days.append(ft.Container(width=50, height=50))
        
        return ft.Column([
            ft.Row([
                ft.Text("Пн", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Вт", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Ср", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Чт", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Пт", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Сб", weight="bold", width=50, text_align=ft.TextAlign.CENTER),
                ft.Text("Вс", weight="bold", width=50, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Row(days[i:i+7], alignment=ft.MainAxisAlignment.CENTER)
                for i in range(0, len(days), 7)
            ])
        ])
    
    def update_calendar():
        current_month_display.value = f"{RUSSIAN_MONTHS[current_month]} {current_year}"
        calendar_grid_container.controls = [get_calendar_grid(current_year, current_month)]
        page.update()
    
    def change_month(direction):
        nonlocal current_month, current_year
        if direction == -1:
            current_month -= 1
            if current_month < 1:
                current_month = 12
                current_year -= 1
        else:
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        update_calendar()
    
    update_calendar()
    
    shifts_content = ft.Column([
        ft.Text("Календарь смен", size=24, weight="bold"),
        ft.Divider(),
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: change_month(-1)),
            current_month_display,
            ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: change_month(1))
        ], alignment=ft.MainAxisAlignment.CENTER),
        calendar_grid_container
    ], spacing=10, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    # Функции для добавления смены
    def search_employees(query):
        if not query or len(query) < 2:
            search_results.visible = False
            page.update()
            return
        try:
            if db.is_closed():
                db.connect()
            from datetime import date
            today = date.today()
            
            # Сначала точное совпадение (только активные сотрудники с действительными документами)
            employees = []
            all_employees = Employee.select().where(
                (Employee.full_name.contains(query)) & 
                (Employee.termination_date.is_null())
            )
            
            for emp in all_employees:
                # Проверяем сроки документов
                valid = True
                
                # Проверка УЧО (действует 5 лет)
                if emp.guard_license_date:
                    guard_expiry = emp.guard_license_date.replace(year=emp.guard_license_date.year + 5)
                    if guard_expiry < today:
                        valid = False
                
                # Проверка медкомиссии (действует 1 год)
                if emp.medical_exam_date:
                    medical_expiry = emp.medical_exam_date.replace(year=emp.medical_exam_date.year + 1)
                    if medical_expiry < today:
                        valid = False
                
                # Проверка периодической проверки (действует 1 год)
                if emp.periodic_check_date:
                    periodic_expiry = emp.periodic_check_date.replace(year=emp.periodic_check_date.year + 1)
                    if periodic_expiry < today:
                        valid = False
                
                if valid:
                    employees.append(emp)
            
            # Если не найдено, ищем без учета регистра
            if not employees:
                all_employees = Employee.select().where(
                    (Employee.full_name.contains(query.lower()) | Employee.full_name.contains(query.upper()) | Employee.full_name.contains(query.title())) &
                    (Employee.termination_date.is_null())
                )
                
                for emp in all_employees:
                    # Проверяем сроки документов
                    valid = True
                    
                    if emp.guard_license_date:
                        guard_expiry = emp.guard_license_date.replace(year=emp.guard_license_date.year + 5)
                        if guard_expiry < today:
                            valid = False
                    
                    if emp.medical_exam_date:
                        medical_expiry = emp.medical_exam_date.replace(year=emp.medical_exam_date.year + 1)
                        if medical_expiry < today:
                            valid = False
                    
                    if emp.periodic_check_date:
                        periodic_expiry = emp.periodic_check_date.replace(year=emp.periodic_check_date.year + 1)
                        if periodic_expiry < today:
                            valid = False
                    
                    if valid:
                        employees.append(emp)
            search_results.controls.clear()
            if employees:
                for emp in employees[:5]:
                    search_results.controls.append(
                        ft.ListTile(title=ft.Text(emp.full_name), on_click=lambda e, employee=emp: select_employee(employee))
                    )
                search_results.visible = True
            else:
                search_results.controls.append(ft.Text("Сотрудник не найден", color=ft.Colors.ERROR))
                search_results.visible = True
        except:
            pass
        finally:
            if not db.is_closed():
                db.close()
        page.update()
    
    def select_employee(employee):
        employee_search.value = employee.full_name
        search_results.visible = False
        page.update()
    
    def search_objects(query):
        if not query or len(query) < 2:
            object_search_results.visible = False
            page.update()
            return
        try:
            if db.is_closed():
                db.connect()
            # Сначала точное совпадение
            objects = list(Object.select().where(Object.name.contains(query)))
            # Если не найдено, ищем без учета регистра
            if not objects:
                objects = list(Object.select().where(Object.name.contains(query.lower()) | Object.name.contains(query.upper()) | Object.name.contains(query.title())))
            object_search_results.controls.clear()
            if objects:
                for obj in objects[:5]:
                    object_search_results.controls.append(
                        ft.ListTile(title=ft.Text(obj.name), on_click=lambda e, object_item=obj: select_object(object_item))
                    )
                object_search_results.visible = True
            else:
                object_search_results.controls.append(ft.Text("Объект не найден", color=ft.Colors.ERROR))
                object_search_results.visible = True
        except:
            pass
        finally:
            if not db.is_closed():
                db.close()
        page.update()
    
    def select_object(obj):
        object_search.value = obj.name
        object_search_results.visible = False
        hourly_rate_display.value = f"Почасовая ставка: {float(obj.hourly_rate):.2f} ₽"
        address_display.value = f"Адрес: {obj.address or 'не указан'}"
        page.update()
    
    def setup_add_shift_form():
        employee_search.value = ""
        object_search.value = ""
        hours_dropdown.value = "12"
        search_results.visible = False
        object_search_results.visible = False
        hourly_rate_display.value = "Почасовая ставка: не выбрано"
        address_display.value = "Адрес: не выбрано"
        
        add_shift_dialog.content.controls = [
            ft.Text(f"Дата: {current_shift_date.strftime('%d.%m.%Y')}", weight="bold"),
            employee_search,
            search_results,
            object_search,
            object_search_results,
            hours_dropdown,
            address_display,
            hourly_rate_display
        ]
    
    def save_new_shift():
        if not employee_search.value or not object_search.value or not hours_dropdown.value:
            return
        
        try:
            if db.is_closed():
                db.connect()
            
            employee = Employee.get(Employee.full_name == employee_search.value)
            obj = Object.get(Object.name == object_search.value)
            
            Assignment.create(
                employee=employee,
                object=obj,
                date=current_shift_date,
                hours=int(hours_dropdown.value),
                hourly_rate=obj.hourly_rate
            )
            
            salary_increase = float(obj.hourly_rate) * int(hours_dropdown.value)
            new_salary = float(employee.salary) + salary_increase
            new_hours = employee.hours_worked + int(hours_dropdown.value)
            
            employee.salary = new_salary
            employee.hours_worked = new_hours
            employee.save()
            
            close_add_shift_dialog()
            update_calendar()
            show_shifts_for_date(current_shift_date)
            
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
        finally:
            if not db.is_closed():
                db.close()
    
    # Добавляем диалоги в overlay страницы
    if edit_dialog not in page.overlay:
        page.overlay.append(edit_dialog)
    if delete_confirm_dialog not in page.overlay:
        page.overlay.append(delete_confirm_dialog)
    if add_shift_dialog not in page.overlay:
        page.overlay.append(add_shift_dialog)
    
    return shifts_content, shifts_dialog