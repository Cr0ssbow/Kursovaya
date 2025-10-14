import datetime
import flet as ft
import locale

# Set locale for Russian month names
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def calendar_page(page: ft.Page):
    selected_date_text = ft.Text("Выберите дату", size=20)
    current_month_display = ft.Text("", size=24, weight=ft.FontWeight.BOLD)
    calendar_grid_container = ft.Column()

    def on_date_select(e):
        selected_date_text.value = f"Выбрана дата: {e.control.data.strftime('%d.%m.%Y')}"
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
        
        start_weekday = first_day_of_month.weekday() # Monday is 0, Sunday is 6
        empty_slots = (start_weekday + 1) % 7 # Number of empty slots before the 1st day of the month if Sunday is the first day of the week

        days = []
        for _ in range(empty_slots):
            days.append(ft.Container(width=40, height=40)) # Empty containers for padding

        for day in range(1, days_in_month + 1):
            current_date = datetime.date(year, month, day)
            days.append(create_day_button(day, current_date))

        # Fill remaining slots to complete the last week
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

    update_calendar_view() # Initial calendar render

    return ft.Column(
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
