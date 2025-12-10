import flet as ft
from database.models import UserLog, User, db
from datetime import datetime, date

def logs_page(page: ft.Page = None) -> ft.Column:
    """Страница просмотра логов действий пользователей"""
    
    search_value = ""
    current_page = 0
    page_size = 20
    selected_user = "Все пользователи"
    selected_action = "Все действия"
    date_from = None
    date_to = None
    
    logs_list = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        height=500
    )
    
    # Поля фильтрации
    search_field = ft.TextField(
        label="Поиск по описанию",
        width=300,
        dense=True
    )
    
    user_dropdown = ft.Dropdown(
        label="Пользователь",
        width=200,
        value="Все пользователи",
        dense=True
    )
    
    action_dropdown = ft.Dropdown(
        label="Действие",
        width=250,
        value="Все действия",
        dense=True,
        options=[
            ft.dropdown.Option("Все действия"),
            ft.dropdown.Option("Вход"),
            ft.dropdown.Option("Выход"),
            ft.dropdown.Option("Создание"),
            ft.dropdown.Option("Редактирование"),
            ft.dropdown.Option("Увольнение"),
            ft.dropdown.Option("Восстановление"),
            ft.dropdown.Option("Удаление"),
        ]
    )
    
    date_from_field = ft.TextField(
        label="Дата с (дд.мм.гггг)",
        width=150,
        max_length=10,
        dense=True
    )
    
    date_to_field = ft.TextField(
        label="Дата по (дд.мм.гггг)",
        width=150,
        max_length=10,
        dense=True
    )
    
    page_info = ft.Text("Страница 1 из 1")
    prev_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK)
    next_btn = ft.IconButton(icon=ft.Icons.ARROW_FORWARD)
    
    def format_date_input(e):
        """Форматирует ввод даты"""
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
    
    date_from_field.on_change = format_date_input
    date_to_field.on_change = format_date_input
    
    def load_users():
        """Загружает список пользователей для фильтра"""
        try:
            if db.is_closed():
                db.connect()
            
            users = ["Все пользователи"]
            for user in User.select():
                users.append(user.username)
            
            user_dropdown.options = [ft.dropdown.Option(u) for u in users]
            
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
        finally:
            if not db.is_closed():
                db.close()
    
    def get_logs():
        """Получает логи с учетом фильтров"""
        try:
            if db.is_closed():
                db.connect()
            
            query = UserLog.select().join(User)
            
            # Фильтр по пользователю
            if selected_user != "Все пользователи":
                query = query.where(User.username == selected_user)
            
            # Фильтр по действию
            if selected_action != "Все действия":
                query = query.where(UserLog.action.contains(selected_action))
            
            # Фильтр по описанию
            if search_value:
                query = query.where(UserLog.description.contains(search_value))
            
            # Фильтр по датам
            if date_from:
                query = query.where(UserLog.created_at >= date_from)
            if date_to:
                # Добавляем время до конца дня
                date_to_end = datetime.combine(date_to, datetime.max.time())
                query = query.where(UserLog.created_at <= date_to_end)
            
            # Сортировка по дате (новые сначала)
            query = query.order_by(UserLog.created_at.desc())
            
            return list(query)
            
        except Exception as e:
            print(f"Ошибка получения логов: {e}")
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def refresh_list():
        """Обновляет список логов"""
        all_logs = get_logs()
        
        # Пагинация
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        page_logs = all_logs[start_idx:end_idx]
        
        logs_list.controls.clear()
        
        for log in page_logs:
            # Определяем цвет в зависимости от типа действия
            color = None
            if "Удаление" in log.action:
                color = ft.Colors.RED
            elif "Создание" in log.action:
                color = ft.Colors.GREEN
            elif "Редактирование" in log.action:
                color = ft.Colors.BLUE
            elif "Восстановление" in log.action:
                color = ft.Colors.ORANGE
            
            logs_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(
                                log.created_at.strftime("%d.%m.%Y %H:%M:%S"),
                                size=12,
                                width=130
                            ),
                            ft.Text(
                                log.user.username,
                                size=12,
                                weight="bold",
                                width=100
                            ),
                            ft.Text(
                                log.action,
                                size=12,
                                color=color,
                                weight="bold",
                                width=200
                            ),
                            ft.Text(
                                log.description or "",
                                size=12,
                                expand=True
                            )
                        ], spacing=10)
                    ], spacing=2),
                    padding=ft.padding.all(8),
                    border=ft.border.all(1),
                    border_radius=5,
                    margin=ft.margin.only(bottom=2)
                )
            )
        
        # Обновляем пагинацию
        total_pages = (len(all_logs) + page_size - 1) // page_size if all_logs else 1
        prev_btn.disabled = current_page == 0
        next_btn.disabled = current_page >= total_pages - 1
        page_info.value = f"Страница {current_page + 1} из {max(1, total_pages)} (всего записей: {len(all_logs)})"
        
        if page:
            page.update()
    
    def on_search_change(e):
        nonlocal search_value, current_page
        search_value = e.control.value.strip()
        current_page = 0
        refresh_list()
    
    def on_user_change(e):
        nonlocal selected_user, current_page
        selected_user = e.control.value
        current_page = 0
        refresh_list()
    
    def on_action_change(e):
        nonlocal selected_action, current_page
        selected_action = e.control.value
        current_page = 0
        refresh_list()
    
    def on_date_from_change(e):
        nonlocal date_from, current_page
        try:
            if e.control.value.strip():
                date_from = datetime.strptime(e.control.value.strip(), "%d.%m.%Y").date()
            else:
                date_from = None
            current_page = 0
            refresh_list()
        except ValueError:
            pass
    
    def on_date_to_change(e):
        nonlocal date_to, current_page
        try:
            if e.control.value.strip():
                date_to = datetime.strptime(e.control.value.strip(), "%d.%m.%Y").date()
            else:
                date_to = None
            current_page = 0
            refresh_list()
        except ValueError:
            pass
    
    def prev_page_click(e):
        nonlocal current_page
        if current_page > 0:
            current_page -= 1
            refresh_list()
    
    def next_page_click(e):
        nonlocal current_page
        current_page += 1
        refresh_list()
    
    def clear_filters(e):
        """Очищает все фильтры"""
        nonlocal search_value, selected_user, selected_action, date_from, date_to, current_page
        
        search_value = ""
        selected_user = "Все пользователи"
        selected_action = "Все действия"
        date_from = None
        date_to = None
        current_page = 0
        
        search_field.value = ""
        user_dropdown.value = "Все пользователи"
        action_dropdown.value = "Все действия"
        date_from_field.value = ""
        date_to_field.value = ""
        
        refresh_list()
    
    # Привязываем обработчики
    search_field.on_change = on_search_change
    user_dropdown.on_change = on_user_change
    action_dropdown.on_change = on_action_change
    date_from_field.on_change = on_date_from_change
    date_to_field.on_change = on_date_to_change
    prev_btn.on_click = prev_page_click
    next_btn.on_click = next_page_click
    
    # Загружаем данные
    load_users()
    refresh_list()
    
    return ft.Column([
        ft.Text("Логи действий пользователей", size=24, weight="bold"),
        ft.Divider(),
        
        # Фильтры
        ft.Row([
            search_field,
            user_dropdown,
            action_dropdown,
        ], spacing=10),
        
        ft.Row([
            date_from_field,
            date_to_field,
            ft.ElevatedButton(
                "Очистить фильтры",
                icon=ft.Icons.CLEAR,
                on_click=clear_filters
            )
        ], spacing=10),
        
        # Заголовки колонок
        ft.Container(
            content=ft.Row([
                ft.Text("Дата и время", size=12, weight="bold", width=130),
                ft.Text("Пользователь", size=12, weight="bold", width=100),
                ft.Text("Действие", size=12, weight="bold", width=200),
                ft.Text("Описание", size=12, weight="bold", expand=True)
            ], spacing=10),
            padding=ft.padding.all(8),
            border_radius=5
        ),
        
        # Список логов
        ft.Container(
            content=logs_list,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            padding=10,
            expand=True,
        ),
        
        # Пагинация
        ft.Row([
            prev_btn,
            page_info,
            next_btn
        ], alignment=ft.MainAxisAlignment.CENTER),
        
    ], spacing=10, expand=True)