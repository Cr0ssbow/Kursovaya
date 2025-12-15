import datetime
import flet as ft
from database.models import Employee, db
from datetime import date, timedelta
from views.settings import load_birthday_display_from_db

def home_page(page: ft.Page = None) -> ft.Column:
    # Поле поиска
    search_field = ft.TextField(
        label="Поиск сотрудника",
        hint_text="Введите ФИО для поиска",
        width=300,
        on_change=lambda e: update_containers(e.control.value)
    )
    
    def get_expiring_licenses(search_query=""):
        """Получает список сотрудников с истекающими УЧО (в течение 30 дней)"""
        try:
            if db.is_closed():
                db.connect()
            
            today = date.today()
            
            expiring = []
            min_days = 999
            for employee in Employee.select():
                if hasattr(employee, 'guard_license_date') and employee.guard_license_date:
                    # Фильтрация по поисковому запросу
                    if search_query and search_query.lower() not in employee.full_name.lower():
                        continue
                    # УЧО действует 5 лет
                    try:
                        expiry_date = employee.guard_license_date.replace(year=employee.guard_license_date.year + 5)
                    except ValueError:
                        # Обработка 29 февраля в невисокосном году
                        expiry_date = employee.guard_license_date.replace(year=employee.guard_license_date.year + 5, day=28)
                    days_left = (expiry_date - today).days
                    if days_left <= 90:  # Показываем истёкшие и истекающие в течение 90 дней
                        expiring.append((employee.full_name, expiry_date, days_left))
                        min_days = min(min_days, days_left)
            
            return expiring, min_days if expiring else 999
        except Exception as e:
            print(f"Ошибка при получении УЧО: {e}")
            return [], 999
        finally:
            if not db.is_closed():
                db.close()
    
    def get_expiring_medical(search_query=""):
        """Получает список сотрудников с истекающими медкомиссиями (в течение 30 дней)"""
        try:
            if db.is_closed():
                db.connect()
            
            today = date.today()
            
            expiring = []
            min_days = 999
            for employee in Employee.select():
                if hasattr(employee, 'medical_exam_date') and employee.medical_exam_date:
                    # Фильтрация по поисковому запросу
                    if search_query and search_query.lower() not in employee.full_name.lower():
                        continue
                    # Медкомиссия действует 1 год
                    try:
                        expiry_date = employee.medical_exam_date.replace(year=employee.medical_exam_date.year + 1)
                    except ValueError:
                        # Обработка 29 февраля в невисокосном году
                        expiry_date = employee.medical_exam_date.replace(year=employee.medical_exam_date.year + 1, day=28)
                    days_left = (expiry_date - today).days
                    if days_left <= 60:  # Показываем истёкшие и истекающие в течение 60 дней
                        expiring.append((employee.full_name, expiry_date, days_left))
                        min_days = min(min_days, days_left)
            
            return expiring, min_days if expiring else 999
        except Exception as e:
            print(f"Ошибка при получении медкомиссий: {e}")
            return [], 999
        finally:
            if not db.is_closed():
                db.close()
    
    def get_expiring_periodic_checks(search_query=""):
        """Получает список сотрудников с истекающими периодическими проверками (в течение 30 дней)"""
        try:
            if db.is_closed():
                db.connect()
            
            today = date.today()
            
            expiring = []
            min_days = 999
            for employee in Employee.select():
                if hasattr(employee, 'periodic_check_date') and employee.periodic_check_date:
                    # Фильтрация по поисковому запросу
                    if search_query and search_query.lower() not in employee.full_name.lower():
                        continue
                    # Периодическая проверка действует 1 год
                    try:
                        expiry_date = employee.periodic_check_date.replace(year=employee.periodic_check_date.year + 1)
                    except ValueError:
                        # Обработка 29 февраля в невисокосном году
                        expiry_date = employee.periodic_check_date.replace(year=employee.periodic_check_date.year + 1, day=28)
                    days_left = (expiry_date - today).days
                    if days_left <= 30:  # Показываем истёкшие и истекающие в течение 30 дней
                        expiring.append((employee.full_name, expiry_date, days_left))
                        min_days = min(min_days, days_left)
            
            return expiring, min_days if expiring else 999
        except Exception as e:
            print(f"Ошибка при получении периодических проверок: {e}")
            return [], 999
        finally:
            if not db.is_closed():
                db.close()
    
    def get_upcoming_birthdays(search_query=""):
        """Получает список сотрудников с днями рождения в ближайшие 7 дней"""
        try:
            if db.is_closed():
                db.connect()
            
            today = date.today()
            upcoming = []
            
            for employee in Employee.select():
                # Фильтрация по поисковому запросу
                if search_query and search_query.lower() not in employee.full_name.lower():
                    continue
                # Создаем дату дня рождения в текущем году
                try:
                    birthday_this_year = employee.birth_date.replace(year=today.year)
                except ValueError:
                    # Обработка 29 февраля в невисокосном году
                    birthday_this_year = employee.birth_date.replace(year=today.year, day=28)
                
                # Если день рождения уже прошел в этом году, берем следующий год
                if birthday_this_year < today:
                    try:
                        birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                    except ValueError:
                        # Обработка 29 февраля в невисокосном году
                        birthday_this_year = birthday_this_year.replace(year=today.year + 1, day=28)
                
                # Проверяем, попадает ли в ближайшие 7 дней
                days_until = (birthday_this_year - today).days
                if 0 <= days_until <= 7:
                    upcoming.append((employee.full_name, birthday_this_year, days_until))
            
            return sorted(upcoming, key=lambda x: x[2])
        except Exception as e:
            print(f"Ошибка при получении дней рождения: {e}")
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def get_license_color(min_days):
        """Определяет цвет контейнера УЧО"""
        if min_days <= 30:
            return ft.Colors.RED
        elif min_days <= 60:
            return ft.Colors.AMBER
        else:
            return ft.Colors.GREEN
    
    def get_medical_color(min_days):
        """Определяет цвет контейнера медкомиссий"""
        if min_days <= 20:
            return ft.Colors.RED
        elif min_days <= 40:
            return ft.Colors.AMBER
        else:
            return ft.Colors.GREEN
    
    def get_periodic_color(min_days):
        """Определяет цвет контейнера периодических проверок"""
        if min_days <= 10:
            return ft.Colors.RED
        elif min_days <= 20:
            return ft.Colors.AMBER
        else:
            return ft.Colors.GREEN
    
    def get_container_color(min_days):
        """Определяет цвет контейнера на основе минимального количества дней"""
        if min_days <= 1:
            return ft.Colors.RED
        elif min_days <= 7:
            return ft.Colors.AMBER
        else:
            return ft.Colors.GREEN
    
    # Получаем данные
    expiring_licenses, license_min_days = get_expiring_licenses()
    expiring_medical, medical_min_days = get_expiring_medical()
    expiring_periodic_checks, periodic_min_days = get_expiring_periodic_checks()
    upcoming_birthdays = get_upcoming_birthdays()
    birthday_min_days = min([days for _, _, days in upcoming_birthdays], default=999)
    
    # Контейнеры для обновления
    containers_row = ft.Row([], alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=15)
    
    def update_containers(search_query):
        """Обновляет контейнеры с учетом поискового запроса"""
        nonlocal expiring_licenses, license_min_days, expiring_medical, medical_min_days
        nonlocal expiring_periodic_checks, periodic_min_days, upcoming_birthdays, birthday_min_days
        
        # Получаем отфильтрованные данные
        expiring_licenses, license_min_days = get_expiring_licenses(search_query)
        expiring_medical, medical_min_days = get_expiring_medical(search_query)
        expiring_periodic_checks, periodic_min_days = get_expiring_periodic_checks(search_query)
        upcoming_birthdays = get_upcoming_birthdays(search_query)
        birthday_min_days = min([days for _, _, days in upcoming_birthdays], default=999)
        
        # Обновляем контейнеры
        containers_row.controls.clear()
        containers = [
            create_license_container(),
            create_medical_container(),
            create_periodic_container()
        ]
        
        # Проверяем настройку отображения дней рождения
        if load_birthday_display_from_db():
            containers.append(create_birthday_container())
        
        containers_row.controls.extend(containers)
        
        if page:
            page.update()
    
    # Диалог для деталей
    details_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(""),
        content=ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            width=500,
            height=300
        ),
        actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(details_dialog) if page else None)]
    )
    
    def show_license_details(e):
        if not page:
            return
        details_dialog.title.value = "УЧО"
        details_dialog.content.content.controls.clear()
        
        def update_license_date(employee_name, field_type, days_to_add=None, new_date=None):
            try:
                if db.is_closed():
                    db.connect()
                employee = Employee.get(Employee.full_name == employee_name)
                if days_to_add:
                    current_date = employee.guard_license_date
                    employee.guard_license_date = current_date + timedelta(days=days_to_add)
                elif new_date:
                    employee.guard_license_date = new_date
                employee.save()
                # Перезагружаем данные и обновляем контейнеры
                nonlocal expiring_licenses, license_min_days
                expiring_licenses, license_min_days = get_expiring_licenses()
                update_containers(search_field.value if search_field else "")
                
                if expiring_licenses:
                    show_license_details(None)
                else:
                    page.close(details_dialog)
            except Exception as ex:
                pass
            finally:
                if not db.is_closed():
                    db.close()
        
        def show_update_dialog(employee_name):
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
                    page.update()
            
            date_field = ft.TextField(label="Новая дата (дд.мм.гггг)", width=200, on_change=format_date_input, max_length=10)
            
            def save_new_date():
                try:
                    new_date = datetime.datetime.strptime(date_field.value, "%d.%m.%Y").date()
                    update_license_date(employee_name, "guard_license_date", new_date=new_date)
                    page.close(update_dialog)
                except Exception as ex:
                    pass
            
            update_dialog = ft.AlertDialog(
                title=ft.Text(f"Обновить УЧО - {employee_name}"),
                content=date_field,
                actions=[
                    ft.TextButton("Сохранить", on_click=lambda e: save_new_date()),
                    ft.TextButton("Отмена", on_click=lambda e: page.close(update_dialog))
                ]
            )
            
            page.overlay.append(update_dialog)
            page.update()
            page.open(update_dialog)
        
        for name, exp_date, days_left in expiring_licenses:
            status = f"Просрочено на {abs(days_left)} дн." if days_left < 0 else f"Осталось {days_left} дн."
            details_dialog.content.content.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"ФИО: {name}", weight="bold"),
                            ft.Text(f"Дата истечения: {exp_date.strftime('%d.%m.%Y')}"),
                            ft.Text(status, color=ft.Colors.RED if days_left < 0 else ft.Colors.ORANGE if days_left <= 7 else ft.Colors.GREEN),
                            ft.Row([
                                ft.ElevatedButton("+1 день", on_click=lambda e, n=name: update_license_date(n, "guard_license_date", 1), width=100),
                                ft.ElevatedButton("+1 неделя", on_click=lambda e, n=name: update_license_date(n, "guard_license_date", 7), width=100),
                                ft.ElevatedButton("Обновить", on_click=lambda e, n=name: show_update_dialog(n), width=100)
                            ], spacing=5)
                        ]),
                        padding=10
                    )
                )
            )
        
        if not expiring_licenses:
            details_dialog.content.content.controls.append(ft.Text("Нет данных"))
        
        page.open(details_dialog)
    
    def create_license_container():
        return ft.Container(
            content=ft.Column([
                ft.Text("УЧО", size=18, weight="bold", color=ft.Colors.WHITE),
                ft.Text(f"Истекает в ближайшие 90 дней: {len(expiring_licenses)}", color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=get_license_color(license_min_days),
            padding=15,
            border_radius=10,
            width=250,
            height=150,
            on_click=show_license_details
        )
    
    def show_medical_details(e):
        if not page:
            return
        details_dialog.title.value = "Медкомиссии"
        details_dialog.content.content.controls.clear()
        
        def update_medical_date(employee_name, field_type, days_to_add=None, new_date=None):
            try:
                if db.is_closed():
                    db.connect()
                employee = Employee.get(Employee.full_name == employee_name)
                if days_to_add:
                    current_date = employee.medical_exam_date
                    employee.medical_exam_date = current_date + timedelta(days=days_to_add)
                elif new_date:
                    employee.medical_exam_date = new_date
                employee.save()
                # Перезагружаем данные и обновляем контейнеры
                nonlocal expiring_medical, medical_min_days
                expiring_medical, medical_min_days = get_expiring_medical()
                update_containers(search_field.value if search_field else "")
                
                if expiring_medical:
                    show_medical_details(None)
                else:
                    page.close(details_dialog)
            except Exception as ex:
                pass
            finally:
                if not db.is_closed():
                    db.close()
        
        def show_update_dialog(employee_name):
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
                    page.update()
            
            date_field = ft.TextField(label="Новая дата (дд.мм.гггг)", width=200, on_change=format_date_input, max_length=10)
            
            def save_new_date():
                try:
                    new_date = datetime.datetime.strptime(date_field.value, "%d.%m.%Y").date()
                    update_medical_date(employee_name, "medical_exam_date", new_date=new_date)
                    page.close(update_dialog)
                except Exception as ex:
                    pass
            
            update_dialog = ft.AlertDialog(
                title=ft.Text(f"Обновить медкомиссию - {employee_name}"),
                content=date_field,
                actions=[
                    ft.TextButton("Сохранить", on_click=lambda e: save_new_date()),
                    ft.TextButton("Отмена", on_click=lambda e: page.close(update_dialog))
                ]
            )
            
            page.overlay.append(update_dialog)
            page.update()
            page.open(update_dialog)
        
        for name, exp_date, days_left in expiring_medical:
            status = f"Просрочено на {abs(days_left)} дн." if days_left < 0 else f"Осталось {days_left} дн."
            details_dialog.content.content.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"ФИО: {name}", weight="bold"),
                            ft.Text(f"Дата истечения: {exp_date.strftime('%d.%m.%Y')}"),
                            ft.Text(status, color=ft.Colors.RED if days_left < 0 else ft.Colors.ORANGE if days_left <= 7 else ft.Colors.GREEN),
                            ft.Row([
                                ft.ElevatedButton("+1 день", on_click=lambda e, n=name: update_medical_date(n, "medical_exam_date", 1), width=100),
                                ft.ElevatedButton("+1 неделя", on_click=lambda e, n=name: update_medical_date(n, "medical_exam_date", 7), width=100),
                                ft.ElevatedButton("Обновить", on_click=lambda e, n=name: show_update_dialog(n), width=100)
                            ], spacing=5)
                        ]),
                        padding=10
                    )
                )
            )
        
        if not expiring_medical:
            details_dialog.content.content.controls.append(ft.Text("Нет данных"))
        
        page.open(details_dialog)
    
    def create_medical_container():
        return ft.Container(
            content=ft.Column([
                ft.Text("Медкомиссии", size=18, weight="bold", color=ft.Colors.WHITE),
                ft.Text(f"Истекает в ближайшие 60 дней: {len(expiring_medical)}", color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=get_medical_color(medical_min_days),
            padding=15,
            border_radius=10,
            width=250,
            height=150,
            on_click=show_medical_details
        )
    
    def show_birthday_details(e):
        if not page:
            return
        details_dialog.title.value = "Дни рождения"
        details_dialog.content.content.controls.clear()
        
        for name, bday, days_left in upcoming_birthdays:
            status = f"Сегодня!" if days_left == 0 else f"Через {days_left} дн."
            details_dialog.content.content.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"ФИО: {name}", weight="bold"),
                            ft.Text(f"Дата рождения: {bday.strftime('%d.%m.%Y')}"),
                            ft.Text(status, color=ft.Colors.RED if days_left == 0 else ft.Colors.ORANGE if days_left <= 1 else ft.Colors.GREEN)
                        ]),
                        padding=10
                    )
                )
            )
        
        if not upcoming_birthdays:
            details_dialog.content.content.controls.append(ft.Text("Нет данных"))
        
        page.open(details_dialog)
    
    def create_birthday_container():
        return ft.Container(
            content=ft.Column([
                ft.Text("Дни рождения", size=18, weight="bold", color=ft.Colors.WHITE),
                ft.Text(f"В ближайшие 7 дней: {len(upcoming_birthdays)}", color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=get_container_color(birthday_min_days),
            padding=15,
            border_radius=10,
            width=250,
            height=150,
            on_click=show_birthday_details
        )
    
    def show_periodic_details(e):
        if not page:
            return
        details_dialog.title.value = "Периодические проверки"
        details_dialog.content.content.controls.clear()
        
        def update_periodic_date(employee_name, field_type, days_to_add=None, new_date=None):
            try:
                if db.is_closed():
                    db.connect()
                employee = Employee.get(Employee.full_name == employee_name)
                if days_to_add:
                    current_date = employee.periodic_check_date
                    employee.periodic_check_date = current_date + timedelta(days=days_to_add)
                elif new_date:
                    employee.periodic_check_date = new_date
                employee.save()
                # Перезагружаем данные и обновляем контейнеры
                nonlocal expiring_periodic_checks, periodic_min_days
                expiring_periodic_checks, periodic_min_days = get_expiring_periodic_checks()
                update_containers(search_field.value if search_field else "")
                
                if expiring_periodic_checks:
                    show_periodic_details(None)
                else:
                    page.close(details_dialog)
            except Exception as ex:
                pass
            finally:
                if not db.is_closed():
                    db.close()
        
        def show_update_dialog(employee_name):
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
                    page.update()
            
            date_field = ft.TextField(label="Новая дата (дд.мм.гггг)", width=200, on_change=format_date_input, max_length=10)
            
            def save_new_date():
                try:
                    new_date = datetime.datetime.strptime(date_field.value, "%d.%m.%Y").date()
                    update_periodic_date(employee_name, "periodic_check_date", new_date=new_date)
                    page.close(update_dialog)
                except Exception as ex:
                    pass
            
            update_dialog = ft.AlertDialog(
                title=ft.Text(f"Обновить периодическую проверку - {employee_name}"),
                content=date_field,
                actions=[
                    ft.TextButton("Сохранить", on_click=lambda e: save_new_date()),
                    ft.TextButton("Отмена", on_click=lambda e: page.close(update_dialog))
                ]
            )
            
            page.overlay.append(update_dialog)
            page.update()
            page.open(update_dialog)
        
        for name, exp_date, days_left in expiring_periodic_checks:
            status = f"Просрочено на {abs(days_left)} дн." if days_left < 0 else f"Осталось {days_left} дн."
            details_dialog.content.content.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"ФИО: {name}", weight="bold"),
                            ft.Text(f"Дата истечения: {exp_date.strftime('%d.%m.%Y')}"),
                            ft.Text(status, color=ft.Colors.RED if days_left < 0 else ft.Colors.ORANGE if days_left <= 7 else ft.Colors.GREEN),
                            ft.Row([
                                ft.ElevatedButton("+1 день", on_click=lambda e, n=name: update_periodic_date(n, "periodic_check_date", 1), width=100),
                                ft.ElevatedButton("+1 неделя", on_click=lambda e, n=name: update_periodic_date(n, "periodic_check_date", 7), width=100),
                                ft.ElevatedButton("Обновить", on_click=lambda e, n=name: show_update_dialog(n), width=100)
                            ], spacing=5)
                        ]),
                        padding=10
                    )
                )
            )
        
        if not expiring_periodic_checks:
            details_dialog.content.content.controls.append(ft.Text("Нет данных"))
        
        page.open(details_dialog)
    
    def create_periodic_container():
        return ft.Container(
            content=ft.Column([
                ft.Text("Периодические проверки", size=18, weight="bold", color=ft.Colors.WHITE),
                ft.Text(f"Истекает в ближайшие 30 дней: {len(expiring_periodic_checks)}", color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=get_periodic_color(periodic_min_days),
            padding=15,
            border_radius=10,
            width=250,
            height=150,
            on_click=show_periodic_details
        )
    
    # Добавляем диалог в overlay
    if page and details_dialog not in page.overlay:
        page.overlay.append(details_dialog)
    
    # Инициализируем контейнеры
    containers = [
        create_license_container(),
        create_medical_container(),
        create_periodic_container()
    ]
    
    # Проверяем настройку отображения дней рождения
    if load_birthday_display_from_db():
        containers.append(create_birthday_container())
    
    containers_row.controls.extend(containers)
    
    return ft.Column(
        [
            ft.Text("Главная страница", size=24, weight="bold"),
            ft.Divider(),
            ft.Row([
                search_field,
                ft.IconButton(
                    icon=ft.Icons.CLEAR,
                    tooltip="Очистить поиск",
                    on_click=lambda e: (setattr(search_field, 'value', ''), update_containers(''))
                )
            ], alignment=ft.MainAxisAlignment.START),
            containers_row,
        ],
        spacing=20,
        expand=True,
    )
