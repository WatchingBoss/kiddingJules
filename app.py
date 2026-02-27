import sys
import polars as pl
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QGroupBox, QComboBox, QTextEdit,
                               QDialog, QFormLayout, QDialogButtonBox, QAbstractItemView,
                               QRadioButton, QButtonGroup, QScrollArea, QFrame, QSizePolicy,
                               QGridLayout, QTableView)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QIntValidator

from book import Book, generate_books, save_books, load_books

DATA_FILE = "data/books.json"

class BookTableModel(QAbstractTableModel):
    def __init__(self, books):
        super().__init__()
        # Define schema to handle empty list correctly
        self.schema = {
            "title": pl.Utf8,
            "year": pl.Int64,
            "author": pl.Utf8,
            "genre": pl.Utf8,
            "language": pl.Utf8,
            "description": pl.Utf8
        }
        data = [b.to_dict() for b in books] if books else []
        self.full_df = pl.DataFrame(data, schema=self.schema)
        self.display_df = self.full_df.clone()
        self.columns = ["Title", "Year", "Author", "Genre", "Language"]
        self.col_map = {0: "title", 1: "year", 2: "author", 3: "genre", 4: "language"}
        
        self.current_sort_col = -1
        self.current_sort_order = Qt.SortOrder.AscendingOrder

    def rowCount(self, parent=QModelIndex()):
        return self.display_df.height

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            col_name = self.col_map.get(index.column())
            if col_name:
                return str(self.display_df.item(index.row(), col_name))

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.columns[section]
        return None

    def sort(self, column, order):
        self.current_sort_col = column
        self.current_sort_order = order
        self._apply_sort()

    def _apply_sort(self):
        col_name = self.col_map.get(self.current_sort_col)
        if not col_name:
            return
            
        self.beginResetModel()
        descending = (self.current_sort_order == Qt.SortOrder.DescendingOrder)
        self.display_df = self.display_df.sort(col_name, descending=descending)
        self.endResetModel()

    def add_book(self, book):
        # We append to full_df. The view update happens when filters are reapplied/refreshed.
        # Ensure schema matches to avoid type issues on append
        new_row = pl.DataFrame([book.to_dict()], schema=self.schema)
        # Use simple concat (creating new DF) as Polars is immutable
        try:
            self.full_df = pl.concat([self.full_df, new_row], how="vertical")
        except Exception as e:
            # Fallback for empty df case if schema differs slightly (shouldn't happen with explicit schema)
             self.full_df = pl.concat([self.full_df, new_row], how="vertical_relaxed")
        
        # We don't automatically update display_df here; the main window calls update_filters()
        
    def apply_filters(self, title, author, min_year, max_year, genre, lang):
        # We don't call beginResetModel here because _apply_sort will do it.
        # But we need to update display_df first.
        
        expr = True
        
        if title:
            expr &= pl.col("title").str.to_lowercase().str.contains(title.lower())
        if author:
            expr &= pl.col("author").str.to_lowercase().str.contains(author.lower())
        if min_year is not None:
            expr &= pl.col("year") >= min_year
        if max_year is not None:
            expr &= pl.col("year") <= max_year
        if genre and genre != "All":
            expr &= pl.col("genre") == genre
        if lang and lang != "All":
            expr &= pl.col("language") == lang
            
        if isinstance(expr, bool) and expr is True:
            self.display_df = self.full_df
        else:
            self.display_df = self.full_df.filter(expr)
            
        # Re-apply sort if active
        if self.current_sort_col != -1:
            self._apply_sort()
        else:
            # If no sort, we still need to notify views of change
            self.beginResetModel()
            self.endResetModel()


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

        # Filter Debouncing Timer
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)
        self.debounce_timer.timeout.connect(self.update_filters)

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
        self.filter_title.textChanged.connect(lambda: self.debounce_timer.start())

        self.filter_author = QLineEdit()
        self.filter_author.setPlaceholderText("Filter Author")
        self.filter_author.textChanged.connect(lambda: self.debounce_timer.start())

        filter_layout.addWidget(QLabel("Title:"), 0, 0)
        filter_layout.addWidget(self.filter_title, 0, 1)
        filter_layout.addWidget(QLabel("Author:"), 0, 2)
        filter_layout.addWidget(self.filter_author, 0, 3)

        # Row 2: Year Range
        self.filter_year_min = QLineEdit()
        self.filter_year_min.setPlaceholderText("Min")
        self.filter_year_min.setValidator(QIntValidator())
        self.filter_year_min.textChanged.connect(lambda: self.debounce_timer.start())

        self.filter_year_max = QLineEdit()
        self.filter_year_max.setPlaceholderText("Max")
        self.filter_year_max.setValidator(QIntValidator())
        self.filter_year_max.textChanged.connect(lambda: self.debounce_timer.start())

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
        # Replaced ProxyModel with direct Polars filtering in TableModel
        
        self.table = QTableView()
        self.table.setModel(self.model)
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
        title = self.filter_title.text()
        author = self.filter_author.text()
        
        try:
            min_y = int(self.filter_year_min.text())
        except ValueError:
            min_y = None
            
        try:
            max_y = int(self.filter_year_max.text())
        except ValueError:
            max_y = None
            
        genre = self.filter_genre.currentText()
        lang = self.filter_lang.currentText()
        
        self.model.apply_filters(title, author, min_y, max_y, genre, lang)

    def on_selection_changed(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return

        # Get the row of the selected item
        index = indexes[0]
        # Retrieve description directly from the display dataframe
        desc = self.model.display_df.item(index.row(), "description")
        self.desc_view.setText(desc)

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
        # Update persistence if needed, though here we'd need to reconstruct the full list or keep it synced.
        # Since we converted to Polars, self.model.books is no longer the source of truth if we modify the DF?
        # Actually BookTableModel.__init__ took `books`. But we didn't keep `self.books` in the model!
        # We need to ensure persistence works. 
        # Ideally we'd persist the full dataframe back to list of dicts.
        
        # Let's reconstruct the books list from the full dataframe to save it
        # Or simpler: just append to the original list if we kept it? 
        # But we replaced `self.books` with `self.full_df` in the model.
        # The Window created the list `self.books` initially. 
        # Let's append to that local list and save it.
        self.books.append(book)
        save_books(self.books, DATA_FILE)
        
        # Refresh the view to show the new book (if it matches filters)
        self.update_filters()

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
