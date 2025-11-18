import datetime
import flet as ft
import locale
from database.models import Employee, Object, Assignment, db
from peewee import *

# Русская локализация
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def calendar_page(page: ft.Page):
    # Отображение выбранной даты в верхней части страницы
    selected_date_text = ft.Text("Выберите дату", size=20)
    # Отображение текущего месяца и года
    current_month_display = ft.Text("", size=24, weight=ft.FontWeight.BOLD)
    # Контейнер для сетки календаря
    calendar_grid_container = ft.Column()

    # Загрузка списков сотрудников и объектов из базы данных
    employees = []
    objects = []
    try:
        if db.is_closed():
            db.connect()
        employees = Employee.select()
        objects = Object.select()
    except OperationalError as e:
        print(f"Error fetching data: {e}")
    finally:
        if not db.is_closed():
            db.close()

    # Поле поиска сотрудника
    employee_search = ft.TextField(
        label="Поиск сотрудника",
        width=300,
        on_change=lambda e: search_employees(e.control.value),
    )
    
    # Список найденных сотрудников
    search_results = ft.Column(visible=False)
    
    # Функция поиска сотрудников по введенному тексту
    def search_employees(query):
        # Проверка минимальной длины запроса (2 символа)
        if not query or len(query) < 2:
            search_results.visible = False
            page.update()
            return
            
        # Фильтрация сотрудников по частичному совпадению имени
        filtered_employees = [emp for emp in employees if query.lower() in emp.full_name.lower()]
        
        # Очистка списка результатов и добавление новых
        search_results.controls.clear()
        if filtered_employees:
            # Ограничение количества результатов (5 штук)
            for emp in filtered_employees[:5]:
                search_results.controls.append(
                    ft.ListTile(
                        title=ft.Text(emp.full_name),
                        on_click=lambda e, employee=emp: select_employee(employee),

                    )
                )
            search_results.visible = True
        else:
            # Отображение сообщения о том, что ничего не найдено
            search_results.controls.append(
                ft.Text("Сотрудник не найден", color=ft.Colors.ERROR)
            )
            search_results.visible = True
        page.update()
    
    # Функция выбора сотрудника из списка результатов
    def select_employee(employee):
        # Заполнение поля поиска выбранным именем
        employee_search.value = employee.full_name
        # Скрытие списка результатов
        search_results.visible = False
        page.update()
    
    # Поле поиска объекта
    object_search = ft.TextField(
        label="Поиск объекта",
        width=300,
        on_change=lambda e: search_objects(e.control.value),
    )
    
    # Список найденных объектов
    object_search_results = ft.Column(visible=False)
    
    # Функция поиска объектов по введенному тексту
    def search_objects(query):
        # Проверка минимальной длины запроса (2 символа)
        if not query or len(query) < 2:
            object_search_results.visible = False
            page.update()
            return
            
        # Фильтрация объектов по частичному совпадению названия
        filtered_objects = [obj for obj in objects if query.lower() in obj.name.lower()]
        
        # Очистка списка результатов и добавление новых
        object_search_results.controls.clear()
        if filtered_objects:
            # Ограничение количества результатов (5 штук)
            for obj in filtered_objects[:5]:
                object_search_results.controls.append(
                    ft.ListTile(
                        title=ft.Text(obj.name),
                        on_click=lambda e, object_item=obj: select_object(object_item),
                    )
                )
            object_search_results.visible = True
        else:
            # Отображение сообщения о том, что ничего не найдено
            object_search_results.controls.append(
                ft.Text("Объект не найден", color=ft.Colors.ERROR)
            )
            object_search_results.visible = True
        page.update()
    
    # Функция выбора объекта из списка результатов
    def select_object(obj):
        # Заполнение поля поиска выбранным названием
        object_search.value = obj.name
        # Скрытие списка результатов
        object_search_results.visible = False
        # Обновление информации о почасовой ставке и адресе
        hourly_rate_display.value = f"Почасовая ставка: {float(obj.hourly_rate):.2f} ₽"
        address_display.value = f"Адрес: {obj.address or 'не указан'}"
        page.update()
    
    hours_dropdown = ft.Dropdown(
        label="Количество часов",
        options=[
            ft.dropdown.Option("12"),
            ft.dropdown.Option("24")
        ],
        value="12", # ставка по умолчанию
        width=200,
    )
    
    hourly_rate_display = ft.Text("Почасовая ставка: не выбрано", size=16)
    address_display = ft.Text("Адрес: не выбрано", size=16)

    date_menu = ft.AlertDialog(
        modal=True,
        title=ft.Text("Выставление смены на дату"),
        content=ft.Column([
            ft.Text(""), # This will be updated with the selected date
            employee_search,
            search_results,
            object_search,
            object_search_results,
            hours_dropdown,
            address_display,
            hourly_rate_display,
        ], spacing=10),
        actions=[
            ft.TextButton("Сохранить", on_click=lambda e: save_date_assignment(e)),
            ft.TextButton("Закрыть", on_click=lambda e: close_date_menu(e)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_date_menu(date_obj):
        nonlocal selected_date
        selected_date = date_obj
        date_menu.content.controls[0].value = f"Выбрана дата: {date_obj.strftime('%d.%m.%Y')}"
        page.dialog = date_menu
        date_menu.open = True
        page.update()

    def close_date_menu(e):
        date_menu.open = False
        page.dialog = None
        page.update()
    
    selected_date = None
    
    def save_date_assignment(e):
        selected_employee_name = employee_search.value
        selected_object_name = object_search.value
        selected_hours = hours_dropdown.value
        
        if selected_employee_name and selected_object_name and selected_hours and selected_date:
            try:
                if db.is_closed():
                    db.connect()
                
                # Находим сотрудника и объект
                employee = Employee.get(Employee.full_name == selected_employee_name)
                obj = Object.get(Object.name == selected_object_name)
                
                # Сохраняем назначение
                Assignment.create(
                    employee=employee,
                    object=obj,
                    date=selected_date,
                    hours=int(selected_hours),
                    hourly_rate=obj.hourly_rate
                )
                
                # Обновляем зарплату сотрудника
                salary_increase = float(obj.hourly_rate) * int(selected_hours)
                new_salary = float(employee.salary) + salary_increase
                new_hours = employee.hours_worked + int(selected_hours)
                
                employee.salary = new_salary
                employee.hours_worked = new_hours
                employee.save()
                

                
                close_date_menu(e)
                success_snack = ft.SnackBar(
                    content=ft.Text(f"Назначение сохранено! Зарплата: {new_salary:.2f} ₽"),
                    bgcolor=ft.Colors.GREEN,
                    duration=3000
                )
                page.overlay.append(success_snack)
                success_snack.open = True
                page.update()
                
            except Exception as ex:
                close_date_menu(e)
                error_snack = ft.SnackBar(
                    content=ft.Text(f"Ошибка сохранения: {str(ex)}"),
                    bgcolor=ft.Colors.RED,
                    duration=3000
                )
                page.overlay.append(error_snack)
                error_snack.open = True
                page.update()
            finally:
                if not db.is_closed():
                    db.close()
        else:
            close_date_menu(e)

    def on_date_select(e):
        selected_date_text.value = f"Выбрана дата: {e.control.data.strftime('%d.%m.%Y')}"
        open_date_menu(e.control.data)
        page.update()

    def create_day_button(day, date_obj):
        return ft.ElevatedButton(
            text=str(day),
            data=date_obj,
            on_click=on_date_select,
            width=40,
            height=40,
            style=ft.ButtonStyle(padding=0)
        )

    def get_calendar_grid(year, month):
        first_day_of_month = datetime.date(year, month, 1)
        days_in_month = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days if month < 12 else (datetime.date(year + 1, 1, 1) - datetime.date(year, 12, 1)).days
        
        start_weekday = first_day_of_month.weekday()
        empty_slots = (start_weekday + 1) % 7

        days = []
        for _ in range(empty_slots):
            days.append(ft.Container(width=40, height=40))

        for day in range(1, days_in_month + 1):
            current_date = datetime.date(year, month, day)
            days.append(create_day_button(day, current_date))

        while len(days) % 7 != 0:
            days.append(ft.Container(width=40, height=40))

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Пн", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("Вт", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("Ср", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("Чт", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("Пт", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("Сб", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("Вс", weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Row(days[i:i+7], alignment=ft.MainAxisAlignment.CENTER)
                        for i in range(0, len(days), 7)
                    ]
                )
            ]
        )

    current_year = datetime.date.today().year
    current_month = datetime.date.today().month

    year_dropdown = ft.Dropdown(
        width=100,
        options=[ft.dropdown.Option(str(year)) for year in range(datetime.date.today().year - 10, datetime.date.today().year + 10)],
        value=str(datetime.date.today().year),
        on_change=lambda e: change_year(int(e.control.value)),
    )

    def update_calendar_view():
        nonlocal current_year, current_month
        current_month_display.value = datetime.date(current_year, current_month, 1).strftime('%B %Y').capitalize()
        calendar_grid_container.controls = [get_calendar_grid(current_year, current_month)]
        year_dropdown.value = str(current_year)
        page.update()

    def change_month(e):
        nonlocal current_month, current_year
        if e.control.icon == ft.Icons.ARROW_LEFT:
            current_month -= 1
            if current_month < 1:
                current_month = 12
                current_year -= 1
        else:
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        update_calendar_view()

    def change_year(year):
        nonlocal current_year
        current_year = year
        update_calendar_view()

    update_calendar_view()

    calendar_content = ft.Column(
        [
            selected_date_text,
            ft.Row(
                [
                    ft.IconButton(ft.Icons.ARROW_LEFT, on_click=change_month),
                    current_month_display,
                    ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=change_month),
                    year_dropdown,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            calendar_grid_container,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return calendar_content, date_menu
