import flet as ft
from database.models import Employee, Assignment, db
from datetime import datetime, date

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
    
    # Диалоги для показа деталей
    missed_shifts_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Пропущенные смены"),
        content=ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            width=500,
            height=300
        ),
        actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(missed_shifts_dialog))]
    )
    
    bonuses_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Премии"),
        content=ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            width=500,
            height=300
        ),
        actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(bonuses_dialog))]
    )
    
    deductions_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Удержания"),
        content=ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            width=500,
            height=300
        ),
        actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(deductions_dialog))]
    )
    
    # Карточки статистики
    absences_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Пропуски", size=18, weight="bold"),
                ft.Text("0", size=24, color=ft.Colors.RED)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            width=150,
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
            width=150,
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
            width=150,
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
            width=150,
            height=100
        )
    )
    
    # Список детальной статистики
    stats_list = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        height=500
    )
    
    def update_statistics():
        try:
            if db.is_closed():
                db.connect()
            
            total_absences = 0
            total_bonuses = 0
            total_deductions = 0
            total_salary = 0
            
            employees = Employee.select()
            stats_list.controls.clear()
            
            for employee in employees:
                assignments = Assignment.select().where(
                    (Assignment.employee == employee) &
                    (Assignment.date.month == selected_month) &
                    (Assignment.date.year == selected_year)
                )
                
                emp_absences = sum(1 for a in assignments if a.is_absent)
                # Базовая зарплата за отработанные смены
                base_salary = sum(float(a.hourly_rate) * a.hours for a in assignments if not a.is_absent)
                # Премии только за отработанные смены
                emp_bonuses = sum(float(a.bonus_amount) for a in assignments if not a.is_absent)
                # Удержания со всех смен (включая отработанные)
                emp_deductions = sum(float(a.deduction_amount) for a in assignments)
                # Итоговая зарплата
                emp_salary = base_salary + emp_bonuses - emp_deductions
                emp_salary = max(0, emp_salary)
                
                total_absences += emp_absences
                total_bonuses += emp_bonuses
                total_deductions += emp_deductions
                total_salary += emp_salary
                
                if emp_absences > 0 or emp_bonuses > 0 or emp_deductions > 0 or emp_salary > 0:
                    def show_missed_shifts(employee_id, employee_name):
                        def on_click(e):
                            try:
                                if db.is_closed():
                                    db.connect()
                                
                                missed_assignments = Assignment.select().where(
                                    (Assignment.employee == employee_id) &
                                    (Assignment.date.month == selected_month) &
                                    (Assignment.date.year == selected_year) &
                                    (Assignment.is_absent == True)
                                )
                                
                                missed_shifts_dialog.title.value = f"Пропущенные смены - {employee_name}"
                                missed_shifts_dialog.content.content.controls.clear()
                                
                                if missed_assignments.count() == 0:
                                    missed_shifts_dialog.content.content.controls.append(
                                        ft.Text("Нет пропущенных смен")
                                    )
                                else:
                                    for assignment in missed_assignments:
                                        missed_shifts_dialog.content.content.controls.append(
                                            ft.Card(
                                                content=ft.Container(
                                                    content=ft.Column([
                                                        ft.Text(f"Дата: {assignment.date.strftime('%d.%m.%Y')}", weight="bold"),
                                                        ft.Text(f"Объект: {assignment.object.name}"),
                                                        ft.Text(f"Часы: {assignment.hours}"),
                                                        ft.Text(f"Комментарий: {assignment.absent_comment or 'Не указан'}")
                                                    ]),
                                                    padding=10
                                                )
                                            )
                                        )
                                
                                page.open(missed_shifts_dialog)
                                
                            except Exception as e:
                                print(f"Ошибка при загрузке пропущенных смен: {e}")
                            finally:
                                if not db.is_closed():
                                    db.close()
                        return on_click
                    
                    def show_bonuses(employee_id, employee_name):
                        def on_click(e):
                            try:
                                if db.is_closed():
                                    db.connect()
                                
                                bonus_assignments = Assignment.select().where(
                                    (Assignment.employee == employee_id) &
                                    (Assignment.date.month == selected_month) &
                                    (Assignment.date.year == selected_year) &
                                    (Assignment.bonus_amount > 0)
                                )
                                
                                bonuses_dialog.title.value = f"Премии - {employee_name}"
                                bonuses_dialog.content.content.controls.clear()
                                
                                if bonus_assignments.count() == 0:
                                    bonuses_dialog.content.content.controls.append(
                                        ft.Text("Нет премий")
                                    )
                                else:
                                    for assignment in bonus_assignments:
                                        bonuses_dialog.content.content.controls.append(
                                            ft.Card(
                                                content=ft.Container(
                                                    content=ft.Column([
                                                        ft.Text(f"Дата: {assignment.date.strftime('%d.%m.%Y')}", weight="bold"),
                                                        ft.Text(f"Объект: {assignment.object.name}"),
                                                        ft.Text(f"Сумма: {assignment.bonus_amount:.0f} ₽", color=ft.Colors.GREEN),
                                                        ft.Text(f"Комментарий: {assignment.bonus_comment or 'Не указан'}")
                                                    ]),
                                                    padding=10
                                                )
                                            )
                                        )
                                
                                page.open(bonuses_dialog)
                                
                            except Exception as e:
                                print(f"Ошибка при загрузке премий: {e}")
                            finally:
                                if not db.is_closed():
                                    db.close()
                        return on_click
                    
                    def show_deductions(employee_id, employee_name):
                        def on_click(e):
                            try:
                                if db.is_closed():
                                    db.connect()
                                
                                deduction_assignments = Assignment.select().where(
                                    (Assignment.employee == employee_id) &
                                    (Assignment.date.month == selected_month) &
                                    (Assignment.date.year == selected_year) &
                                    (Assignment.deduction_amount > 0)
                                )
                                
                                deductions_dialog.title.value = f"Удержания - {employee_name}"
                                deductions_dialog.content.content.controls.clear()
                                
                                if deduction_assignments.count() == 0:
                                    deductions_dialog.content.content.controls.append(
                                        ft.Text("Нет удержаний")
                                    )
                                else:
                                    for assignment in deduction_assignments:
                                        deductions_dialog.content.content.controls.append(
                                            ft.Card(
                                                content=ft.Container(
                                                    content=ft.Column([
                                                        ft.Text(f"Дата: {assignment.date.strftime('%d.%m.%Y')}", weight="bold"),
                                                        ft.Text(f"Объект: {assignment.object.name}"),
                                                        ft.Text(f"Сумма: {assignment.deduction_amount:.0f} ₽", color=ft.Colors.RED)
                                                    ]),
                                                    padding=10
                                                )
                                            )
                                        )
                                
                                page.open(deductions_dialog)
                                
                            except Exception as e:
                                print(f"Ошибка при загрузке удержаний: {e}")
                            finally:
                                if not db.is_closed():
                                    db.close()
                        return on_click
                    
                    def show_employee_details(emp_id, emp_name):
                        # Можно добавить логику для показа деталей
                        pass
                    
                    # Создаем элемент списка
                    stats_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(employee.full_name, weight="bold"),
                            subtitle=ft.Text(f"Пропуски: {emp_absences} | Премии: {emp_bonuses:.0f} ₽ | Удержания: {emp_deductions:.0f} ₽"),
                            trailing=ft.Text(f"{emp_salary:.0f} ₽", weight="bold", color=ft.Colors.BLUE),
                            on_click=lambda e, emp_id=employee.id, emp_name=employee.full_name: show_employee_details(emp_id, emp_name)
                        )
                    )
            
            # Обновляем карточки
            absences_card.content.content.controls[1].value = str(total_absences)
            bonuses_card.content.content.controls[1].value = f"{total_bonuses:.0f} ₽"
            deductions_card.content.content.controls[1].value = f"{total_deductions:.0f} ₽"
            salary_card.content.content.controls[1].value = f"{total_salary:.0f} ₽"
            
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
    
    # Добавляем диалоги в overlay
    if page:
        if missed_shifts_dialog not in page.overlay:
            page.overlay.append(missed_shifts_dialog)
        if bonuses_dialog not in page.overlay:
            page.overlay.append(bonuses_dialog)
        if deductions_dialog not in page.overlay:
            page.overlay.append(deductions_dialog)
    
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
            salary_card
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Divider(),
        ft.Text("Детальная статистика по сотрудникам", size=18, weight="bold"),
        ft.Container(
            content=stats_list,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            padding=10,
            expand=True
        )
    ], spacing=10, expand=True)
    
    return statistics_content