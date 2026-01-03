import flet as ft
from database.models import Employee, db
from datetime import datetime

def format_date(date):
    """Форматирует дату в строку дд.мм.гггг"""
    return date.strftime("%d.%m.%Y") if date else "Не указано"

def terminated_page(page: ft.Page = None) -> ft.Column:
    search_value = ""
    selected_companies = set()  # Множество выбранных компаний
    
    # Диалог действий с сотрудником
    actions_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Действия с сотрудником"),
        content=ft.Column([], height=200),
        actions=[
            ft.TextButton("Вернуть", on_click=lambda e: restore_employee(current_employee), style=ft.ButtonStyle(color=ft.Colors.GREEN)),
            ft.TextButton("Редактировать", on_click=lambda e: show_edit_termination(current_employee)),
            ft.TextButton("Отмена", on_click=lambda e: close_actions_dialog())
        ]
    )
    
    # Диалог редактирования увольнения
    edit_termination_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Редактировать увольнение"),
        content=ft.Column([], height=150),
        actions=[
            ft.TextButton("Сохранить", on_click=lambda e: save_termination_changes()),
            ft.TextButton("Отмена", on_click=lambda e: close_edit_termination_dialog())
        ]
    )
    
    # Диалог подтверждения удаления
    delete_confirmation_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Подтверждение удаления"),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Удалить", on_click=lambda e: confirm_delete_employee(), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Отмена", on_click=lambda e: close_delete_confirmation())
        ]
    )
    
    def format_date_input(e):
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
            if page:
                page.update()
    
    edit_termination_date = ft.TextField(label="Дата увольнения", width=200, on_change=format_date_input, max_length=10)
    edit_termination_reason = ft.TextField(label="Причина увольнения", width=300, multiline=True)
    current_employee = None
    
    def get_employee_companies(employee):
        """Получает все компании сотрудника"""
        try:
            if db.is_closed():
                db.connect()
            
            from database.models import Company, EmployeeCompany, GuardEmployee, ChiefEmployee, OfficeEmployee
            
            companies = []
            if isinstance(employee, GuardEmployee):
                company_relations = EmployeeCompany.select().where(EmployeeCompany.guard_employee == employee)
            elif isinstance(employee, ChiefEmployee):
                company_relations = EmployeeCompany.select().where(EmployeeCompany.chief_employee == employee)
            elif isinstance(employee, OfficeEmployee):
                company_relations = EmployeeCompany.select().where(EmployeeCompany.office_employee == employee)
            else:
                return ["Легион"]
            
            for relation in company_relations:
                companies.append(relation.company.name)
            
            return companies if companies else ["Легион"]
        except:
            return ["Легион"]
        finally:
            if not db.is_closed():
                db.close()
    
    def show_employee_actions(employee):
        nonlocal current_employee
        current_employee = employee
        
        companies = get_employee_companies(employee)
        companies_text = ", ".join(companies)
        
        actions_dialog.title.value = f"Действия: {employee.full_name}"
        actions_dialog.content.controls = [
            ft.Text(f"Сотрудник: {employee.full_name}", weight="bold"),
            ft.Text(f"Дата увольнения: {format_date(employee.termination_date)}"),
            ft.Text(f"Причина: {getattr(employee, 'termination_reason', '') or 'Не указана'}"),
            ft.Text(f"Компании: {companies_text}", size=16),
            ft.Divider(),
        ]
        
        actions_dialog.open = True
        if page and actions_dialog not in page.overlay:
            page.overlay.append(actions_dialog)
        if page:
            page.update()
    
    def close_actions_dialog():
        actions_dialog.open = False
        if page:
            page.update()
    
    def show_edit_termination(employee):
        edit_termination_date.value = format_date(employee.termination_date)
        edit_termination_reason.value = getattr(employee, 'termination_reason', '') or ''
        
        edit_termination_dialog.content.controls = [
            edit_termination_date,
            edit_termination_reason
        ]
        
        close_actions_dialog()
        edit_termination_dialog.open = True
        if page and edit_termination_dialog not in page.overlay:
            page.overlay.append(edit_termination_dialog)
        if page:
            page.update()
    
    def close_edit_termination_dialog():
        edit_termination_dialog.open = False
        if page:
            page.update()
    
    def save_termination_changes():
        try:
            if db.is_closed():
                db.connect()
            
            from datetime import datetime
            termination_date = datetime.strptime(edit_termination_date.value, "%d.%m.%Y").date()
            
            current_employee.termination_date = termination_date
            current_employee.termination_reason = edit_termination_reason.value or None
            current_employee.save()
            
            # Логирование
            if page and hasattr(page, 'auth_manager'):
                page.auth_manager.log_action("Редактирование данных увольнения", f"Отредактированы данные увольнения сотрудника: {current_employee.full_name}")
            
            close_edit_termination_dialog()
            refresh_list()
        except Exception as ex:
            print(f"Ошибка сохранения: {ex}")
        finally:
            if not db.is_closed():
                db.close()
    
    def show_delete_confirmation(employee):
        delete_confirmation_dialog.content.value = f"Вы уверены, что хотите окончательно удалить сотрудника {employee.full_name}?\n\nЭто действие нельзя отменить!"
        delete_confirmation_dialog.open = True
        if page and delete_confirmation_dialog not in page.overlay:
            page.overlay.append(delete_confirmation_dialog)
        if page:
            page.update()
    
    def close_delete_confirmation():
        delete_confirmation_dialog.open = False
        if page:
            page.update()
    
    def confirm_delete_employee():
        try:
            if db.is_closed():
                db.connect()
            
            from database.models import User, EmployeeCompany, GuardEmployee, ChiefEmployee, OfficeEmployee
            
            employee_name = current_employee.full_name
            
            # Удаляем связанных пользователей
            if isinstance(current_employee, GuardEmployee):
                User.delete().where(User.guard_employee == current_employee).execute()
                EmployeeCompany.delete().where(EmployeeCompany.guard_employee == current_employee).execute()
            elif isinstance(current_employee, ChiefEmployee):
                User.delete().where(User.chief_employee == current_employee).execute()
                EmployeeCompany.delete().where(EmployeeCompany.chief_employee == current_employee).execute()
            elif isinstance(current_employee, OfficeEmployee):
                User.delete().where(User.office_employee == current_employee).execute()
                EmployeeCompany.delete().where(EmployeeCompany.office_employee == current_employee).execute()
            
            # Теперь удаляем сотрудника
            current_employee.delete_instance()
            
            # Логирование
            if page and hasattr(page, 'auth_manager'):
                page.auth_manager.log_action("Удаление сотрудника", f"Окончательно удален сотрудник: {employee_name}")
            
            close_delete_confirmation()
            close_actions_dialog()
            refresh_list()
        except Exception as ex:
            print(f"Ошибка удаления: {ex}")
        finally:
            if not db.is_closed():
                db.close()
    
    def delete_employee_permanently(employee):
        close_actions_dialog()
        show_delete_confirmation(employee)
    
    def get_terminated_employees():
        """Получает список уволенных сотрудников"""
        try:
            if db.is_closed():
                db.connect()
            
            from database.models import GuardEmployee, ChiefEmployee, OfficeEmployee, Company, EmployeeCompany
            
            # Фильтр по компаниям
            companies = []
            all_companies = list(Company.select())
            
            for company in all_companies:
                attr_name = f"show_{company.name.lower().replace(' ', '_')}"
                if getattr(terminated_page, attr_name, True):
                    companies.append(company.name)
            
            # Получаем всех уволенных сотрудников
            all_terminated = []
            
            # Охранники
            guard_query = GuardEmployee.select().where(GuardEmployee.termination_date.is_null(False))
            if search_value:
                guard_query = guard_query.where(GuardEmployee.full_name.contains(search_value))
            
            # Применяем фильтр по компаниям для охранников
            if len(companies) < len(all_companies) and len(companies) > 0:
                company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
                employee_ids = [ec.guard_employee_id for ec in EmployeeCompany.select().where(EmployeeCompany.company_id.in_(company_ids))]
                guard_query = guard_query.where(GuardEmployee.id.in_(employee_ids))
            elif len(companies) == 0:
                guard_query = guard_query.where(False)
            
            all_terminated.extend(list(guard_query))
            
            # Начальники
            chief_query = ChiefEmployee.select().where(ChiefEmployee.termination_date.is_null(False))
            if search_value:
                chief_query = chief_query.where(ChiefEmployee.full_name.contains(search_value))
            
            # Применяем фильтр по компаниям для начальников
            if len(companies) < len(all_companies) and len(companies) > 0:
                company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
                employee_ids = [ec.chief_employee_id for ec in EmployeeCompany.select().where(EmployeeCompany.company_id.in_(company_ids))]
                chief_query = chief_query.where(ChiefEmployee.id.in_(employee_ids))
            elif len(companies) == 0:
                chief_query = chief_query.where(False)
            
            all_terminated.extend(list(chief_query))
            
            # Офисные сотрудники
            office_query = OfficeEmployee.select().where(OfficeEmployee.termination_date.is_null(False))
            if search_value:
                office_query = office_query.where(OfficeEmployee.full_name.contains(search_value))
            
            # Применяем фильтр по компаниям для офисных сотрудников
            if len(companies) < len(all_companies) and len(companies) > 0:
                company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
                employee_ids = [ec.office_employee_id for ec in EmployeeCompany.select().where(EmployeeCompany.company_id.in_(company_ids))]
                office_query = office_query.where(OfficeEmployee.id.in_(employee_ids))
            elif len(companies) == 0:
                office_query = office_query.where(False)
            
            all_terminated.extend(list(office_query))
            
            # Сортируем по имени
            all_terminated.sort(key=lambda emp: emp.full_name)
            
            return all_terminated
        except:
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def restore_employee(employee):
        """Восстанавливает сотрудника (убирает дату увольнения)"""
        try:
            if db.is_closed():
                db.connect()
            employee.termination_date = None
            employee.termination_reason = None
            employee.save()
            
            # Логирование
            if page and hasattr(page, 'auth_manager'):
                page.auth_manager.log_action("Восстановление сотрудника", f"Восстановлен сотрудник: {employee.full_name}")
            
            close_actions_dialog()
            refresh_list()
        except:
            pass
        finally:
            if not db.is_closed():
                db.close()
    
    def refresh_list():
        """Обновляет список уволенных сотрудников"""
        terminated_employees = get_terminated_employees()
        terminated_list.controls.clear()
        
        for employee in terminated_employees:
            companies = get_employee_companies(employee)
            companies_text = ", ".join(companies)
            
            terminated_list.controls.append(
                ft.ListTile(
                    title=ft.Text(employee.full_name, weight="bold"),
                    subtitle=ft.Text(f"Дата: {format_date(employee.termination_date)} | Причина: {getattr(employee, 'termination_reason', '') or 'Не указана'}"),
                    trailing=ft.Text(companies_text),
                    on_click=lambda e, emp=employee: show_employee_actions(emp)
                )
            )
        
        if page:
            page.update()
    
    def on_search_change(e):
        nonlocal search_value
        search_value = e.control.value.strip()
        refresh_list()
    
    def create_company_filter_dropdown():
        """Создает dropdown с чекбоксами для фильтрации компаний"""
        from database.models import Company
        
        # Инициализируем фильтры для всех компаний
        companies = list(Company.select())
        for company in companies:
            attr_name = f"show_{company.name.lower().replace(' ', '_')}"
            if not hasattr(terminated_page, attr_name):
                setattr(terminated_page, attr_name, True)
        
        def update_company_filter(company_name, value):
            attr_name = f"show_{company_name.lower().replace(' ', '_')}"
            setattr(terminated_page, attr_name, value)
            refresh_list()
            
            # Обновляем текст кнопки
            selected = []
            for company in companies:
                attr_name = f"show_{company.name.lower().replace(' ', '_')}"
                if getattr(terminated_page, attr_name, True):
                    selected.append(company.name)
            
            if len(selected) == len(companies):
                button_text.value = "Все ЧОПЫ"
            elif len(selected) == 0:
                button_text.value = "Нет ЧОПОВ"
            else:
                button_text.value = f"Выбрано: {len(selected)}"
            if page:
                page.update()
        
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
                value=getattr(terminated_page, attr_name, True),
                on_change=make_checkbox_handler(company.name)
            )
            
            menu_items.append(
                ft.PopupMenuItem(
                    content=checkbox,
                    on_click=lambda e, cb=checkbox: setattr(cb, 'value', not cb.value) or cb.on_change(type('Event', (), {'control': cb})())
                )
            )
        
        # Создаем текст кнопки отдельно для простого обновления
        button_text = ft.Text("Все ЧОПЫ", size=14)
        
        # Создаем кнопку с меню
        company_button = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Row([
                    button_text,
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=20)
                ], tight=True),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=8,
                width=180, 
                height=47,
            ),
            items=menu_items,
            tooltip="Фильтр по компаниям"
        )
        
        return company_button
    
    company_button = create_company_filter_dropdown()
    
    # Создаем список
    terminated_list = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        height=500
    )
    
    refresh_list()
    
    return ft.Column([
        ft.Text("Уволенные сотрудники", size=24, weight="bold"),
        ft.Divider(),
        ft.Row([
            ft.TextField(
                label="Поиск по ФИО",
                width=300,
                on_change=on_search_change,
                autofocus=False,
                dense=True,
            ),
            company_button,
        ], alignment=ft.MainAxisAlignment.START, spacing=20),
        ft.Container(
            content=terminated_list,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            padding=10,
            expand=True,
        ),
    ], spacing=10, expand=True)