import flet as ft
from book import Book, generate_books, save_books, load_books
import os

# Constants
DATA_FILE = "books.json"

def main(page: ft.Page):
    page.title = "Book Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    # Load data
    books = load_books(DATA_FILE)
    if not books:
        books = generate_books(50)
        save_books(books, DATA_FILE)

    # --- State ---
    # We will keep track of visibility of columns
    column_visibility = {
        "title": True,
        "year": True,
        "author": True,
        "genre": True,
        "language": True,
    }

    # For sorting
    current_sort_column_index = None
    sort_ascending = True

    # --- Components ---

    # Description Area
    description_text = ft.Text("Select a book to see description.", size=16)
    description_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Description", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                description_text
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=10,
        padding=10,
        expand=True,
    )

    # Table
    def on_sort(e):
        nonlocal sort_ascending, current_sort_column_index

        idx = e.column_index
        if current_sort_column_index == idx:
            sort_ascending = not sort_ascending
        else:
            sort_ascending = True
            current_sort_column_index = idx

        # Get the key to sort by
        header_text = books_table.columns[idx].label.value.lower()

        # Sort books
        books.sort(key=lambda b: getattr(b, header_text), reverse=not sort_ascending)

        # Update arrows
        books_table.sort_column_index = idx
        books_table.sort_ascending = sort_ascending

        update_table()
        page.update()

    books_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Title"), on_sort=on_sort),
            ft.DataColumn(ft.Text("Year"), numeric=True, on_sort=on_sort),
            ft.DataColumn(ft.Text("Author"), on_sort=on_sort),
            ft.DataColumn(ft.Text("Genre"), on_sort=on_sort),
            ft.DataColumn(ft.Text("Language"), on_sort=on_sort),
        ],
        rows=[],
        border=ft.border.all(1, ft.Colors.GREY_400),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_400),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_400),
        heading_row_color=ft.Colors.BLUE_GREY_50,
    )

    def on_select_book(e):
        # e.control is the DataRow
        # We need to find which book corresponds to this row.
        # Since we rebuild rows on sort/add, we can store the book in the row's data property if available,
        # or just use the index if we are careful.
        # A safer way: store the book object in the data property of the row.
        selected_book = e.control.data
        description_text.value = selected_book.description
        page.update()

    def update_table():
        # Rebuild rows based on 'books' list and visibility
        # Note: DataColumn visibility hides the whole column.

        # Update column visibility
        cols = ["title", "year", "author", "genre", "language"]
        for i, col_key in enumerate(cols):
            books_table.columns[i].visible = column_visibility[col_key]

        rows = []
        for book in books:
            cells = [
                ft.DataCell(ft.Text(book.title)),
                ft.DataCell(ft.Text(str(book.year))),
                ft.DataCell(ft.Text(book.author)),
                ft.DataCell(ft.Text(book.genre)),
                ft.DataCell(ft.Text(book.language)),
            ]
            rows.append(
                ft.DataRow(
                    cells=cells,
                    on_select_changed=on_select_book,
                    data=book
                )
            )
        books_table.rows = rows
        page.update()

    # Checkboxes for visibility
    def on_column_check(e, col_name):
        column_visibility[col_name] = e.control.value
        update_table()

    filter_row = ft.Row(
        controls=[
            ft.Checkbox(label="Title", value=True, on_change=lambda e: on_column_check(e, "title")),
            ft.Checkbox(label="Year", value=True, on_change=lambda e: on_column_check(e, "year")),
            ft.Checkbox(label="Author", value=True, on_change=lambda e: on_column_check(e, "author")),
            ft.Checkbox(label="Genre", value=True, on_change=lambda e: on_column_check(e, "genre")),
            ft.Checkbox(label="Language", value=True, on_change=lambda e: on_column_check(e, "language")),
        ]
    )

    # Add Book Form Fields
    txt_title = ft.TextField(label="Title")
    txt_year = ft.TextField(label="Year", keyboard_type=ft.KeyboardType.NUMBER)
    txt_author = ft.TextField(label="Author")
    txt_genre = ft.TextField(label="Genre")
    txt_language = ft.TextField(label="Language")

    # We need a description for new books too? The prompt says "generate random description for each book to have text to put in description".
    # It also says "opens area to fill in book's fields". Usually manual entry implies user enters description too,
    # but the prompt focuses on generated 50 books.
    # "Windows has button to add new book, it opens area to fill in book's fields... so generate random description for each book..."
    # I will assume for manually added books, we generate a random description or leave it empty.
    # Or I can add a field for it. Given the instruction, I'll generate one or add a field.
    # I'll add a field for description but pre-fill it or leave it optional.
    # Actually, to keep the form simple as per prompt "Book has title, year, author, genre, language",
    # and "generate random description for each book", maybe new books get a placeholder description?
    # I will add a description field to the add form for completeness.
    txt_desc = ft.TextField(label="Description", multiline=True, min_lines=3)

    def add_book_action(e):
        try:
            year_val = int(txt_year.value)
        except ValueError:
            year_val = 0 # or handle error

        new_book = Book(
            title=txt_title.value,
            year=year_val,
            author=txt_author.value,
            genre=txt_genre.value,
            language=txt_language.value,
            description=txt_desc.value if txt_desc.value else "No description provided."
        )
        books.append(new_book)
        save_books(books, DATA_FILE)
        update_table()

        # Clear fields
        txt_title.value = ""
        txt_year.value = ""
        txt_author.value = ""
        txt_genre.value = ""
        txt_language.value = ""
        txt_desc.value = ""

        # If inside dialog, close it
        if dlg_modal.open:
            dlg_modal.open = False
        page.update()

    btn_add = ft.ElevatedButton("Add Book", on_click=add_book_action)

    # Form Layouts
    form_column = ft.Column(
        controls=[
            ft.Text("Add New Book", size=20, weight=ft.FontWeight.BOLD),
            txt_title,
            txt_year,
            txt_author,
            txt_genre,
            txt_language,
            txt_desc,
            btn_add
        ],
        scroll=ft.ScrollMode.AUTO
    )

    # Modal Dialog
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add New Book"),
        content=ft.Column([
            txt_title, txt_year, txt_author, txt_genre, txt_language, txt_desc
        ], height=400, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: setattr(dlg_modal, 'open', False) or page.update()),
            ft.TextButton("Add", on_click=add_book_action),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_dlg(e):
        # We need to make sure the fields are not parented by the inline form if we want to show them in dialog
        # Flet controls can only have one parent.
        # So we need two sets of controls OR we reparent them.
        # Reparenting is tricky. Easier to have the form construction be dynamic or just share the logic.
        # But wait, the prompt implies ONE form area that switches location or a switch that changes behavior.
        # "Add switch to choose the area of adding book information... 2 variants: popup windows and area on the top right"

        # If I use the SAME TextFields, I must remove them from one container and add to another.
        # Let's try to keep it simple:
        # The "Right Top" area will verify the mode.
        # If Inline: it shows the form.
        # If Popup: it shows a button "Open Form".

        # But the Form itself (the TextFields) must move.
        # Let's implement a function to render the Right Top Area.
        render_add_area()

        if add_mode_switch.value: # Popup mode
            page.dialog = dlg_modal
            dlg_modal.open = True
            page.update()

    # Switch for Add Mode
    # False = Inline, True = Popup
    add_mode_switch = ft.Switch(label="Popup Mode", value=False)

    add_area_container = ft.Container(
        padding=10,
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=10,
        expand=True
    )

    def render_add_area(e=None):
        # Clear current content
        add_area_container.content = None

        # Important: To avoid "Duplicate Control ID" errors when moving controls between
        # the page tree (Inline) and the dialog tree (Popup), we must carefully detach them.

        # First, ensure controls are detached from the dialog if they were there
        dlg_modal.content.controls.clear()

        if add_mode_switch.value:
            # Popup Mode
            # Assign fields to dialog content.
            dlg_modal.content.controls.extend([
                txt_title, txt_year, txt_author, txt_genre, txt_language, txt_desc
            ])

            add_area_container.content = ft.Column([
                ft.Row([ft.Text("Add Book Mode"), add_mode_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.ElevatedButton("Open Add Book Dialog", on_click=lambda _: setattr(dlg_modal, 'open', True) or page.update())
            ])
            page.dialog = dlg_modal
        else:
            # Inline Mode
            # Ensure we unset the dialog so it's not part of the tree anymore (conceptually)
            # or at least doesn't hold the controls.
            page.dialog = None

            # Fields go into the container
            add_area_container.content = ft.Column([
                ft.Row([ft.Text("Add Book Mode"), add_mode_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                txt_title,
                txt_year,
                txt_author,
                txt_genre,
                txt_language,
                txt_desc,
                btn_add
            ], scroll=ft.ScrollMode.AUTO)

        page.update()

    add_mode_switch.on_change = render_add_area

    # --- Layout Assembly ---

    # Initial Render of Add Area
    render_add_area()

    # Initial Table Update
    update_table()

    left_column = ft.Column(
        controls=[
            ft.Text("Books List", size=20, weight=ft.FontWeight.BOLD),
            filter_row,
            ft.Container(content=books_table, expand=True, padding=0) # Table inside scrollable container if needed
            # DataTable inside Column usually scrolls if Column is scrollable.
            # But simpler to put DataTable in a ListView or enable scroll on Column.
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    right_column = ft.Column(
        controls=[
            ft.Container(content=add_area_container, expand=1), # Top Right (Add) - using flex to split height
            ft.Container(content=description_container, expand=1) # Bottom Right (Description)
        ],
        expand=True
    )

    main_row = ft.Row(
        controls=[
            ft.Container(content=left_column, expand=2, padding=10), # Left takes 2/3 width
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_400),
            ft.Container(content=right_column, expand=1, padding=10)  # Right takes 1/3 width
        ],
        expand=True,
    )

    page.add(main_row)

if __name__ == "__main__":
    ft.app(target=main)
