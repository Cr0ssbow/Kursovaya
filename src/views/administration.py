import flet as ft
from views.settings import manage_companies_dialog
from auth.auth import AuthManager

def administration_page(page: ft.Page = None):
    """Страница администрирования"""
    auth_manager = AuthManager()
    
    def manage_users_dialog(e):
        users_list = ft.Column([], scroll=ft.ScrollMode.AUTO)
        
        def refresh_users():
            users_list.controls.clear()
            for user in auth_manager.get_all_users():
                employee_info = ""
                if user.guard_employee:
                    employee_info = f" (Охранник: {user.guard_employee.full_name})"
                elif user.chief_employee:
                    employee_info = f" (Начальник: {user.chief_employee.full_name})"
                elif user.office_employee:
                    employee_info = f" (Офис: {user.office_employee.full_name})"
                
                users_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"Логин: {user.username}{employee_info}"),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Удалить",
                                        on_click=lambda e, uid=user.id: delete_user(uid)
                                    ) if user.username != "Admin" else ft.Container()
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Роль: {user.role}"),
                                ft.Text(f"Доступ: {user.allowed_pages}", size=12, color=ft.Colors.GREY)
                            ]),
                            padding=10,
                            on_click=lambda e, u=user: edit_user(u)
                        )
                    )
                )
            page.update()
        
        def delete_user(user_id):
            if auth_manager.delete_user(user_id):
                refresh_users()
        
        def edit_user(user):
            username_field = ft.TextField(label="Логин", value=user.username, width=200)
            password_field = ft.TextField(label="Новый пароль (оставьте пустым для сохранения)", password=True, width=300)
            role_dropdown = ft.Dropdown(
                label="Роль",
                options=[ft.dropdown.Option("user"), ft.dropdown.Option("Admin")],
                value=user.role,
                width=200
            )
            
            # Поиск сотрудников
            employees = auth_manager.get_all_employees()
            selected_employee = {"id": None, "type": None}
            
            # Определяем текущего сотрудника
            current_employee_text = ""
            if user.guard_employee:
                selected_employee["id"] = user.guard_employee.id
                selected_employee["type"] = "guard"
                current_employee_text = f"{user.guard_employee.full_name} (guard)"
            elif user.chief_employee:
                selected_employee["id"] = user.chief_employee.id
                selected_employee["type"] = "chief"
                current_employee_text = f"{user.chief_employee.full_name} (chief)"
            elif user.office_employee:
                selected_employee["id"] = user.office_employee.id
                selected_employee["type"] = "office"
                current_employee_text = f"{user.office_employee.full_name} (office)"
            
            employee_search = ft.TextField(
                label="Поиск сотрудника",
                value=current_employee_text,
                width=300,
                on_change=lambda e: update_employee_list(e.control.value)
            )
            
            employee_list = ft.Column([], height=100, scroll=ft.ScrollMode.AUTO)
            
            def update_employee_list(search_text):
                employee_list.controls.clear()
                if search_text and search_text != current_employee_text:
                    filtered = [(emp_id, name, emp_type) for emp_id, name, emp_type in employees 
                               if search_text.lower() in name.lower()]
                    for emp_id, name, emp_type in filtered[:5]:
                        employee_list.controls.append(
                            ft.TextButton(
                                text=f"{name} ({emp_type})",
                                on_click=lambda e, eid=emp_id, etype=emp_type, ename=name: select_employee(eid, etype, ename)
                            )
                        )
                page.update()
            
            def select_employee(emp_id, emp_type, emp_name):
                selected_employee["id"] = emp_id
                selected_employee["type"] = emp_type
                employee_search.value = f"{emp_name} ({emp_type})"
                employee_list.controls.clear()
                page.update()
            
            # Доступные страницы
            pages = [
                ("home", "Главная"),
                ("employees", "Сотрудники охраны"),
                ("chief_employees", "Начальники охраны"),
                ("office_employees", "Офисные сотрудники"),
                ("objects", "Объекты"),
                ("calendar", "Календарь смен"),
                ("statistics", "Статистика"),
                ("notes", "Заметки"),
                ("terminated", "Уволенные"),
                ("discarded_cards", "Списанные карточки"),
                ("administration", "Администрирование")
            ]
            
            user_pages = user.allowed_pages.split(',') if user.allowed_pages else []
            page_checkboxes = []
            for page_key, page_name in pages:
                checkbox = ft.Checkbox(label=page_name, value=page_key in user_pages, data=page_key)
                page_checkboxes.append(checkbox)
            
            def save_user(e):
                selected_pages = [cb.data for cb in page_checkboxes if cb.value]
                allowed_pages = ','.join(selected_pages)
                
                if auth_manager.update_user(
                    user.id,
                    username_field.value,
                    password_field.value if password_field.value else None,
                    role_dropdown.value,
                    selected_employee["id"],
                    selected_employee["type"],
                    allowed_pages
                ):
                    page.close(edit_dialog)
                    refresh_users()
            
            content_column = ft.Column([
                username_field,
                password_field,
                role_dropdown,
                employee_search,
                employee_list,
                ft.Text("Доступные страницы:", weight="bold"),
                ft.Column(page_checkboxes, scroll=ft.ScrollMode.AUTO, height=200)
            ], tight=True, scroll=ft.ScrollMode.AUTO)
            
            edit_dialog = ft.AlertDialog(
                title=ft.Text(f"Редактировать пользователя: {user.username}"),
                content=ft.Container(content=content_column, width=400, height=500),
                actions=[ft.TextButton("Сохранить", on_click=save_user), ft.TextButton("Отмена", on_click=lambda e: page.close(edit_dialog))]
            )
            page.overlay.append(edit_dialog)
            page.update()
            page.open(edit_dialog)
        
        def add_user():
            username_field = ft.TextField(label="Логин", width=200)
            password_field = ft.TextField(label="Пароль", password=True, width=200)
            roles = auth_manager.get_all_roles()
            role_options = [ft.dropdown.Option(role.name) for role in roles]
            role_dropdown = ft.Dropdown(
                label="Роль",
                options=role_options,
                value="user",
                width=200
            )
            
            # Поиск сотрудников
            employees = auth_manager.get_all_employees()
            selected_employee = {"id": None, "type": None}
            
            employee_search = ft.TextField(
                label="Поиск сотрудника (введите ФИО)",
                width=300,
                on_change=lambda e: update_employee_list(e.control.value)
            )
            
            employee_list = ft.Column([], height=100, scroll=ft.ScrollMode.AUTO)
            
            def update_employee_list(search_text):
                employee_list.controls.clear()
                if search_text:
                    filtered = [(emp_id, name, emp_type) for emp_id, name, emp_type in employees 
                               if search_text.lower() in name.lower()]
                    for emp_id, name, emp_type in filtered[:5]:  # Показываем только 5 результатов
                        employee_list.controls.append(
                            ft.TextButton(
                                text=f"{name} ({emp_type})",
                                on_click=lambda e, eid=emp_id, etype=emp_type, ename=name: select_employee(eid, etype, ename)
                            )
                        )
                page.update()
            
            def select_employee(emp_id, emp_type, emp_name):
                selected_employee["id"] = emp_id
                selected_employee["type"] = emp_type
                employee_search.value = f"{emp_name} ({emp_type})"
                employee_list.controls.clear()
                page.update()
            
            # Доступные страницы
            pages = [
                ("home", "Главная"),
                ("employees", "Сотрудники охраны"),
                ("chief_employees", "Начальники охраны"),
                ("office_employees", "Офисные сотрудники"),
                ("objects", "Объекты"),
                ("calendar", "Календарь смен"),
                ("statistics", "Статистика"),
                ("notes", "Заметки"),
                ("terminated", "Уволенные"),
                ("discarded_cards", "Списанные карточки"),
                ("administration", "Администрирование")
            ]
            
            page_checkboxes = []
            for page_key, page_name in pages:
                checkbox = ft.Checkbox(label=page_name, value=page_key=="home", data=page_key)
                page_checkboxes.append(checkbox)
            
            def save_user(e):
                selected_pages = [cb.data for cb in page_checkboxes if cb.value]
                allowed_pages = ','.join(selected_pages)
                
                employee_id = selected_employee["id"]
                employee_type = selected_employee["type"]
                
                if auth_manager.create_user(
                    username_field.value, 
                    password_field.value, 
                    role_dropdown.value,
                    employee_id,
                    employee_type,
                    allowed_pages
                ):
                    page.close(add_dialog)
                    refresh_users()
            
            content_column = ft.Column([
                username_field, 
                password_field, 
                role_dropdown,
                employee_search,
                employee_list,
                ft.Text("Доступные страницы:", weight="bold"),
                ft.Column(page_checkboxes, scroll=ft.ScrollMode.AUTO, height=200)
            ], tight=True, scroll=ft.ScrollMode.AUTO)
            
            add_dialog = ft.AlertDialog(
                title=ft.Text("Добавить пользователя"),
                content=ft.Container(content=content_column, width=400, height=500),
                actions=[ft.TextButton("Сохранить", on_click=save_user), ft.TextButton("Отмена", on_click=lambda e: page.close(add_dialog))]
            )
            page.overlay.append(add_dialog)
            page.update()
            page.open(add_dialog)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Управление пользователями"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.ElevatedButton("Добавить пользователя", on_click=lambda e: add_user()),
                        ft.ElevatedButton("Управление ролями", on_click=lambda e: manage_roles_dialog(e))
                    ]),
                    users_list
                ]),
                width=500,
                height=400
            ),
            actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(dialog))]
        )
        
        page.overlay.append(dialog)
        refresh_users()
        page.open(dialog)
    
    def manage_roles_dialog(e):
        roles_list = ft.Column([], scroll=ft.ScrollMode.AUTO)
        
        def refresh_roles():
            roles_list.controls.clear()
            for role in auth_manager.get_all_roles():
                roles_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"Название: {role.name}", weight="bold"),
                                    ft.Text(f"Описание: {role.description or 'Нет'}", size=12)
                                ], expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Удалить",
                                    on_click=lambda e, rid=getattr(role, 'id', None): delete_role(rid)
                                ) if role.name not in ["Admin", "user"] and hasattr(role, 'id') else ft.Container()
                            ]),
                            padding=10
                        )
                    )
                )
            page.update()
        
        def delete_role(role_id):
            if auth_manager.delete_role(role_id):
                refresh_roles()
        
        def add_role():
            name_field = ft.TextField(label="Название роли", width=200)
            description_field = ft.TextField(label="Описание", width=300)
            
            def save_role(e):
                if auth_manager.create_role(name_field.value, description_field.value):
                    page.close(add_dialog)
                    refresh_roles()
            
            add_dialog = ft.AlertDialog(
                title=ft.Text("Добавить роль"),
                content=ft.Column([name_field, description_field], tight=True),
                actions=[ft.TextButton("Сохранить", on_click=save_role), ft.TextButton("Отмена", on_click=lambda e: page.close(add_dialog))]
            )
            page.overlay.append(add_dialog)
            page.update()
            page.open(add_dialog)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Управление ролями"),
            content=ft.Container(
                content=ft.Column([
                    ft.ElevatedButton("Добавить роль", on_click=lambda e: add_role()),
                    roles_list
                ]),
                width=400,
                height=300
            ),
            actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(dialog))]
        )
        
        page.overlay.append(dialog)
        refresh_roles()
        page.open(dialog)
    
    return ft.Column([
        ft.Text("Администрирование", size=24, weight="bold"),
        ft.Divider(),
        ft.Text("Управление компаниями", size=18, weight="bold"),
        ft.ElevatedButton(
            "Управление компаниями",
            icon=ft.Icons.BUSINESS,
            on_click=lambda e: manage_companies_dialog(page),
        ),
        ft.Divider(),
        ft.Text("Управление пользователями", size=18, weight="bold"),
        ft.ElevatedButton(
            "Управление пользователями",
            icon=ft.Icons.PEOPLE,
            on_click=manage_users_dialog,
        )
    ], spacing=10, expand=True)