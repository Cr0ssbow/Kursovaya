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
    
    def close_shifts_dialog():
        shifts_dialog.open = False
        page.dialog = None
        page.update()
    
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
                    shifts_dialog.content.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text(f"Сотрудник: {assignment.employee.full_name}", weight="bold"),
                                    ft.Text(f"Объект: {assignment.object.name}"),
                                    ft.Text(f"Часы: {assignment.hours}"),
                                    ft.Text(f"Ставка: {assignment.hourly_rate} ₽/час")
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
    
    return shifts_content, shifts_dialog