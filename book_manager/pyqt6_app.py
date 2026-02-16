import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QGroupBox, QComboBox, QTextEdit,
                               QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView,
                               QRadioButton, QButtonGroup, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator

from book import Book, generate_books, save_books, load_books

DATA_FILE = "books.json"

class AddBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Book")
        self.resize(400, 300)

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        self.year_edit = QLineEdit()
        self.year_edit.setValidator(QIntValidator())
        self.author_edit = QLineEdit()
        self.genre_edit = QLineEdit()
        self.lang_edit = QLineEdit()
        self.desc_edit = QTextEdit()

        self.form_layout.addRow("Title:", self.title_edit)
        self.form_layout.addRow("Year:", self.year_edit)
        self.form_layout.addRow("Author:", self.author_edit)
        self.form_layout.addRow("Genre:", self.genre_edit)
        self.form_layout.addRow("Language:", self.lang_edit)
        self.form_layout.addRow("Description:", self.desc_edit)

        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        try:
            year = int(self.year_edit.text())
        except ValueError:
            year = 0

        return Book(
            title=self.title_edit.text(),
            year=year,
            author=self.author_edit.text(),
            genre=self.genre_edit.text(),
            language=self.lang_edit.text(),
            description=self.desc_edit.toPlainText() or "No description provided."
        )

class BookManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Manager (PyQt6)")
        self.resize(1200, 800)

        # Data Loading
        self.books = load_books(DATA_FILE)
        if not self.books:
            self.books = generate_books(50)
            save_books(self.books, DATA_FILE)

        self.unique_genres = sorted(list(set(b.genre for b in self.books)))
        self.unique_languages = sorted(list(set(b.language for b in self.books)))

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel (Table & Filters) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Column Visibility
        vis_group = QGroupBox("Show Columns")
        vis_layout = QHBoxLayout()
        self.col_checks = {}
        columns = ["Title", "Year", "Author", "Genre", "Language"]
        for i, col in enumerate(columns):
            chk = QCheckBox(col)
            chk.setChecked(True)
            chk.toggled.connect(lambda checked, idx=i: self.toggle_column(idx, checked))
            vis_layout.addWidget(chk)
            self.col_checks[col] = chk
        vis_group.setLayout(vis_layout)
        left_layout.addWidget(vis_group)

        # 2. Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout()

        # Row 1: Title, Author
        row1 = QHBoxLayout()
        self.filter_title = QLineEdit()
        self.filter_title.setPlaceholderText("Filter Title")
        self.filter_title.textChanged.connect(self.apply_filters)

        self.filter_author = QLineEdit()
        self.filter_author.setPlaceholderText("Filter Author")
        self.filter_author.textChanged.connect(self.apply_filters)

        row1.addWidget(QLabel("Title:"))
        row1.addWidget(self.filter_title)
        row1.addWidget(QLabel("Author:"))
        row1.addWidget(self.filter_author)
        filter_layout.addLayout(row1)

        # Row 2: Year Range
        row2 = QHBoxLayout()
        self.filter_year_min = QLineEdit()
        self.filter_year_min.setPlaceholderText("Min")
        self.filter_year_min.setValidator(QIntValidator())
        self.filter_year_min.textChanged.connect(self.apply_filters)

        self.filter_year_max = QLineEdit()
        self.filter_year_max.setPlaceholderText("Max")
        self.filter_year_max.setValidator(QIntValidator())
        self.filter_year_max.textChanged.connect(self.apply_filters)

        row2.addWidget(QLabel("Year Min:"))
        row2.addWidget(self.filter_year_min)
        row2.addWidget(QLabel("Max:"))
        row2.addWidget(self.filter_year_max)
        filter_layout.addLayout(row2)

        # Row 3: Genre, Language
        row3 = QHBoxLayout()
        self.filter_genre = QComboBox()
        self.filter_genre.addItem("All")
        self.filter_genre.addItems(self.unique_genres)
        self.filter_genre.currentTextChanged.connect(self.apply_filters)

        self.filter_lang = QComboBox()
        self.filter_lang.addItem("All")
        self.filter_lang.addItems(self.unique_languages)
        self.filter_lang.currentTextChanged.connect(self.apply_filters)

        row3.addWidget(QLabel("Genre:"))
        row3.addWidget(self.filter_genre)
        row3.addWidget(QLabel("Language:"))
        row3.addWidget(self.filter_lang)
        filter_layout.addLayout(row3)

        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)

        # 3. Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # Disable automatic sorting to handle interaction with hiding rows manually
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.table)

        # --- Right Panel (Add & Desc) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 4. Add Book Area
        add_group = QGroupBox("Add New Book")
        add_layout = QVBoxLayout()

        # Mode Switch
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.radio_inline = QRadioButton("Inline")
        self.radio_popup = QRadioButton("Popup")
        self.radio_inline.setChecked(True)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_inline)
        self.mode_group.addButton(self.radio_popup)
        self.mode_group.buttonToggled.connect(self.toggle_add_mode)

        mode_layout.addWidget(self.radio_inline)
        mode_layout.addWidget(self.radio_popup)
        mode_layout.addStretch()
        add_layout.addLayout(mode_layout)

        # Inline Form Container
        self.inline_widget = QWidget()
        self.inline_form = QFormLayout(self.inline_widget)

        self.add_title = QLineEdit()
        self.add_year = QLineEdit()
        self.add_year.setValidator(QIntValidator())
        self.add_author = QLineEdit()
        self.add_genre = QLineEdit()
        self.add_lang = QLineEdit()
        self.add_desc = QTextEdit()
        self.add_desc.setMaximumHeight(80)

        self.inline_form.addRow("Title:", self.add_title)
        self.inline_form.addRow("Year:", self.add_year)
        self.inline_form.addRow("Author:", self.add_author)
        self.inline_form.addRow("Genre:", self.add_genre)
        self.inline_form.addRow("Language:", self.add_lang)
        self.inline_form.addRow("Desc:", self.add_desc)

        self.btn_add_inline = QPushButton("Add Book")
        self.btn_add_inline.clicked.connect(self.add_book_inline)
        self.inline_form.addRow(self.btn_add_inline)

        add_layout.addWidget(self.inline_widget)

        # Popup Button Container
        self.popup_widget = QWidget()
        self.popup_widget.setVisible(False)
        popup_layout = QVBoxLayout(self.popup_widget)
        self.btn_open_popup = QPushButton("Open Add Book Dialog")
        self.btn_open_popup.clicked.connect(self.open_add_popup)
        popup_layout.addWidget(self.btn_open_popup)

        add_layout.addWidget(self.popup_widget)

        add_group.setLayout(add_layout)
        right_layout.addWidget(add_group)

        # 5. Description Area
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        self.desc_view = QTextEdit()
        self.desc_view.setReadOnly(True)
        self.desc_view.setText("Select a book to see description.")
        desc_layout.addWidget(self.desc_view)
        desc_group.setLayout(desc_layout)
        right_layout.addWidget(desc_group)

        # Layout Assembly
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 1)

        # Initial Population
        self.populate_table()

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for book in self.books:
            self.add_row(book)

        self.apply_filters()

    def add_row(self, book):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Items
        # Title
        item_title = QTableWidgetItem(book.title)
        item_title.setData(Qt.ItemDataRole.UserRole, book) # Store book object in first item
        self.table.setItem(row, 0, item_title)

        # Year (Sortable as number)
        item_year = QTableWidgetItem()
        item_year.setData(Qt.ItemDataRole.DisplayRole, book.year)
        self.table.setItem(row, 1, item_year)

        # Others
        self.table.setItem(row, 2, QTableWidgetItem(book.author))
        self.table.setItem(row, 3, QTableWidgetItem(book.genre))
        self.table.setItem(row, 4, QTableWidgetItem(book.language))

    def toggle_column(self, index, checked):
        self.table.setColumnHidden(index, not checked)

    def apply_filters(self):
        title_q = self.filter_title.text().lower()
        author_q = self.filter_author.text().lower()

        try:
            min_y = int(self.filter_year_min.text())
        except ValueError:
            min_y = None

        try:
            max_y = int(self.filter_year_max.text())
        except ValueError:
            max_y = None

        genre_q = self.filter_genre.currentText()
        lang_q = self.filter_lang.currentText()

        for row in range(self.table.rowCount()):
            book = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

            show = True
            if title_q and title_q not in book.title.lower(): show = False
            if show and author_q and author_q not in book.author.lower(): show = False
            if show and min_y is not None and book.year < min_y: show = False
            if show and max_y is not None and book.year > max_y: show = False
            if show and genre_q != "All" and book.genre != genre_q: show = False
            if show and lang_q != "All" and book.language != lang_q: show = False

            self.table.setRowHidden(row, not show)

    def on_selection_changed(self):
        items = self.table.selectedItems()
        if not items:
            return

        # Get the row of the selected item
        row = items[0].row()
        book = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.desc_view.setText(book.description)

    def toggle_add_mode(self, button, checked):
        if not checked: return
        is_inline = (button == self.radio_inline)
        self.inline_widget.setVisible(is_inline)
        self.popup_widget.setVisible(not is_inline)

    def add_book_inline(self):
        try:
            year = int(self.add_year.text())
        except ValueError:
            year = 0

        book = Book(
            title=self.add_title.text(),
            year=year,
            author=self.add_author.text(),
            genre=self.add_genre.text(),
            language=self.add_lang.text(),
            description=self.add_desc.toPlainText() or "No description provided."
        )
        self.save_and_update(book)

        # Clear fields
        self.add_title.clear()
        self.add_year.clear()
        self.add_author.clear()
        self.add_genre.clear()
        self.add_lang.clear()
        self.add_desc.clear()

    def open_add_popup(self):
        dlg = AddBookDialog(self)
        if dlg.exec():
            book = dlg.get_data()
            self.save_and_update(book)

    def sort_table(self, column_index):
        # Determine order
        current_order = self.table.horizontalHeader().sortIndicatorOrder()
        if self.table.horizontalHeader().sortIndicatorSection() != column_index:
            new_order = Qt.SortOrder.AscendingOrder
        else:
            new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder

        self.table.sortItems(column_index, new_order)
        self.table.horizontalHeader().setSortIndicator(column_index, new_order)

        # Re-apply filters after sort because rows moved
        self.apply_filters()

    def save_and_update(self, book):
        self.books.append(book)
        save_books(self.books, DATA_FILE)

        # Update dropdowns
        if book.genre not in self.unique_genres:
            self.unique_genres.append(book.genre)
            self.unique_genres.sort()
            self.filter_genre.addItem(book.genre)

        if book.language not in self.unique_languages:
            self.unique_languages.append(book.language)
            self.unique_languages.sort()
            self.filter_lang.addItem(book.language)

        # Add to table
        self.add_row(book)
        self.apply_filters() # Re-apply filters to newly added row

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookManagerWindow()
    window.show()
    sys.exit(app.exec())
