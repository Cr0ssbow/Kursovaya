import flet as ft
from database.models import Object, db

objects_table = None

def objects_page(page: ft.Page = None) -> ft.Column:
    sort_column = "name"
    sort_reverse = False
    global objects_table

    # Диалог и поля формы
    add_dialog = ft.AlertDialog(modal=True)
    name_field = ft.TextField(label="Название объекта", width=300)
    address_field = ft.TextField(label="Адрес объекта", width=300)
    description_field = ft.TextField(label="Описание объекта", multiline=True, width=300)

    def show_add_dialog(e):
        name_field.value = ""
        address_field.value = ""
        description_field.value = ""
        add_dialog.title = ft.Text("Добавить объект")
        add_dialog.content = ft.Column([
            name_field,
            address_field,
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
            address = address_field.value.strip()
            description = description_field.value.strip()
            if not name:
                raise ValueError("Название объекта обязательно!")
            with db.atomic():
                Object.create(name=name, address=address, description=description)
            close_add_dialog(e)
            refresh_table()
            if page:
                page.update()
        except Exception as ex:
            add_dialog.content = ft.Column([
                name_field,
                address_field,
                description_field,
                ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)
            ], spacing=10)
            if page:
                page.update()
    
    search_value = ""

    # Диалог редактирования
    edit_dialog = ft.AlertDialog(modal=True)
    edit_name = ft.TextField(label="Название объекта", width=300)
    edit_address = ft.TextField(label="Адрес объекта", width=300)
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
        refresh_table()
        if page:
            page.update()

    def show_edit_dialog(obj):
        edit_name.value = obj.name
        edit_address.value = obj.address
        edit_description.value = obj.description
        edit_dialog.title = ft.Text("Редактировать объект")
        edit_dialog.content = ft.Column([
            edit_name,
            edit_address,
            edit_description,
        ], spacing=10)
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
            new_address = edit_address.value.strip()
            new_description = edit_description.value.strip()
            if not new_name:
                raise ValueError("Название объекта обязательно!")
            with db.atomic():
                object_to_update = Object.get_by_id(object_id)
                object_to_update.name = new_name
                object_to_update.address = new_address
                object_to_update.description = new_description
                object_to_update.save()
            close_edit_dialog(None)
            refresh_table()
            if page:
                page.update()
        except Exception as ex:
            edit_dialog.content = ft.Column([
                edit_name,
                edit_address,
                edit_description,
                ft.Text(f"Ошибка: {ex}", color=ft.Colors.RED)
            ], spacing=10)
            if page:
                page.update()

    def refresh_table():
        """Обновляет данные в таблице с учетом поиска"""
        # db.connect(reuse_if_open=True) # Removed explicit connect
        if search_value:
            objects_list = list(Object.select().where(Object.name.contains(search_value)).order_by(Object.name))
        else:
            objects_list = list(Object.select().order_by(Object.name))
        
        def key(obj):
            if sort_column == "name":
                return obj.name
            return obj.name
        objects_list.sort(key=key, reverse=sort_reverse)
        objects_table.rows.clear()
        for obj in objects_list:
            objects_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(obj.name), on_tap=lambda e, object_data=obj: show_edit_dialog(object_data)),
                        ft.DataCell(ft.Text(obj.address)),
                        ft.DataCell(ft.Text(obj.description)),
                    ]
                )
            )
        if page:
            page.update()
        # db.close() # Removed explicit close

    def on_sort(col):
        nonlocal sort_column, sort_reverse
        if sort_column == col:
            sort_reverse = not sort_reverse
        else:
            sort_column = col
            sort_reverse = False
        refresh_table()
        if page:
            page.update()

    def on_search_change(e):
        nonlocal search_value
        search_value = e.control.value.strip()
        refresh_table()
        if page:
            page.update()
    
    # Создаем DataTable
    objects_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Название объекта", width=200), on_sort=lambda _: on_sort("name")),
            ft.DataColumn(ft.Text("Адрес объекта", width=300)),
            ft.DataColumn(ft.Text("Описание", width=400)),
        ],
        rows=[],
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
        heading_row_height=70,
        data_row_min_height=50,
        data_row_max_height=100,
        column_spacing=10,
        width=4000,
        height=4000
    )
    refresh_table()
    
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
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=objects_table,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10,
                expand=True,
            ),
        ],
        spacing=10,
        expand=True,
    )
