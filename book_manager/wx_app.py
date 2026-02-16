import wx
import wx.grid
from book import Book, generate_books, save_books, load_books

DATA_FILE = "books.json"

class AddBookDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Add New Book", size=(400, 450))

        sizer = wx.BoxSizer(wx.VERTICAL)
        form_sizer = wx.FlexGridSizer(rows=6, cols=2, vgap=10, hgap=10)
        form_sizer.AddGrowableCol(1, 1)

        self.title_ctrl = wx.TextCtrl(self)
        self.year_ctrl = wx.TextCtrl(self)
        self.author_ctrl = wx.TextCtrl(self)
        self.genre_ctrl = wx.TextCtrl(self)
        self.lang_ctrl = wx.TextCtrl(self)
        self.desc_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 80))

        form_sizer.Add(wx.StaticText(self, label="Title:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.title_ctrl, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self, label="Year:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.year_ctrl, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self, label="Author:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.author_ctrl, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self, label="Genre:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.genre_ctrl, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self, label="Language:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.lang_ctrl, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self, label="Desc:"), 0, wx.ALIGN_TOP)
        form_sizer.Add(self.desc_ctrl, 1, wx.EXPAND)

        sizer.Add(form_sizer, 1, wx.EXPAND | wx.ALL, 10)

        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btns, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.SetSizer(sizer)

    def GetBookData(self):
        try:
            year = int(self.year_ctrl.GetValue())
        except ValueError:
            year = 0

        return Book(
            title=self.title_ctrl.GetValue(),
            year=year,
            author=self.author_ctrl.GetValue(),
            genre=self.genre_ctrl.GetValue(),
            language=self.lang_ctrl.GetValue(),
            description=self.desc_ctrl.GetValue() or "No description provided."
        )

class BookManagerFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Book Manager (wxPython)", size=(1200, 800))

        # Data
        self.books = load_books(DATA_FILE)
        if not self.books:
            self.books = generate_books(50)
            save_books(self.books, DATA_FILE)

        self.unique_genres = sorted(list(set(b.genre for b in self.books)))
        self.unique_languages = sorted(list(set(b.language for b in self.books)))
        self.filtered_books = list(self.books)

        self.sort_col = -1
        self.sort_ascending = True

        # GUI
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # --- Left Panel ---
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Visibility
        self.col_checks = {}
        vis_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vis_sizer.Add(wx.StaticText(panel, label="Show: "), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        for idx, col in enumerate(["Title", "Year", "Author", "Genre", "Language"]):
            chk = wx.CheckBox(panel, label=col)
            chk.SetValue(True)
            chk.Bind(wx.EVT_CHECKBOX, lambda e, i=idx: self.OnToggleColumn(e, i))
            vis_sizer.Add(chk, 0, wx.RIGHT, 5)
            self.col_checks[idx] = chk
        left_sizer.Add(vis_sizer, 0, wx.ALL, 5)

        # Filters
        filter_sizer = wx.GridSizer(cols=4, vgap=5, hgap=5)

        self.f_title = wx.TextCtrl(panel, value="", style=wx.TE_PROCESS_ENTER)
        self.f_title.SetHint("Filter Title")
        self.f_title.Bind(wx.EVT_TEXT, self.OnFilter)
        filter_sizer.Add(self.f_title, 0, wx.EXPAND)

        self.f_author = wx.TextCtrl(panel, value="", style=wx.TE_PROCESS_ENTER)
        self.f_author.SetHint("Filter Author")
        self.f_author.Bind(wx.EVT_TEXT, self.OnFilter)
        filter_sizer.Add(self.f_author, 0, wx.EXPAND)

        self.f_year_min = wx.TextCtrl(panel, value="")
        self.f_year_min.SetHint("Min Year")
        self.f_year_min.Bind(wx.EVT_TEXT, self.OnFilter)
        filter_sizer.Add(self.f_year_min, 0, wx.EXPAND)

        self.f_year_max = wx.TextCtrl(panel, value="")
        self.f_year_max.SetHint("Max Year")
        self.f_year_max.Bind(wx.EVT_TEXT, self.OnFilter)
        filter_sizer.Add(self.f_year_max, 0, wx.EXPAND)

        self.f_genre = wx.ComboBox(panel, value="All", choices=["All"] + self.unique_genres, style=wx.CB_READONLY)
        self.f_genre.Bind(wx.EVT_COMBOBOX, self.OnFilter)
        filter_sizer.Add(self.f_genre, 0, wx.EXPAND)

        self.f_lang = wx.ComboBox(panel, value="All", choices=["All"] + self.unique_languages, style=wx.CB_READONLY)
        self.f_lang.Bind(wx.EVT_COMBOBOX, self.OnFilter)
        filter_sizer.Add(self.f_lang, 0, wx.EXPAND)

        left_sizer.Add(filter_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Table
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "Title", width=200)
        self.list_ctrl.InsertColumn(1, "Year", width=60)
        self.list_ctrl.InsertColumn(2, "Author", width=150)
        self.list_ctrl.InsertColumn(3, "Genre", width=100)
        self.list_ctrl.InsertColumn(4, "Language", width=100)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

        left_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(left_sizer, 2, wx.EXPAND | wx.ALL, 5)

        # --- Right Panel ---
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add Book
        add_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Add New Book")

        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.rb_inline = wx.RadioButton(panel, label="Inline", style=wx.RB_GROUP)
        self.rb_popup = wx.RadioButton(panel, label="Popup")
        self.rb_inline.SetValue(True)
        self.rb_inline.Bind(wx.EVT_RADIOBUTTON, self.OnModeChange)
        self.rb_popup.Bind(wx.EVT_RADIOBUTTON, self.OnModeChange)
        mode_sizer.Add(wx.StaticText(panel, label="Mode: "), 0, wx.CENTER)
        mode_sizer.Add(self.rb_inline, 0, wx.CENTER | wx.LEFT, 5)
        mode_sizer.Add(self.rb_popup, 0, wx.CENTER | wx.LEFT, 5)
        add_box.Add(mode_sizer, 0, wx.ALL, 5)

        # Inline Form
        self.inline_panel = wx.Panel(panel)
        form_sizer = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
        form_sizer.AddGrowableCol(1, 1)

        self.add_title = wx.TextCtrl(self.inline_panel)
        self.add_year = wx.TextCtrl(self.inline_panel)
        self.add_author = wx.TextCtrl(self.inline_panel)
        self.add_genre = wx.TextCtrl(self.inline_panel)
        self.add_lang = wx.TextCtrl(self.inline_panel)
        self.add_desc = wx.TextCtrl(self.inline_panel, style=wx.TE_MULTILINE, size=(-1, 60))

        form_sizer.Add(wx.StaticText(self.inline_panel, label="Title:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.add_title, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self.inline_panel, label="Year:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.add_year, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self.inline_panel, label="Author:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.add_author, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self.inline_panel, label="Genre:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.add_genre, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self.inline_panel, label="Lang:"), 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.add_lang, 1, wx.EXPAND)
        form_sizer.Add(wx.StaticText(self.inline_panel, label="Desc:"), 0, wx.ALIGN_TOP)
        form_sizer.Add(self.add_desc, 1, wx.EXPAND)

        self.inline_panel.SetSizer(form_sizer)
        add_box.Add(self.inline_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.btn_add_inline = wx.Button(panel, label="Add Book")
        self.btn_add_inline.Bind(wx.EVT_BUTTON, self.OnAddInline)
        add_box.Add(self.btn_add_inline, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # Popup Button
        self.btn_popup = wx.Button(panel, label="Open Add Book Dialog")
        self.btn_popup.Bind(wx.EVT_BUTTON, self.OnOpenPopup)
        self.btn_popup.Hide()
        add_box.Add(self.btn_popup, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        right_sizer.Add(add_box, 0, wx.EXPAND | wx.ALL, 5)

        # Description
        desc_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Description")
        self.desc_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, value="Select a book to see description.")
        desc_box.Add(self.desc_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(desc_box, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(right_sizer, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        self.RefreshList()

    def OnToggleColumn(self, event, col_idx):
        # wx.ListCtrl doesn't support hiding columns natively well.
        # We must set width to 0 or delete/insert.
        # Setting width to 0 is the common hack.
        chk = event.GetEventObject()
        if chk.IsChecked():
            width = 100 if col_idx > 0 else 200 # Default widths
            self.list_ctrl.SetColumnWidth(col_idx, width)
        else:
            self.list_ctrl.SetColumnWidth(col_idx, 0)

    def OnFilter(self, event):
        t_q = self.f_title.GetValue().lower()
        a_q = self.f_author.GetValue().lower()
        g_q = self.f_genre.GetValue()
        l_q = self.f_lang.GetValue()

        try:
            min_y = int(self.f_year_min.GetValue())
        except:
            min_y = None
        try:
            max_y = int(self.f_year_max.GetValue())
        except:
            max_y = None

        self.filtered_books = []
        for b in self.books:
            if t_q and t_q not in b.title.lower(): continue
            if a_q and a_q not in b.author.lower(): continue
            if g_q != "All" and b.genre != g_q: continue
            if l_q != "All" and b.language != l_q: continue
            if min_y is not None and b.year < min_y: continue
            if max_y is not None and b.year > max_y: continue
            self.filtered_books.append(b)

        self.RefreshList()

    def RefreshList(self):
        self.list_ctrl.DeleteAllItems()
        for i, book in enumerate(self.filtered_books):
            idx = self.list_ctrl.InsertItem(i, book.title)
            self.list_ctrl.SetItem(idx, 1, str(book.year))
            self.list_ctrl.SetItem(idx, 2, book.author)
            self.list_ctrl.SetItem(idx, 3, book.genre)
            self.list_ctrl.SetItem(idx, 4, book.language)
            self.list_ctrl.SetItemData(idx, i) # Store index in filtered list

    def OnColClick(self, event):
        col = event.GetColumn()
        if col == self.sort_col:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_col = col
            self.sort_ascending = True

        key_map = {0: 'title', 1: 'year', 2: 'author', 3: 'genre', 4: 'language'}
        attr = key_map.get(col)

        if attr:
            self.filtered_books.sort(key=lambda b: getattr(b, attr), reverse=not self.sort_ascending)
            self.RefreshList()

    def OnItemSelected(self, event):
        idx = event.GetItem().GetData() # This is index in filtered_books
        if 0 <= idx < len(self.filtered_books):
            book = self.filtered_books[idx]
            self.desc_ctrl.SetValue(book.description)

    def OnModeChange(self, event):
        is_inline = self.rb_inline.GetValue()
        self.inline_panel.Show(is_inline)
        self.btn_add_inline.Show(is_inline)
        self.btn_popup.Show(not is_inline)
        self.Layout()

    def OnAddInline(self, event):
        try:
            year = int(self.add_year.GetValue())
        except:
            year = 0

        book = Book(
            title=self.add_title.GetValue(),
            year=year,
            author=self.add_author.GetValue(),
            genre=self.add_genre.GetValue(),
            language=self.add_lang.GetValue(),
            description=self.add_desc.GetValue() or "No description provided."
        )
        self.SaveAndUpdate(book)

        # Clear
        for ctrl in [self.add_title, self.add_year, self.add_author, self.add_genre, self.add_lang, self.add_desc]:
            ctrl.Clear()

    def OnOpenPopup(self, event):
        dlg = AddBookDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            book = dlg.GetBookData()
            self.SaveAndUpdate(book)
        dlg.Destroy()

    def SaveAndUpdate(self, book):
        self.books.append(book)
        save_books(self.books, DATA_FILE)

        # Update dropdowns
        if book.genre not in self.unique_genres:
            self.unique_genres.append(book.genre)
            self.unique_genres.sort()
            self.f_genre.Append(book.genre)

        if book.language not in self.unique_languages:
            self.unique_languages.append(book.language)
            self.unique_languages.sort()
            self.f_lang.Append(book.language)

        self.filtered_books.append(book)
        self.RefreshList()

if __name__ == "__main__":
    app = wx.App()
    frame = BookManagerFrame()
    frame.Show()
    app.MainLoop()
