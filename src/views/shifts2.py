import flet as ft
import datetime
from database.models import Assignment, Employee, Object, db
from peewee import *

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
        actions=[ft.TextButton("Закрыть", on_click=lambda e: close_shifts_dialog())]
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
            except Exception as e:
                print(f"Ошибка удаления: {e}")
            finally:
                if not db.is_closed():
                    db.close()
    
    current_assignment = None
    absent_checkbox = ft.Checkbox(label="Пропуск", on_change=lambda e: toggle_absent_comment())
    absent_comment_field = ft.TextField(label="Комментарий к проспуску", visible=False, multiline=True)
    deduction_amount_field = ft.TextField(label="Сумма удержания", visible=False)
    bonus_amount_field = ft.TextField(label="Сумма премии", on_change=lambda e: toggle_bonus_comment())
    bonus_comment_field = ft.TextField(label="Комментарий к премии", visible=False, multiline=True)
    
    def toggle_absent_comment():
        absent_comment_field.visible = absent_checkbox.value
        deduction_amount_field.visible = absent_checkbox.value
        # Скрываем поля премии если стоит галочка пропуска
        bonus_amount_field.visible = not absent_checkbox.value
        if absent_checkbox.value:
            bonus_comment_field.visible = False
        else:
            try:
                bonus_amount = float(bonus_amount_field.value or "0")
                bonus_comment_field.visible = bonus_amount > 0
            except:
                bonus_comment_field.visible = False
        page.update()
    
    def toggle_bonus_comment():
        try:
            bonus_amount = float(bonus_amount_field.value or "0")
            bonus_comment_field.visible = bonus_amount > 0 and not absent_checkbox.value
        except:
            bonus_comment_field.visible = False
        page.update()
    
    def edit_shift(assignment):
        nonlocal current_assignment
        current_assignment = assignment
        
        absent_checkbox.value = assignment.is_absent
        absent_comment_field.value = assignment.absent_comment or ""
        absent_comment_field.visible = assignment.is_absent
        deduction_amount_field.value = str(float(assignment.deduction_amount))
        deduction_amount_field.visible = assignment.is_absent
        bonus_amount_field.value = str(float(assignment.bonus_amount))
        bonus_comment_field.value = assignment.bonus_comment or ""
        # Поля премии скрываются если стоит галочка пропуска
        bonus_amount_field.visible = not assignment.is_absent
        bonus_comment_field.visible = not assignment.is_absent and float(assignment.bonus_amount) > 0
        
        edit_dialog.content.controls = [
            ft.Text(f"Сотрудник: {assignment.employee.full_name}", weight="bold"),
            ft.Text(f"Объект: {assignment.object.name}"),
            ft.Text(f"Дата: {assignment.date.strftime('%d.%m.%Y')}"),
            ft.Divider(),
            absent_checkbox,
            deduction_amount_field,
            absent_comment_field,
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
                current_assignment.deduction_amount = float(deduction_amount_field.value or "0") if absent_checkbox.value else 0
                current_assignment.bonus_amount = float(bonus_amount_field.value or "0")
                current_assignment.bonus_comment = bonus_comment_field.value if float(bonus_amount_field.value or "0") > 0 else None
                current_assignment.save()
                
                close_edit_dialog()
                update_calendar()
                
            except Exception as e:
                print(f"Ошибка сохранения: {e}")
            finally:
                if not db.is_closed():
                    db.close()
    
    def show_shifts_for_date(date_obj):
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
                    if assignment.is_absent:
                        status_text = " (Пропуск)"
                    elif float(assignment.bonus_amount) > 0:
                        status_text = f" (Премия: {assignment.bonus_amount} ₽)"
                    
                    shifts_dialog.content.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Column([
                                            ft.Text(f"Сотрудник: {assignment.employee.full_name}{status_text}", weight="bold"),
                                            ft.Text(f"Объект: {assignment.object.name}"),
                                            ft.Text(f"Часы: {assignment.hours}"),
                                            ft.Text(f"Ставка: {assignment.hourly_rate} ₽/час")
                                        ], expand=True),
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
        
        return ft.Container(
            content=ft.Column([
                ft.Text(str(day), size=14, weight="bold"),
                ft.Text(f"{shifts_count}" if shifts_count > 0 else "", size=10, color=ft.Colors.BLUE)
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
            width=50,
            height=50,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,

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
        current_month_display.value = datetime.date(current_year, current_month, 1).strftime('%B %Y').capitalize()
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
    
    # Добавляем диалоги в overlay страницы
    if edit_dialog not in page.overlay:
        page.overlay.append(edit_dialog)
    if delete_confirm_dialog not in page.overlay:
        page.overlay.append(delete_confirm_dialog)
    
    return shifts_content, shifts_dialog