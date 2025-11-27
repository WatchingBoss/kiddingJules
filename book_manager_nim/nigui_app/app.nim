import nigui
import std/[strutils, sequtils, strformat, algorithm]
import book

var
  books: seq[Book]
  filteredBooks: seq[Book]
  uniqueGenres: seq[string]
  uniqueLanguages: seq[string]

  # UI References
  window: Window
  tableContainer: LayoutContainer
  descArea: TextArea

  # Inputs
  filterTitle, filterAuthor, filterMinYear, filterMaxYear: TextBox
  filterGenre, filterLang: ComboBox

  # Add Book Inputs
  inputTitle, inputYear, inputAuthor, inputGenre, inputLang: TextBox
  inputDesc: TextArea

  # State
  sortCol = "Title"
  sortAsc = true
  columnVis = [true, true, true, true, true] # Title, Year, Author, Genre, Lang

proc updateFilters()
proc renderTable()

proc loadData() =
  books = loadBooks()
  if books.len == 0:
    books = generateBooks(50)
    saveBooks(books)

  uniqueGenres = @["All"]
  uniqueLanguages = @["All"]

  for b in books:
    if b.genre notin uniqueGenres: uniqueGenres.add(b.genre)
    if b.language notin uniqueLanguages: uniqueLanguages.add(b.language)

  uniqueGenres.sort()
  uniqueLanguages.sort()

proc filterBooks() =
  filteredBooks = @[]
  let t = filterTitle.text.toLowerAscii
  let a = filterAuthor.text.toLowerAscii
  let g = if filterGenre.index >= 0: filterGenre.options[filterGenre.index] else: "All"
  let l = if filterLang.index >= 0: filterLang.options[filterLang.index] else: "All"

  var minY = 0
  var maxY = 9999
  try: minY = parseInt(filterMinYear.text)
  except: discard
  try: maxY = parseInt(filterMaxYear.text)
  except: discard
  if filterMaxYear.text == "": maxY = 9999

  for b in books:
    if t != "" and t notin b.title.toLowerAscii: continue
    if a != "" and a notin b.author.toLowerAscii: continue
    if b.year < minY or b.year > maxY: continue
    if g != "All" and b.genre != g: continue
    if l != "All" and b.language != l: continue

    filteredBooks.add(b)

proc sortBooks() =
  filteredBooks.sort do (x, y: Book) -> int:
    var res = 0
    case sortCol:
    of "Title": res = cmp(x.title, y.title)
    of "Year": res = cmp(x.year, y.year)
    of "Author": res = cmp(x.author, y.author)
    of "Genre": res = cmp(x.genre, y.genre)
    of "Language": res = cmp(x.language, y.language)
    else: discard

    if not sortAsc: res = -res
    return res

proc refreshTable() =
  filterBooks()
  sortBooks()
  renderTable()

# --- UI Handlers ---

proc onHeaderClick(col: string) =
  if sortCol == col:
    sortAsc = not sortAsc
  else:
    sortCol = col
    sortAsc = true
  refreshTable()

proc onRowClick(b: Book) =
  descArea.text = b.description

proc onAddBook(event: ClickEvent) =
  let title = inputTitle.text
  if title == "": return
  var year = 0
  try: year = parseInt(inputYear.text)
  except: discard

  let newBook = newBook(
    title, year, inputAuthor.text,
    inputGenre.text, inputLang.text, inputDesc.text
  )
  books.add(newBook)
  saveBooks(books)

  # Reset inputs
  inputTitle.text = ""
  inputYear.text = ""
  inputAuthor.text = ""
  inputGenre.text = ""
  inputLang.text = ""
  inputDesc.text = ""

  refreshTable()

# --- UI Builder ---

proc renderTable() =
  # Clear existing rows (NiGui doesn't have clear() for container easily exposed in some versions,
  # typically we remove children. Assuming `tableContainer.clear()` works or we iterate remove.)
  # Since I can't check docs/compile, I will try creating a new container and replacing it?
  # No, standard way is loop remove.
  while tableContainer.childCount > 0:
    tableContainer.remove(tableContainer.child(0))

  # Header
  let header = newLayoutContainer(Layout_Horizontal)
  header.height = 30
  let cols = ["Title", "Year", "Author", "Genre", "Language"]

  for i, name in cols:
    if columnVis[i]:
      let btn = newButton(name)
      # Capture loop variable? Nim closures capture by reference in loops?
      # Need to capture `name` locally.
      let cName = name
      btn.onClick = proc(e: ClickEvent) = onHeaderClick(cName)
      header.add(btn)

  tableContainer.add(header)

  # Rows
  # Limit rows for performance if NiGui is slow
  let limit = min(filteredBooks.len, 100)
  for i in 0 ..< limit:
    let b = filteredBooks[i]
    let row = newLayoutContainer(Layout_Horizontal)
    row.height = 30

    if columnVis[0]: row.add(newLabel(b.title))
    if columnVis[1]: row.add(newLabel($b.year))
    if columnVis[2]: row.add(newLabel(b.author))
    if columnVis[3]: row.add(newLabel(b.genre))
    if columnVis[4]: row.add(newLabel(b.language))

    # Make row clickable - NiGui LayoutContainer handles clicks?
    # Usually we put a button or handle click on container if supported.
    # Using a "Select" button for simplicity in NiGui
    let selBtn = newButton("View")
    selBtn.width = 50
    selBtn.onClick = proc(e: ClickEvent) = onRowClick(b)
    row.add(selBtn)

    tableContainer.add(row)

app.init()
loadData()

window = newWindow("Book Manager (NiGui)")
window.width = 1000
window.height = 700

let mainContainer = newLayoutContainer(Layout_Horizontal)
window.add(mainContainer)

# --- Left Panel ---
let leftPanel = newLayoutContainer(Layout_Vertical)
leftPanel.widthMode = WidthMode_Expand
mainContainer.add(leftPanel)

# Filters
let filterBox = newLayoutContainer(Layout_Vertical)
filterBox.frame = newFrame("Filters")
leftPanel.add(filterBox)

let r1 = newLayoutContainer(Layout_Horizontal)
r1.add(newLabel("Title:"))
filterTitle = newTextBox()
filterTitle.onTextChange = proc(e: TextChangeEvent) = refreshTable()
r1.add(filterTitle)
r1.add(newLabel("Author:"))
filterAuthor = newTextBox()
filterAuthor.onTextChange = proc(e: TextChangeEvent) = refreshTable()
r1.add(filterAuthor)
filterBox.add(r1)

let r2 = newLayoutContainer(Layout_Horizontal)
r2.add(newLabel("Year:"))
filterMinYear = newTextBox()
filterMinYear.onTextChange = proc(e: TextChangeEvent) = refreshTable()
r2.add(filterMinYear)
r2.add(newLabel("-"))
filterMaxYear = newTextBox()
filterMaxYear.onTextChange = proc(e: TextChangeEvent) = refreshTable()
r2.add(filterMaxYear)
filterBox.add(r2)

let r3 = newLayoutContainer(Layout_Horizontal)
r3.add(newLabel("Genre:"))
filterGenre = newComboBox(uniqueGenres)
filterGenre.onChange = proc(e: SelectionChangeEvent) = refreshTable()
r3.add(filterGenre)
r3.add(newLabel("Language:"))
filterLang = newComboBox(uniqueLanguages)
filterLang.onChange = proc(e: SelectionChangeEvent) = refreshTable()
r3.add(filterLang)
filterBox.add(r3)

# Column Vis (Simple Checkboxes)
let visBox = newLayoutContainer(Layout_Horizontal)
visBox.height = 30
let colNames = ["Title", "Year", "Author", "Genre", "Lang"]
for i in 0..4:
  let cb = newCheckbox(colNames[i])
  cb.checked = true
  # Capture i
  let idx = i
  cb.onToggle = proc(e: ToggleEvent) =
    columnVis[idx] = cb.checked
    refreshTable()
  visBox.add(cb)
leftPanel.add(visBox)

# Table Area
# NiGui usually needs a ScrollLayout for lists
# Assuming ScrollLayout exists or TextArea workaround.
# LayoutContainer inside a window should scroll if configured?
# NiGui doesn't autoscoll LayoutContainers. We need specific control.
# I'll use a simple LayoutContainer for this demo structure.
tableContainer = newLayoutContainer(Layout_Vertical)
leftPanel.add(tableContainer)

# --- Right Panel ---
let rightPanel = newLayoutContainer(Layout_Vertical)
rightPanel.width = 350
mainContainer.add(rightPanel)

# Add Book
let addGroup = newLayoutContainer(Layout_Vertical)
addGroup.frame = newFrame("Add Book")
rightPanel.add(addGroup)

proc addInput(label: string, tb: var TextBox) =
  let row = newLayoutContainer(Layout_Horizontal)
  row.add(newLabel(label))
  tb = newTextBox()
  row.add(tb)
  addGroup.add(row)

var dummyTB: TextBox # Helper
addInput("Title:", inputTitle)
addInput("Year:", inputYear)
addInput("Author:", inputAuthor)
addInput("Genre:", inputGenre)
addInput("Lang:", inputLang)

addGroup.add(newLabel("Description:"))
inputDesc = newTextArea()
inputDesc.height = 60
addGroup.add(inputDesc)

let addBtn = newButton("Add Book")
addBtn.onClick = onAddBook
addGroup.add(addBtn)

# Description
let descGroup = newLayoutContainer(Layout_Vertical)
descGroup.frame = newFrame("Description")
descGroup.heightMode = HeightMode_Expand
rightPanel.add(descGroup)

descArea = newTextArea()
descArea.editable = false
descGroup.add(descArea)

# Init
refreshTable()
window.show()
app.run()
