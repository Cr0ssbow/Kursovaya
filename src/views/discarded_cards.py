import flet as ft
from database.models import PersonalCard, GuardEmployee, ChiefEmployee, Company, db
from datetime import datetime
import os

def discarded_cards_page(page: ft.Page = None):
    search_value = ""
    show_nord = True
    show_legion = True
    show_rosbezopasnost = True
    
    # Диалог действий с карточкой
    actions_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Действия с карточкой"),
        content=ft.Column([], height=200),
        actions=[
            ft.TextButton("Восстановить", on_click=lambda e: restore_card(current_card), style=ft.ButtonStyle(color=ft.Colors.GREEN)),
            ft.TextButton("Удалить навсегда", on_click=lambda e: delete_card_permanently(current_card), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Просмотр", on_click=lambda e: view_card(current_card)),
            ft.TextButton("Отмена", on_click=lambda e: close_actions_dialog())
        ]
    )
    
    current_card = None
    
    def show_card_actions(card):
        nonlocal current_card
        current_card = card
        
        # Определяем сотрудника
        employee_name = "Неизвестно"
        if card.guard_employee:
            employee_name = card.guard_employee.full_name
        elif card.chief_employee:
            employee_name = card.chief_employee.full_name
        
        actions_dialog.title.value = f"Карточка: {employee_name}"
        actions_dialog.content.controls = [
            ft.Text(f"Сотрудник: {employee_name}", weight="bold"),
            ft.Text(f"Компания: {card.company.name}"),
            ft.Text(f"Дата выдачи: {format_date(card.issue_date)}"),
            ft.Text(f"Дата списания: {format_date(card.discarded_date)}", color=ft.Colors.RED),
            ft.Text(f"Статус: Списана", color=ft.Colors.RED),
            ft.Divider(),
        ]
        
        actions_dialog.open = True
        if page and actions_dialog not in page.overlay:
            page.overlay.append(actions_dialog)
        if page:
            page.update()
    
    def close_actions_dialog():
        actions_dialog.open = False
        if page:
            page.update()
    
    def restore_card(card):
        """Восстанавливает карточку (убирает пометку о списании)"""
        try:
            if db.is_closed():
                db.connect()
            card.is_discarded = False
            card.discarded_date = None
            card.save()
            close_actions_dialog()
            refresh_list()
        except Exception as ex:
            print(f"Ошибка восстановления: {ex}")
        finally:
            if not db.is_closed():
                db.close()
    
    def delete_card_permanently(card):
        """Удаляет карточку навсегда"""
        try:
            if db.is_closed():
                db.connect()
            # Удаляем файл если существует
            if card.photo_path and os.path.exists(card.photo_path):
                os.remove(card.photo_path)
            card.delete_instance()
            close_actions_dialog()
            refresh_list()
        except Exception as ex:
            print(f"Ошибка удаления: {ex}")
        finally:
            if not db.is_closed():
                db.close()
    
    def view_card(card):
        """Просматривает карточку"""
        if card.photo_path and os.path.exists(card.photo_path):
            import subprocess
            import platform
            try:
                if platform.system() == 'Windows':
                    os.startfile(card.photo_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', card.photo_path])
                else:  # Linux
                    subprocess.run(['xdg-open', card.photo_path])
            except Exception as e:
                print(f"Ошибка открытия файла: {e}")
    
    def format_date(date):
        """Форматирует дату в строку дд.мм.гггг"""
        return date.strftime("%d.%m.%Y") if date else "Не указано"
    
    def get_discarded_cards():
        """Получает список списанных карточек"""
        try:
            if db.is_closed():
                db.connect()
            
            query = PersonalCard.select().where(PersonalCard.is_discarded == True)
            
            # Фильтр по компаниям
            companies = []
            if show_nord:
                companies.append("Норд")
            if show_legion:
                companies.append("Легион")
            if show_rosbezopasnost:
                companies.append("Росбезопасность")
            
            if len(companies) < 3 and len(companies) > 0:
                company_ids = [c.id for c in Company.select().where(Company.name.in_(companies))]
                query = query.where(PersonalCard.company.in_(company_ids))
            elif len(companies) == 0:
                query = query.where(False)
            
            if search_value:
                # Поиск по имени сотрудника
                guard_query = query.join(GuardEmployee, on=(PersonalCard.guard_employee == GuardEmployee.id)).where(
                    GuardEmployee.full_name.contains(search_value)
                )
                chief_query = query.join(ChiefEmployee, on=(PersonalCard.chief_employee == ChiefEmployee.id)).where(
                    ChiefEmployee.full_name.contains(search_value)
                )
                cards = list(guard_query) + list(chief_query)
            else:
                cards = list(query)
            
            # Сортировка по компании
            cards.sort(key=lambda c: c.company.name)
            
            return cards
        except Exception as e:
            print(f"Ошибка получения карточек: {e}")
            return []
        finally:
            if not db.is_closed():
                db.close()
    
    def refresh_list():
        """Обновляет список списанных карточек"""
        discarded_cards = get_discarded_cards()
        cards_list.controls.clear()
        
        if discarded_cards:
            for card in discarded_cards:
                employee_name = "Неизвестно"
                if card.guard_employee:
                    employee_name = card.guard_employee.full_name
                elif card.chief_employee:
                    employee_name = card.chief_employee.full_name
                
                cards_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(employee_name, weight="bold"),
                        subtitle=ft.Text(f"Компания: {card.company.name} | Выдана: {format_date(card.issue_date)} | Списана: {format_date(card.discarded_date)}"),
                        trailing=ft.Text("Списана", color=ft.Colors.RED),
                        on_click=lambda e, c=card: show_card_actions(c)
                    )
                )
        else:
            cards_list.controls.append(
                ft.Container(
                    content=ft.Text("Нет списанных карточек", size=16, color=ft.Colors.GREY),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
        
        if page:
            page.update()
    
    def on_search_change(e):
        nonlocal search_value
        search_value = e.control.value.strip()
        refresh_list()
    
    def on_nord_change(e):
        nonlocal show_nord
        show_nord = e.control.value
        refresh_list()
    
    def on_legion_change(e):
        nonlocal show_legion
        show_legion = e.control.value
        refresh_list()
    
    def on_rosbezopasnost_change(e):
        nonlocal show_rosbezopasnost
        show_rosbezopasnost = e.control.value
        refresh_list()
    
    # Создаем список
    cards_list = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        height=500
    )
    
    refresh_list()
    
    return ft.Column([
        ft.Text("Списанные личные карточки", size=24, weight="bold"),
        ft.Divider(),
        ft.Row([
            ft.TextField(
                label="Поиск по ФИО сотрудника",
                width=300,
                on_change=on_search_change,
                autofocus=False,
                dense=True,
            ),
            ft.Checkbox(label="Норд", value=show_nord, on_change=lambda e: on_nord_change(e)),
            ft.Checkbox(label="Легион", value=show_legion, on_change=lambda e: on_legion_change(e)),
            ft.Checkbox(label="Росбезопасность", value=show_rosbezopasnost, on_change=lambda e: on_rosbezopasnost_change(e)),
        ], alignment=ft.MainAxisAlignment.START, spacing=20),
        ft.Container(
            content=cards_list,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            padding=10,
            expand=True,
        ),
    ], spacing=10, expand=True)