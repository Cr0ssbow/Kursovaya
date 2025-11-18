import flet as ft
from database.models import Settings, Employee, Object, Assignment, db
from peewee import DoesNotExist
import pandas as pd
from datetime import datetime
import os
from openpyxl.styles import Font, Border, Side

def save_theme_to_db(theme: str):
    Settings.insert(key="theme", value=theme).on_conflict_replace().execute()

def load_theme_from_db() -> str:
    try:
        setting = Settings.get(Settings.key == "theme")
        return setting.value
    except DoesNotExist:
        return "light"

def settings_page(page: ft.Page) -> ft.Column:
    global switch

    def theme_changed(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        switch.label = (
            "Светлая тема" if page.theme_mode == ft.ThemeMode.LIGHT else "Тёмная тема"
        )
        save_theme_to_db("dark" if page.theme_mode == ft.ThemeMode.DARK else "light")
        page.update()

    # Загружаем тему из БД
    theme = load_theme_from_db()
    page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT
    switch = ft.Switch(label=("Тёмная тема" if theme == "dark" else "Светлая тема"), value=(theme == "dark"), on_change=theme_changed)

    # Экспорт данных в Excel с разделением по объектам
    def import_to_excel(e):
        try:
            if db.is_closed():
                db.connect()
            
            # Получаем все назначения с данными сотрудников и объектов
            assignments = Assignment.select(Assignment, Employee, Object).join(Employee).switch(Assignment).join(Object)
            
            # Группируем данные по объектам
            objects_data = {}
            for assignment in assignments:
                obj_name = assignment.object.name
                if obj_name not in objects_data:
                    objects_data[obj_name] = []
                
                objects_data[obj_name].append({
                    'ФИО': assignment.employee.full_name,
                    'Зарплата': float(assignment.employee.salary),
                    'Отработанные часы': assignment.employee.hours_worked
                })
            
            # Создаем Excel файл с названием "График смен" и месяцем
            current_date = datetime.now()
            month_names = {
                1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
                5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
                9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
            }
            month_name = month_names[current_date.month]
            filename = f"График смен {month_name} {current_date.year}.xlsx"
            filepath = os.path.join(os.path.expanduser('~'), 'Downloads', filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                for obj_name, data in objects_data.items():
                    df = pd.DataFrame(data)
                    # Убираем дубликаты по ФИО
                    df = df.drop_duplicates(subset=['ФИО'])
                    df.to_excel(writer, sheet_name=obj_name[:31], index=False)
                    
                    # Настройка форматирования листа
                    worksheet = writer.sheets[obj_name[:31]]
                    worksheet.column_dimensions['A'].width = 60  # ФИО
                    worksheet.column_dimensions['B'].width = 15  # Зарплата
                    worksheet.column_dimensions['C'].width = 20  # Отработанные часы
                    
                    # Настройка шрифта и границ
                    font = Font(name='Times New Roman', size=12)
                    thin_border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                    
                    # Применяем форматирование ко всем заполненным ячейкам
                    for row in worksheet.iter_rows(min_row=1, max_row=len(df)+1, min_col=1, max_col=3):
                        for cell in row:
                            if cell.value is not None:
                                cell.font = font
                                cell.border = thin_border
            
            # Уведомление об успехе
            success_snack = ft.SnackBar(
                content=ft.Text(f"Данные экспортированы в {filename}"),
                bgcolor=ft.Colors.GREEN,
                duration=3000
            )
            page.overlay.append(success_snack)
            success_snack.open = True
            page.update()
            
        except Exception as ex:
            # Уведомление об ошибке
            error_snack = ft.SnackBar(
                content=ft.Text(f"Ошибка экспорта: {str(ex)}"),
                bgcolor=ft.Colors.RED,
                duration=3000
            )
            page.overlay.append(error_snack)
            error_snack.open = True
            page.update()
        finally:
            if not db.is_closed():
                db.close()

    return ft.Column(
        [
            ft.Text("Настройки", size=24, weight="bold"),
            ft.Text("Выбор темы"),
            switch,
            ft.Divider(),
            ft.Text("Экспорт данных"),
            ft.ElevatedButton(
                "Импорт в Excel",
                icon=ft.Icons.FILE_DOWNLOAD,
                on_click=import_to_excel,
            ),
        ],
        spacing=10,
        expand=True,
    )
