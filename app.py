import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QGroupBox, QComboBox, QTextEdit,
                               QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView,
                               QRadioButton, QButtonGroup, QScrollArea, QFrame, QSizePolicy,
                               QGridLayout, QTableView)
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QIntValidator

from book import Book, generate_books, save_books, load_books

DATA_FILE = "data/books.json"

class BookTableModel(QAbstractTableModel):
    def __init__(self, books):
        super().__init__()
        self.books = books
        self.columns = ["Title", "Year", "Author", "Genre", "Language"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.books)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        book = self.books[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return book.title
            if col == 1: return book.year
            if col == 2: return book.author
            if col == 3: return book.genre
            if col == 4: return book.language

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.columns[section]
        return None

    def add_book(self, book):
        self.beginInsertRows(QModelIndex(), len(self.books), len(self.books))
        self.books.append(book)
        self.endInsertRows()

class BookFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.filter_title = ""
        self.filter_author = ""
        self.min_year = None
        self.max_year = None
        self.filter_genre = "All"
        self.filter_language = "All"

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        idx_title = model.index(source_row, 0, source_parent)
        idx_year = model.index(source_row, 1, source_parent)
        idx_author = model.index(source_row, 2, source_parent)
        idx_genre = model.index(source_row, 3, source_parent)
        idx_lang = model.index(source_row, 4, source_parent)

        title = model.data(idx_title, Qt.ItemDataRole.DisplayRole)
        year = model.data(idx_year, Qt.ItemDataRole.DisplayRole)
        author = model.data(idx_author, Qt.ItemDataRole.DisplayRole)
        genre = model.data(idx_genre, Qt.ItemDataRole.DisplayRole)
        lang = model.data(idx_lang, Qt.ItemDataRole.DisplayRole)

        if self.filter_title and self.filter_title.lower() not in title.lower():
            return False
        if self.filter_author and self.filter_author.lower() not in author.lower():
            return False
        if self.min_year is not None and year < self.min_year:
            return False
        if self.max_year is not None and year > self.max_year:
            return False
        if self.filter_genre != "All" and genre != self.filter_genre:
            return False
        if self.filter_language != "All" and lang != self.filter_language:
            return False

        return True

    def set_filter_title(self, text):
        self.filter_title = text
        self.invalidateFilter()

    def set_filter_author(self, text):
        self.filter_author = text
        self.invalidateFilter()

    def set_min_year(self, val):
        self.min_year = val
        self.invalidateFilter()

    def set_max_year(self, val):
        self.max_year = val
        self.invalidateFilter()

    def set_filter_genre(self, text):
        self.filter_genre = text
        self.invalidateFilter()

    def set_filter_language(self, text):
        self.filter_language = text
        self.invalidateFilter()

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

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        self.setWindowTitle("Book Manager (PySide6)")
        self.resize(1200, 800)

        # Data Loading
        self.books = load_books(DATA_FILE)
        if not self.books:
            self.books = generate_books(50_000)
            save_books(self.books, DATA_FILE)

        self.unique_genres = sorted(list(set(b.genre for b in self.books)))
        self.unique_languages = sorted(list(set(b.language for b in self.books)))

        self.current_sort_column = -1
        self.current_sort_order = Qt.SortOrder.AscendingOrder

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
        filter_layout = QGridLayout()

        # Row 1: Title, Author
        self.filter_title = QLineEdit()
        self.filter_title.setPlaceholderText("Filter Title")
        self.filter_title.textChanged.connect(self.update_filters)

        self.filter_author = QLineEdit()
        self.filter_author.setPlaceholderText("Filter Author")
        self.filter_author.textChanged.connect(self.update_filters)

        filter_layout.addWidget(QLabel("Title:"), 0, 0)
        filter_layout.addWidget(self.filter_title, 0, 1)
        filter_layout.addWidget(QLabel("Author:"), 0, 2)
        filter_layout.addWidget(self.filter_author, 0, 3)

        # Row 2: Year Range
        self.filter_year_min = QLineEdit()
        self.filter_year_min.setPlaceholderText("Min")
        self.filter_year_min.setValidator(QIntValidator())
        self.filter_year_min.textChanged.connect(self.update_filters)

        self.filter_year_max = QLineEdit()
        self.filter_year_max.setPlaceholderText("Max")
        self.filter_year_max.setValidator(QIntValidator())
        self.filter_year_max.textChanged.connect(self.update_filters)

        filter_layout.addWidget(QLabel("Year Min:"), 1, 0)
        filter_layout.addWidget(self.filter_year_min, 1, 1)
        filter_layout.addWidget(QLabel("Max:"), 1, 2)
        filter_layout.addWidget(self.filter_year_max, 1, 3)

        # Row 3: Genre, Language
        self.filter_genre = QComboBox()
        self.filter_genre.addItem("All")
        self.filter_genre.addItems(self.unique_genres)
        self.filter_genre.currentTextChanged.connect(self.update_filters)

        self.filter_lang = QComboBox()
        self.filter_lang.addItem("All")
        self.filter_lang.addItems(self.unique_languages)
        self.filter_lang.currentTextChanged.connect(self.update_filters)

        filter_layout.addWidget(QLabel("Genre:"), 2, 0)
        filter_layout.addWidget(self.filter_genre, 2, 1)
        filter_layout.addWidget(QLabel("Language:"), 2, 2)
        filter_layout.addWidget(self.filter_lang, 2, 3)

        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)

        # 3. Table
        self.model = BookTableModel(self.books)
        self.proxy_model = BookFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
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

        # Initial Population - Filters
        self.update_filters()

    def toggle_column(self, index, checked):
        self.table.setColumnHidden(index, not checked)

    def update_filters(self):
        self.proxy_model.set_filter_title(self.filter_title.text())
        self.proxy_model.set_filter_author(self.filter_author.text())

        try:
            min_y = int(self.filter_year_min.text())
        except ValueError:
            min_y = None
        self.proxy_model.set_min_year(min_y)

        try:
            max_y = int(self.filter_year_max.text())
        except ValueError:
            max_y = None
        self.proxy_model.set_max_year(max_y)

        self.proxy_model.set_filter_genre(self.filter_genre.currentText())
        self.proxy_model.set_filter_language(self.filter_lang.currentText())

    def on_selection_changed(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return

        # Get the row of the selected item
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        book = self.model.books[source_index.row()]
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

    def save_and_update(self, book):
        self.model.add_book(book)
        save_books(self.model.books, DATA_FILE)

        # Update dropdowns
        if book.genre not in self.unique_genres:
            self.unique_genres.append(book.genre)
            self.unique_genres.sort()
            self.filter_genre.addItem(book.genre)

        if book.language not in self.unique_languages:
            self.unique_languages.append(book.language)
            self.unique_languages.sort()
            self.filter_lang.addItem(book.language)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookManagerWindow()
    window.show()
    sys.exit(app.exec())
