import os
from book import Book, generate_books, save_books, load_books

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.switch import Switch
from kivy.metrics import dp
from kivy.core.window import Window

DATA_FILE = "books.json"

class BookManagerApp(App):
    def build(self):
        self.title = "Book Manager (Kivy)"
        Window.clearcolor = (0.95, 0.95, 0.95, 1) # Light background

        # Data State
        self.books = load_books(DATA_FILE)
        if not self.books:
            self.books = generate_books(50)
            save_books(self.books, DATA_FILE)

        self.filtered_books = list(self.books)
        self.selected_book = None

        # View State
        self.column_visibility = {
            "Title": True,
            "Year": True,
            "Author": True,
            "Genre": True,
            "Language": True
        }
        self.sort_column = None
        self.sort_descending = False

        # Unique values for dropdowns
        self.unique_genres = sorted(list(set(b.genre for b in self.books)))
        self.unique_languages = sorted(list(set(b.language for b in self.books)))

        # --- Layouts ---
        root = BoxLayout(orientation='horizontal', padding=10, spacing=10)

        # Left Panel (Table & Filters)
        left_panel = BoxLayout(orientation='vertical', spacing=10, size_hint_x=0.66)

        # 1. Filters Area
        filter_area = self._build_filter_area()
        left_panel.add_widget(filter_area)

        # 2. Table Header
        self.header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=2)
        left_panel.add_widget(self.header_layout)

        # 3. Table Rows (Scrollable)
        self.scroll_view = ScrollView()
        self.table_content = GridLayout(cols=1, spacing=2, size_hint_y=None)
        self.table_content.bind(minimum_height=self.table_content.setter('height'))
        self.scroll_view.add_widget(self.table_content)
        left_panel.add_widget(self.scroll_view)

        root.add_widget(left_panel)

        # Right Panel (Add & Desc)
        right_panel = BoxLayout(orientation='vertical', spacing=10, size_hint_x=0.34)

        # 4. Add Book Area
        self.add_area_container = BoxLayout(orientation='vertical', size_hint_y=0.5)
        right_panel.add_widget(self.add_area_container)

        # 5. Description Area
        desc_area = BoxLayout(orientation='vertical', size_hint_y=0.5)
        desc_area.add_widget(Label(text="[b]Description[/b]", markup=True, size_hint_y=None, height=dp(30), color=(0,0,0,1)))
        self.desc_input = TextInput(text="Select a book to see description.", readonly=True, background_color=(1,1,1,1), foreground_color=(0,0,0,1))
        desc_area.add_widget(self.desc_input)
        right_panel.add_widget(desc_area)

        root.add_widget(right_panel)

        # Initial Render
        self._render_add_area_mode() # Setup add area
        self._update_table()

        return root

    def _build_filter_area(self):
        container = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200), spacing=5)

        # Visibility Toggles
        vis_label = Label(text="Show Columns:", size_hint_y=None, height=dp(20), color=(0,0,0,1), halign='left', text_size=(Window.width * 0.6, None))
        container.add_widget(vis_label)

        vis_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        for key in self.column_visibility:
            box = BoxLayout(orientation='horizontal')
            chk = CheckBox(active=True, color=(0,0,0,1))
            chk.bind(active=lambda instance, val, k=key: self._on_vis_change(k, val))
            box.add_widget(chk)
            box.add_widget(Label(text=key, color=(0,0,0,1)))
            vis_row.add_widget(box)
        container.add_widget(vis_row)

        # Content Filters
        container.add_widget(Label(text="Filters:", size_hint_y=None, height=dp(20), color=(0,0,0,1)))

        # Title & Author
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=5)
        self.filter_title = TextInput(hint_text="Filter Title", multiline=False, write_tab=False)
        self.filter_title.bind(text=self._on_filter_change)
        self.filter_author = TextInput(hint_text="Filter Author", multiline=False, write_tab=False)
        self.filter_author.bind(text=self._on_filter_change)
        row1.add_widget(self.filter_title)
        row1.add_widget(self.filter_author)
        container.add_widget(row1)

        # Year Range
        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=5)
        self.filter_min_year = TextInput(hint_text="Min Year", multiline=False, input_filter='int', write_tab=False)
        self.filter_min_year.bind(text=self._on_filter_change)
        self.filter_max_year = TextInput(hint_text="Max Year", multiline=False, input_filter='int', write_tab=False)
        self.filter_max_year.bind(text=self._on_filter_change)
        row2.add_widget(self.filter_min_year)
        row2.add_widget(self.filter_max_year)
        container.add_widget(row2)

        # Genre & Language
        row3 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=5)
        self.filter_genre = Spinner(text='All', values=['All'] + self.unique_genres)
        self.filter_genre.bind(text=self._on_filter_change)
        self.filter_lang = Spinner(text='All', values=['All'] + self.unique_languages)
        self.filter_lang.bind(text=self._on_filter_change)
        row3.add_widget(self.filter_genre)
        row3.add_widget(self.filter_lang)
        container.add_widget(row3)

        return container

    def _render_add_area_mode(self):
        # We need to rebuild the add area based on mode
        self.add_area_container.clear_widgets()

        # Mode Switch Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        header.add_widget(Label(text="Add Book Mode:", color=(0,0,0,1)))
        self.mode_switch = Switch(active=False) # False=Inline, True=Popup
        self.mode_switch.bind(active=lambda i, v: self._render_add_area_mode())
        header.add_widget(self.mode_switch)
        header.add_widget(Label(text="Popup", color=(0,0,0,1)))

        self.add_area_container.add_widget(header)

        # Inputs creation (reused)
        self.input_title = TextInput(hint_text="Title", multiline=False, write_tab=False, size_hint_y=None, height=dp(35))
        self.input_year = TextInput(hint_text="Year", multiline=False, input_filter='int', write_tab=False, size_hint_y=None, height=dp(35))
        self.input_author = TextInput(hint_text="Author", multiline=False, write_tab=False, size_hint_y=None, height=dp(35))
        self.input_genre = TextInput(hint_text="Genre", multiline=False, write_tab=False, size_hint_y=None, height=dp(35))
        self.input_lang = TextInput(hint_text="Language", multiline=False, write_tab=False, size_hint_y=None, height=dp(35))
        self.input_desc = TextInput(hint_text="Description", multiline=True, size_hint_y=None, height=dp(70))

        add_btn = Button(text="Add Book", size_hint_y=None, height=dp(40))
        add_btn.bind(on_release=self._add_book)

        controls = [
            self.input_title, self.input_year, self.input_author,
            self.input_genre, self.input_lang, self.input_desc, add_btn
        ]

        if self.mode_switch.active:
            # Popup Mode: Show button to open popup
            open_btn = Button(text="Open Add Book Dialog", size_hint_y=None, height=dp(40))
            open_btn.bind(on_release=lambda x: self._open_popup(controls))
            self.add_area_container.add_widget(open_btn)
        else:
            # Inline Mode
            form = BoxLayout(orientation='vertical', spacing=5)
            for c in controls:
                if c.parent:
                    c.parent.remove_widget(c)
                form.add_widget(c)
            # spacer
            form.add_widget(Label())
            self.add_area_container.add_widget(form)

    def _open_popup(self, controls):
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        # We need to remove parent if they are attached elsewhere, but we create new instance layout for them
        # Note: In Kivy a widget can only have one parent.
        # Since we create them fresh in _render_add_area_mode, if we switch mode, they are lost?
        # No, I bound them to self variables.
        # If I switch mode, _render_add_area_mode clears widgets, so they are detached.
        # So we can safely add them to the popup content.

        for c in controls:
            if c.parent:
                c.parent.remove_widget(c)
            content.add_widget(c)

        # Add cancel button for popup
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=dp(40))
        content.add_widget(cancel_btn)

        self.popup = Popup(title="Add New Book", content=content, size_hint=(0.8, 0.8))
        cancel_btn.bind(on_release=self.popup.dismiss)

        # We need to make sure the "Add Book" button also closes popup
        # The add_btn is the last in 'controls' list (index 6)
        controls[-1].unbind(on_release=self._add_book) # clear previous binds to avoid double calls
        controls[-1].bind(on_release=lambda x: [self._add_book(x), self.popup.dismiss()])

        self.popup.open()

    def _add_book(self, instance):
        title = self.input_title.text
        if not title: return

        try:
            year = int(self.input_year.text)
        except:
            year = 0

        new_book = Book(
            title=title,
            year=year,
            author=self.input_author.text,
            genre=self.input_genre.text,
            language=self.input_lang.text,
            description=self.input_desc.text or "No description provided."
        )

        self.books.append(new_book)
        save_books(self.books, DATA_FILE)

        # Clear inputs
        self.input_title.text = ""
        self.input_year.text = ""
        self.input_author.text = ""
        self.input_genre.text = ""
        self.input_lang.text = ""
        self.input_desc.text = ""

        # Update dropdowns if needed
        if new_book.genre not in self.unique_genres:
            self.unique_genres.append(new_book.genre)
            self.unique_genres.sort()
            self.filter_genre.values = ['All'] + self.unique_genres

        if new_book.language not in self.unique_languages:
            self.unique_languages.append(new_book.language)
            self.unique_languages.sort()
            self.filter_lang.values = ['All'] + self.unique_languages

        self._on_filter_change()

    def _on_vis_change(self, key, is_active):
        self.column_visibility[key] = is_active
        self._update_table()

    def _on_filter_change(self, *args):
        # Filter logic
        title_q = self.filter_title.text.lower()
        author_q = self.filter_author.text.lower()
        min_y = int(self.filter_min_year.text) if self.filter_min_year.text else None
        max_y = int(self.filter_max_year.text) if self.filter_max_year.text else None
        genre_q = self.filter_genre.text
        lang_q = self.filter_lang.text

        self.filtered_books = []
        for b in self.books:
            if title_q and title_q not in b.title.lower(): continue
            if author_q and author_q not in b.author.lower(): continue
            if min_y is not None and b.year < min_y: continue
            if max_y is not None and b.year > max_y: continue
            if genre_q != 'All' and b.genre != genre_q: continue
            if lang_q != 'All' and b.language != lang_q: continue

            self.filtered_books.append(b)

        self._update_table()

    def _sort_books(self):
        if not self.sort_column: return

        key_map = {
            "Title": "title",
            "Year": "year",
            "Author": "author",
            "Genre": "genre",
            "Language": "language"
        }
        attr = key_map.get(self.sort_column)
        if attr:
            self.filtered_books.sort(key=lambda b: getattr(b, attr), reverse=self.sort_descending)

    def _update_table(self):
        # 1. Sort
        self._sort_books()

        # 2. Rebuild Header
        self.header_layout.clear_widgets()
        visible_cols = [k for k,v in self.column_visibility.items() if v]

        if not visible_cols:
            self.table_content.clear_widgets()
            return

        col_width = 1.0 / len(visible_cols)

        for col in visible_cols:
            txt = col
            if self.sort_column == col:
                txt += " (Desc)" if self.sort_descending else " (Asc)"

            btn = Button(text=txt, size_hint_x=col_width, background_normal='', background_color=(0.8, 0.8, 0.8, 1), color=(0,0,0,1))
            btn.bind(on_release=lambda x, c=col: self._on_header_click(c))
            self.header_layout.add_widget(btn)

        # 3. Rebuild Rows
        self.table_content.clear_widgets()
        self.table_content.cols = 1 # We use rows of BoxLayouts

        for book in self.filtered_books:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=2)

            # Row selection logic (Clickable row)
            # Use a Button invisible background or ToggleButton
            # But we have multiple cells.
            # Easiest way: A BoxLayout of Labels, but touch handling is manual.
            # Better: A BoxLayout with a transparent Button on top?
            # Or make each Cell a Button with same callback.

            for col in visible_cols:
                val = ""
                if col == "Title": val = book.title
                elif col == "Year": val = str(book.year)
                elif col == "Author": val = book.author
                elif col == "Genre": val = book.genre
                elif col == "Language": val = book.language

                cell = Button(text=val, size_hint_x=col_width, background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
                cell.bind(on_release=lambda x, b=book: self._select_book(b))
                row.add_widget(cell)

            self.table_content.add_widget(row)

    def _on_header_click(self, col_name):
        if self.sort_column == col_name:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = col_name
            self.sort_descending = False
        self._update_table()

    def _select_book(self, book):
        self.selected_book = book
        self.desc_input.text = book.description

if __name__ == '__main__':
    BookManagerApp().run()
