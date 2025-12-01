import flet as ft
from database.models import Object, ObjectAddress, ObjectRate, db

def objects_page(page: ft.Page = None):
    search_value = ""
    current_page = 0
    page_size = 9
    sort_ascending = True
    sort_by_name = True
    objects_list_view = ft.ListView(expand=True, spacing=10, padding=20)

    # Диалог и поля формы
    add_dialog = ft.AlertDialog(modal=True)
    name_field = ft.TextField(label="Название объекта", width=300)
    description_field = ft.TextField(label="Описание объекта", multiline=True, width=300)

    def show_add_dialog(e):
        name_field.value = ""
        description_field.value = ""
        add_dialog.title = ft.Text("Добавить объект")
        add_dialog.content = ft.Column([
            name_field,
            description_field,
        ], spacing=10)
        add_dialog.actions = [
            ft.TextButton("Сохранить", on_click=save_object),
            ft.TextButton("Отмена", on_click=close_add_dialog),
        ]
        add_dialog.open = True
        if page and add_dialog not in page.overlay:
            page.overlay.append(add_dialog)
        if page:
            page.update()

    def close_add_dialog(e):
        add_dialog.open = False
        if page:
            page.update()

    def save_object(e):
        try:
            name = name_field.value.strip()
            description = description_field.value.strip()
            if not name:
                raise ValueError("Название объекта обязательно!")
            with db.atomic():
                Object.create(name=name, description=description)
            close_add_dialog(e)
            refresh_list()
            if page:
                page.update()
        except Exception as ex:
            add_dialog.content = ft.Column([
                name_field,
                description_field,
                ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)
            ], spacing=10)
            if page:
                page.update()

    # Диалог редактирования
    edit_dialog = ft.AlertDialog(modal=True)
    edit_name = ft.TextField(label="Название объекта", width=300)
    edit_description = ft.TextField(label="Описание объекта", multiline=True, width=300)

    # Диалог подтверждения удаления
    confirm_delete_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Подтвердите удаление"),
        content=ft.Text("Вы уверены, что хотите удалить этот объект?"),
        actions=[
            ft.TextButton("Да", on_click=None),
            ft.TextButton("Отмена", on_click=lambda e: close_confirm_delete_dialog()),
        ]
    )

    def show_confirm_delete_dialog(obj):
        confirm_delete_dialog.actions[0].on_click = lambda e: delete_object(obj)
        confirm_delete_dialog.open = True
        if page and confirm_delete_dialog not in page.overlay:
            page.overlay.append(confirm_delete_dialog)
        if page:
            page.update()

    def close_confirm_delete_dialog():
        confirm_delete_dialog.open = False
        if page:
            page.update()

    def delete_object(obj):
        obj.delete_instance()
        close_confirm_delete_dialog()
        close_edit_dialog(None)
        refresh_list()
        if page:
            page.update()

    def get_addresses_tab(obj):
        addresses_list = ft.Column([], spacing=5)
        new_address_field = ft.TextField(label="Новый адрес", width=300)
        
        def refresh_addresses():
            addresses_list.controls.clear()
            for addr in obj.addresses:
                def make_delete_handler(address):
                    return lambda e: delete_address(address)
                
                addresses_list.controls.append(
                    ft.Row([
                        ft.Text(addr.address, expand=True),
                        ft.Checkbox(label="Основной", value=addr.is_primary),
                        ft.IconButton(icon=ft.Icons.DELETE, on_click=make_delete_handler(addr))
                    ])
                )
            if page:
                page.update()
        
        def add_address(e):
            if new_address_field.value and new_address_field.value.strip():
                ObjectAddress.create(object=obj, address=new_address_field.value.strip())
                new_address_field.value = ""
                refresh_addresses()
        
        def delete_address(addr):
            addr.delete_instance()
            refresh_addresses()
        
        refresh_addresses()
        return ft.Column([
            ft.Row([new_address_field, ft.ElevatedButton("Добавить", on_click=add_address)]),
            ft.Container(height=10),
            ft.Container(content=addresses_list, height=200)
        ])

    def get_rates_tab(obj):
        rates_list = ft.Column([], spacing=5)
        new_rate_field = ft.TextField(label="Новая ставка", width=150)
        rate_desc_field = ft.TextField(label="Описание", width=200)
        
        def refresh_rates():
            rates_list.controls.clear()
            for rate in obj.rates:
                def make_delete_handler(rate_obj):
                    return lambda e: delete_rate(rate_obj)
                
                rates_list.controls.append(
                    ft.Row([
                        ft.Text(f"{rate.rate} ₽/ч", width=80),
                        ft.Text(rate.description or "", expand=True),
                        ft.Checkbox(label="По умолчанию", value=rate.is_default),
                        ft.IconButton(icon=ft.Icons.DELETE, on_click=make_delete_handler(rate))
                    ])
                )
            if page:
                page.update()
        
        def add_rate(e):
            if new_rate_field.value and new_rate_field.value.strip():
                try:
                    rate_value = float(new_rate_field.value.strip().replace(",", "."))
                    ObjectRate.create(object=obj, rate=rate_value, description=rate_desc_field.value.strip() if rate_desc_field.value else None)
                    new_rate_field.value = ""
                    rate_desc_field.value = ""
                    refresh_rates()
                except ValueError:
                    pass
        
        def delete_rate(rate):
            rate.delete_instance()
            refresh_rates()
        
        refresh_rates()
        return ft.Column([
            ft.Row([new_rate_field, rate_desc_field, ft.ElevatedButton("Добавить", on_click=add_rate)]),
            ft.Container(height=10),
            ft.Container(content=rates_list, height=200)
        ])

    def show_edit_dialog(obj):
        edit_name.value = obj.name
        edit_description.value = obj.description or ""
        
        # Создаем вкладки
        tabs = ft.Tabs(
            tabs=[
                ft.Tab(text="Основное", content=ft.Column([ft.Container(height=10), edit_name, edit_description], spacing=10)),
                ft.Tab(text="Адреса", content=get_addresses_tab(obj)),
                ft.Tab(text="Ставки", content=get_rates_tab(obj))
            ]
        )
        
        edit_dialog.title = ft.Text("Редактировать объект")
        edit_dialog.content = ft.Container(content=tabs, width=500, height=400)
        edit_dialog.actions = [
            ft.TextButton("Сохранить", on_click=lambda e, object_id=obj.id: save_edit_object(object_id)),
            ft.TextButton("Удалить", on_click=lambda e, obj_to_delete=obj: show_confirm_delete_dialog(obj_to_delete), style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Отмена", on_click=close_edit_dialog),
        ]
        edit_dialog.open = True
        if page and edit_dialog not in page.overlay:
            page.overlay.append(edit_dialog)
        if page:
            page.update()
            
    def close_edit_dialog(e):
        edit_dialog.open = False
        if page:
            page.update()

    def save_edit_object(object_id):
        try:
            new_name = edit_name.value.strip()
            new_description = edit_description.value.strip()
            if not new_name:
                raise ValueError("Название объекта обязательно!")
            with db.atomic():
                object_to_update = Object.get_by_id(object_id)
                object_to_update.name = new_name
                object_to_update.description = new_description
                object_to_update.save()
            close_edit_dialog(None)
            refresh_list()
            if page:
                page.update()
        except Exception as ex:
            pass

    def refresh_list():
        """Обновляет список объектов"""
        if search_value:
            all_objects = list(Object.select().where(Object.name.contains(search_value)))
        else:
            all_objects = list(Object.select())
        
        # Сортируем в Python
        if sort_by_name:
            all_objects.sort(key=lambda x: x.name.lower(), reverse=not sort_ascending)
        else:
            # Сортируем по минимальной ставке
            def get_min_rate(obj):
                rates = list(obj.rates)
                return min([float(r.rate) for r in rates]) if rates else 0
            all_objects.sort(key=get_min_rate, reverse=not sort_ascending)
        
        # Пагинация
        start = current_page * page_size
        end = start + page_size
        objects_list = all_objects[start:end]
        
        objects_list_view.controls.clear()
        for obj in objects_list:
            objects_list_view.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.BUSINESS),
                        title=ft.Text(obj.name, weight="bold"),
                        subtitle=ft.Text(get_object_info(obj)),
                        trailing=ft.IconButton(
                            icon=ft.Icons.EDIT,
                            on_click=lambda e, object_data=obj: show_edit_dialog(object_data)
                        ),
                        on_click=lambda e, object_data=obj: show_edit_dialog(object_data)
                    ),
                    margin=ft.margin.only(left=-30)
                )
            )
        
        if page:
            page.update()

    def get_object_info(obj):
        addresses = list(obj.addresses)
        rates = list(obj.rates)
        
        addr_text = addresses[0].address if addresses else "Нет адресов"
        if len(addresses) > 1:
            addr_text += f" (+{len(addresses)-1})"
        
        if rates:
            min_rate = min([float(r.rate) for r in rates])
            max_rate = max([float(r.rate) for r in rates])
            if min_rate == max_rate:
                rate_text = f"{min_rate:.2f} ₽/ч"
            else:
                rate_text = f"{min_rate:.2f}-{max_rate:.2f} ₽/ч"
        else:
            rate_text = "Нет ставок"
        
        return f"{addr_text} • {rate_text}"

    def on_search_change(e):
        nonlocal search_value, current_page
        search_value = e.control.value.strip()
        current_page = 0
        refresh_list()
        if page:
            page.update()
    
    def prev_page(e):
        nonlocal current_page
        if current_page > 0:
            current_page -= 1
            refresh_list()
            if page:
                page.update()
    
    def next_page(e):
        nonlocal current_page
        current_page += 1
        refresh_list()
        if page:
            page.update()
    
    def sort_by_name_click(e):
        nonlocal sort_by_name, sort_ascending, current_page
        if sort_by_name:
            sort_ascending = not sort_ascending
        else:
            sort_by_name = True
            sort_ascending = True
        current_page = 0
        refresh_list()
        if page:
            page.update()
    
    def sort_by_rate_click(e):
        nonlocal sort_by_name, sort_ascending, current_page
        if not sort_by_name:
            sort_ascending = not sort_ascending
        else:
            sort_by_name = False
            sort_ascending = True
        current_page = 0
        refresh_list()
        if page:
            page.update()
    
    refresh_list()
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Объекты", size=24, weight="bold"),
                    ft.ElevatedButton(
                        "Добавить объект",
                        icon=ft.Icons.ADD,
                        on_click=show_add_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Row([
                ft.TextField(
                    label="Поиск по названию",
                    width=300,
                    on_change=on_search_change,
                    autofocus=False,
                    dense=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_UPWARD if (sort_by_name and sort_ascending) else ft.Icons.ARROW_DOWNWARD if sort_by_name else ft.Icons.ABC,
                    tooltip=f"По названию {'↑' if sort_ascending else '↓'}" if sort_by_name else "Сортировка по названию",
                    on_click=sort_by_name_click
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_UPWARD if (not sort_by_name and sort_ascending) else ft.Icons.ARROW_DOWNWARD if not sort_by_name else ft.Icons.ATTACH_MONEY,
                    tooltip=f"По мин. ставке {'↑' if sort_ascending else '↓'}" if not sort_by_name else "Сортировка по мин. ставке",
                    on_click=sort_by_rate_click
                ),
            ], alignment=ft.MainAxisAlignment.START),
            objects_list_view,
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=prev_page
                ),
                ft.Text(f"Страница {current_page + 1}"),
                ft.IconButton(
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=next_page
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ],
        spacing=10,
        expand=True,
    )