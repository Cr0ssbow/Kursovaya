import flet as ft
from database.models import Employee, Assignment, CashWithdrawal, db
from datetime import datetime, date
from peewee import fn

# Словарь русских названий месяцев
RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

def statistics_page(page: ft.Page = None):
    current_date = date.today()
    selected_month = current_date.month
    selected_year = current_date.year
    
    # Отображение месяца
    month_display = ft.Text(f"{RUSSIAN_MONTHS[selected_month]} {selected_year}", size=20, weight="bold")
    
    # Поле поиска сотрудника
    employee_search = ft.TextField(
        label="Поиск сотрудника",
        width=300,
        on_change=lambda e: search_employees(e.control.value)
    )
    
    # Контейнер для результатов поиска
    search_results = ft.Column(visible=False)
    
    # Диалог для статистики сотрудника
    employee_stats_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Статистика сотрудника"),
        content=ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            width=500,
            height=400
        ),
        actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(employee_stats_dialog))]
    )
    

    
    # Карточки статистики
    absences_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Пропуски", size=18, weight="bold"),
                ft.Text("0", size=24, color=ft.Colors.RED)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=200,
            height=100
        )
    )
    
    bonuses_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Премии", size=18, weight="bold"),
                ft.Text("0 ₽", size=24, color=ft.Colors.GREEN)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=200,
            height=100
        )
    )
    
    salary_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Зарплата", size=18, weight="bold"),
                ft.Text("0 ₽", size=24, color=ft.Colors.BLUE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=200,
            height=100
        )
    )
    
    deductions_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Удержания", size=18, weight="bold"),
                ft.Text("0 ₽", size=24, color=ft.Colors.ORANGE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=200,
            height=100
        )
    )
    
    vzn_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("ВЗН", size=18, weight="bold"),
                ft.Text("0 ₽", size=24, color=ft.Colors.PURPLE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=200,
            height=100
        )
    )
    

    
    def search_employees(query):
        if not query or len(query) < 2:
            search_results.visible = False
            if page:
                page.update()
            return
        
        try:
            if db.is_closed():
                db.connect()
            
            # Поиск среди активных сотрудников
            employees = Employee.select().where(
                (Employee.termination_date.is_null()) &
                (fn.LOWER(Employee.full_name).contains(query.lower()))
            ).limit(5)
            
            # Если не найдено, ищем среди всех сотрудников
            if not employees.exists():
                employees = Employee.select().where(
                    fn.LOWER(Employee.full_name).contains(query.lower())
                ).limit(5)
            
            search_results.controls.clear()
            
            if employees.exists():
                for emp in employees:
                    status = " (неактивен)" if emp.termination_date is not None else ""
                    search_results.controls.append(
                        ft.ListTile(
                            title=ft.Text(f"{emp.full_name}{status}"),
                            on_click=lambda e, employee=emp: select_employee(employee)
                        )
                    )
                search_results.visible = True
            else:
                search_results.controls.append(ft.Text("Сотрудник не найден", color=ft.Colors.ERROR))
                search_results.visible = True
            
            if page:
                page.update()
            
        except Exception as e:
            print(f"Ошибка при поиске сотрудников: {e}")
        finally:
            if not db.is_closed():
                db.close()
    
    def select_employee(employee):
        employee_search.value = employee.full_name
        search_results.visible = False
        if page:
            page.update()
    
    def show_employee_stats(e):
        if not employee_search.value:
            return
        
        try:
            if db.is_closed():
                db.connect()
            
            try:
                employee = Employee.get(Employee.full_name == employee_search.value.replace(" (неактивен)", ""))
                emp_id = employee.id
            except Employee.DoesNotExist:
                employee_stats_dialog.title.value = "Ошибка"
                employee_stats_dialog.content.content.controls.clear()
                employee_stats_dialog.content.content.controls.append(
                    ft.Text("Сотрудник не найден. Пожалуйста, выберите сотрудника из списка.", color=ft.Colors.ERROR)
                )
                page.open(employee_stats_dialog)
                return
            
            start_date = date(selected_year, selected_month, 1)
            if selected_month == 12:
                end_date = date(selected_year + 1, 1, 1)
            else:
                end_date = date(selected_year, selected_month + 1, 1)
            
            # Статистика по сменам
            assignments = Assignment.select().where(
                (Assignment.employee == emp_id) &
                Assignment.date.between(start_date, end_date)
            )
            
            absences = sum(1 for a in assignments if a.is_absent)
            base_salary = sum(float(a.hourly_rate) * a.hours for a in assignments if not a.is_absent)
            bonuses = sum(float(a.bonus_amount) for a in assignments)
            deductions = sum(float(a.deduction_amount) for a in assignments)
            
            # Статистика по ВЗН
            vzn_records = CashWithdrawal.select().where(
                (CashWithdrawal.employee == emp_id) &
                CashWithdrawal.date.between(start_date, end_date)
            )
            
            vzn_bonuses = sum(float(v.bonus_amount) for v in vzn_records)
            total_salary = base_salary + bonuses - deductions
            
            employee_stats_dialog.title.value = f"Статистика - {employee.full_name}"
            employee_stats_dialog.content.content.controls.clear()
            
            employee_stats_dialog.content.content.controls.extend([
                ft.Text(f"Период: {RUSSIAN_MONTHS[selected_month]} {selected_year}", size=16, weight="bold"),
                ft.Divider(),
                ft.Row([
                    ft.Text(f"Пропуски: {absences}", color=ft.Colors.RED),
                    ft.Text(f"Премии: {bonuses + vzn_bonuses:.0f} ₽", color=ft.Colors.GREEN),
                ]),
                ft.Row([
                    ft.Text(f"Удержания: {deductions:.0f} ₽", color=ft.Colors.ORANGE),
                    ft.Text(f"Зарплата: {total_salary:.0f} ₽", color=ft.Colors.BLUE, weight="bold")
                ])
            ])
            
            page.open(employee_stats_dialog)
            
        except Exception as e:
            print(f"Ошибка при загрузке статистики сотрудника: {e}")
        finally:
            if not db.is_closed():
                db.close()
    
    def update_statistics():
        try:
            if db.is_closed():
                db.connect()
            
            start_date = date(selected_year, selected_month, 1)
            if selected_month == 12:
                end_date = date(selected_year + 1, 1, 1)
            else:
                end_date = date(selected_year, selected_month + 1, 1)
            
            # Прямые агрегированные запросы без JOIN
            total_absences = Assignment.select(fn.SUM(Assignment.is_absent.cast('integer'))).where(
                Assignment.date.between(start_date, end_date)
            ).scalar() or 0
            
            total_bonuses = Assignment.select(fn.SUM(Assignment.bonus_amount)).where(
                Assignment.date.between(start_date, end_date)
            ).scalar() or 0
            
            total_deductions = Assignment.select(fn.SUM(Assignment.deduction_amount)).where(
                Assignment.date.between(start_date, end_date)
            ).scalar() or 0
            
            total_salary = Assignment.select(
                fn.SUM((~Assignment.is_absent).cast('integer') * Assignment.hourly_rate * Assignment.hours)
            ).where(Assignment.date.between(start_date, end_date)).scalar() or 0
            
            # Добавляем данные из ВЗН
            vzn_bonuses = CashWithdrawal.select(fn.SUM(CashWithdrawal.bonus_amount)).where(
                CashWithdrawal.date.between(start_date, end_date)
            ).scalar() or 0
            
            vzn_total = CashWithdrawal.select(
                fn.SUM((~CashWithdrawal.is_absent).cast('integer') * CashWithdrawal.hourly_rate * CashWithdrawal.hours + CashWithdrawal.bonus_amount - CashWithdrawal.deduction_amount)
            ).where(CashWithdrawal.date.between(start_date, end_date)).scalar() or 0
            
            total_bonuses += vzn_bonuses
            
            # Обновляем карточки
            absences_card.content.content.controls[1].value = str(int(total_absences))
            bonuses_card.content.content.controls[1].value = f"{total_bonuses:.0f} ₽"
            deductions_card.content.content.controls[1].value = f"{total_deductions:.0f} ₽"
            salary_card.content.content.controls[1].value = f"{total_salary:.0f} ₽"
            vzn_card.content.content.controls[1].value = f"{vzn_total:.0f} ₽"
            
        except Exception as e:
            print(f"Ошибка при загрузке статистики: {e}")
        finally:
            if not db.is_closed():
                db.close()
        
        if page:
            page.update()
    
    def change_month(delta):
        nonlocal selected_month, selected_year
        selected_month += delta
        if selected_month > 12:
            selected_month = 1
            selected_year += 1
        elif selected_month < 1:
            selected_month = 12
            selected_year -= 1
        month_display.value = f"{RUSSIAN_MONTHS[selected_month]} {selected_year}"
        update_statistics()
    

    

    update_statistics()
    
    # Добавляем диалог в overlay
    if page and employee_stats_dialog not in page.overlay:
        page.overlay.append(employee_stats_dialog)
    
    statistics_content = ft.Column([
        ft.Text("Статистика", size=24, weight="bold"),
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: change_month(-1)),
            month_display,
            ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: change_month(1))
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        ft.Row([
            absences_card,
            bonuses_card,
            deductions_card,
            salary_card,
            vzn_card
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Divider(),
        ft.Row([
            employee_search,
            ft.ElevatedButton("Показать статистику", on_click=show_employee_stats)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        search_results
    ], spacing=10, expand=True)
    
    return statistics_content