import 'package:flutter/material.dart';
import '../models/book.dart';
import '../services/book_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final BookService _bookService = BookService();
  List<Book> _allBooks = [];
  List<Book> _filteredBooks = [];
  Book? _selectedBook;

  // UI State
  bool _isPopupMode = false;
  Map<String, bool> _columnVisibility = {
    'Title': true,
    'Year': true,
    'Author': true,
    'Genre': true,
    'Language': true,
  };

  // Sorting
  int _sortColumnIndex = 0;
  bool _sortAscending = true;

  // Filter State
  final TextEditingController _titleFilterCtrl = TextEditingController();
  final TextEditingController _authorFilterCtrl = TextEditingController();
  final TextEditingController _minYearCtrl = TextEditingController();
  final TextEditingController _maxYearCtrl = TextEditingController();
  String _selectedGenre = "All";
  String _selectedLanguage = "All";

  // Lists for dropdowns
  List<String> _genres = ["All"];
  List<String> _languages = ["All"];

  // Add Book Controllers
  final TextEditingController _addTitleCtrl = TextEditingController();
  final TextEditingController _addYearCtrl = TextEditingController();
  final TextEditingController _addAuthorCtrl = TextEditingController();
  final TextEditingController _addGenreCtrl = TextEditingController();
  final TextEditingController _addLanguageCtrl = TextEditingController();
  final TextEditingController _addDescCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    List<Book> books = await _bookService.loadBooks();
    if (books.isEmpty) {
      books = _bookService.generateBooks(50);
      await _bookService.saveBooks(books);
    }
    setState(() {
      _allBooks = books;
      _updateDropdownOptions();
      _applyFilters();
    });
  }

  void _updateDropdownOptions() {
    final uniqueGenres = _allBooks.map((b) => b.genre).toSet().toList()..sort();
    final uniqueLangs = _allBooks.map((b) => b.language).toSet().toList()..sort();

    _genres = ["All", ...uniqueGenres];
    _languages = ["All", ...uniqueLangs];

    // Ensure selected value still exists
    if (!_genres.contains(_selectedGenre)) _selectedGenre = "All";
    if (!_languages.contains(_selectedLanguage)) _selectedLanguage = "All";
  }

  void _applyFilters() {
    setState(() {
      _filteredBooks = _allBooks.where((book) {
        // Title
        if (_titleFilterCtrl.text.isNotEmpty &&
            !book.title.toLowerCase().contains(_titleFilterCtrl.text.toLowerCase())) {
          return false;
        }
        // Author
        if (_authorFilterCtrl.text.isNotEmpty &&
            !book.author.toLowerCase().contains(_authorFilterCtrl.text.toLowerCase())) {
          return false;
        }
        // Year Range
        if (_minYearCtrl.text.isNotEmpty) {
          final min = int.tryParse(_minYearCtrl.text);
          if (min != null && book.year < min) return false;
        }
        if (_maxYearCtrl.text.isNotEmpty) {
          final max = int.tryParse(_maxYearCtrl.text);
          if (max != null && book.year > max) return false;
        }
        // Genre
        if (_selectedGenre != "All" && book.genre != _selectedGenre) return false;
        // Language
        if (_selectedLanguage != "All" && book.language != _selectedLanguage) return false;

        return true;
      }).toList();

      // Apply Sort
      _sortBooks();
    });
  }

  void _sortBooks() {
    // Map column index to field
    // But columns are dynamic. We need to find the KEY of the visible column at index _sortColumnIndex
    // This is tricky with DataTables if columns change index.
    // Instead, let's just track the 'sortKey' directly if we were robust,
    // but standard Flutter DataTable passes index.
    // We will rebuild columns dynamically, so the index passed to onSort corresponds to the VISIBLE index.

    // Let's get the list of visible keys in order
    final visibleKeys = _columnVisibility.entries
        .where((e) => e.value)
        .map((e) => e.key)
        .toList();

    if (_sortColumnIndex >= visibleKeys.length) return;

    final key = visibleKeys[_sortColumnIndex];

    _filteredBooks.sort((a, b) {
      int cmp = 0;
      switch (key) {
        case 'Title': cmp = a.title.compareTo(b.title); break;
        case 'Year': cmp = a.year.compareTo(b.year); break;
        case 'Author': cmp = a.author.compareTo(b.author); break;
        case 'Genre': cmp = a.genre.compareTo(b.genre); break;
        case 'Language': cmp = a.language.compareTo(b.language); break;
      }
      return _sortAscending ? cmp : -cmp;
    });
  }

  void _onSort(int columnIndex, bool ascending) {
    setState(() {
      _sortColumnIndex = columnIndex;
      _sortAscending = ascending;
      _sortBooks();
    });
  }

  void _addBook() {
    final year = int.tryParse(_addYearCtrl.text) ?? DateTime.now().year;
    final newBook = Book(
      title: _addTitleCtrl.text,
      year: year,
      author: _addAuthorCtrl.text,
      genre: _addGenreCtrl.text,
      language: _addLanguageCtrl.text,
      description: _addDescCtrl.text.isEmpty ? "No description provided." : _addDescCtrl.text,
    );

    setState(() {
      _allBooks.add(newBook);
      _updateDropdownOptions();
      _bookService.saveBooks(_allBooks);
      _applyFilters();
    });

    // Clear fields
    _addTitleCtrl.clear();
    _addYearCtrl.clear();
    _addAuthorCtrl.clear();
    _addGenreCtrl.clear();
    _addLanguageCtrl.clear();
    _addDescCtrl.clear();

    if (_isPopupMode) {
      Navigator.of(context).pop();
    }
  }

  void _showAddDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Add New Book"),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: _buildAddFormFields(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: _addBook,
            child: const Text("Add"),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildAddFormFields() {
    return [
      TextField(controller: _addTitleCtrl, decoration: const InputDecoration(labelText: "Title")),
      TextField(controller: _addYearCtrl, decoration: const InputDecoration(labelText: "Year"), keyboardType: TextInputType.number),
      TextField(controller: _addAuthorCtrl, decoration: const InputDecoration(labelText: "Author")),
      TextField(controller: _addGenreCtrl, decoration: const InputDecoration(labelText: "Genre")),
      TextField(controller: _addLanguageCtrl, decoration: const InputDecoration(labelText: "Language")),
      TextField(controller: _addDescCtrl, decoration: const InputDecoration(labelText: "Description"), maxLines: 3),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Book Manager (Flutter)"),
      ),
      body: Row(
        children: [
          // Left Column: Table & Filters
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                border: Border(right: BorderSide(color: Colors.grey.shade300)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("Books List", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  _buildVisibilityRow(),
                  const Divider(),
                  _buildFiltersArea(),
                  const Divider(),
                  Expanded(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.vertical,
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: _buildTable(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Right Column: Add & Description
          Expanded(
            flex: 1,
            child: Column(
              children: [
                // Top Right: Add Book
                Expanded(
                  flex: 1,
                  child: Container(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text("Add New Book", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                            Row(
                              children: [
                                const Text("Popup Mode"),
                                Switch(
                                  value: _isPopupMode,
                                  onChanged: (val) => setState(() => _isPopupMode = val),
                                ),
                              ],
                            ),
                          ],
                        ),
                        const Divider(),
                        Expanded(
                          child: _isPopupMode
                              ? Center(
                                  child: ElevatedButton(
                                    onPressed: _showAddDialog,
                                    child: const Text("Open Add Book Dialog"),
                                  ),
                                )
                              : SingleChildScrollView(
                                  child: Column(
                                    children: [
                                      ..._buildAddFormFields(),
                                      const SizedBox(height: 10),
                                      ElevatedButton(
                                        onPressed: _addBook,
                                        child: const Text("Add Book"),
                                      ),
                                    ],
                                  ),
                                ),
                        ),
                      ],
                    ),
                  ),
                ),
                const Divider(),
                // Bottom Right: Description
                Expanded(
                  flex: 1,
                  child: Container(
                    padding: const EdgeInsets.all(16.0),
                    width: double.infinity,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("Description", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const Divider(),
                        Expanded(
                          child: SingleChildScrollView(
                            child: Text(
                              _selectedBook?.description ?? "Select a book to see description.",
                              style: const TextStyle(fontSize: 16),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVisibilityRow() {
    return Wrap(
      spacing: 10,
      children: _columnVisibility.keys.map((key) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Checkbox(
              value: _columnVisibility[key],
              onChanged: (val) {
                setState(() {
                  _columnVisibility[key] = val ?? true;
                });
              },
            ),
            Text(key),
          ],
        );
      }).toList(),
    );
  }

  Widget _buildFiltersArea() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Filters", style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(child: TextField(controller: _titleFilterCtrl, decoration: const InputDecoration(labelText: "Title"), onChanged: (_) => _applyFilters())),
            const SizedBox(width: 10),
            Expanded(child: TextField(controller: _authorFilterCtrl, decoration: const InputDecoration(labelText: "Author"), onChanged: (_) => _applyFilters())),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            SizedBox(
              width: 100,
              child: TextField(controller: _minYearCtrl, decoration: const InputDecoration(labelText: "Min Year"), keyboardType: TextInputType.number, onChanged: (_) => _applyFilters()),
            ),
            const SizedBox(width: 10),
            SizedBox(
              width: 100,
              child: TextField(controller: _maxYearCtrl, decoration: const InputDecoration(labelText: "Max Year"), keyboardType: TextInputType.number, onChanged: (_) => _applyFilters()),
            ),
            const SizedBox(width: 20),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _selectedGenre,
                decoration: const InputDecoration(labelText: "Genre"),
                items: _genres.map((g) => DropdownMenuItem(value: g, child: Text(g))).toList(),
                onChanged: (val) {
                  setState(() => _selectedGenre = val!);
                  _applyFilters();
                },
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _selectedLanguage,
                decoration: const InputDecoration(labelText: "Language"),
                items: _languages.map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),
                onChanged: (val) {
                  setState(() => _selectedLanguage = val!);
                  _applyFilters();
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTable() {
    final visibleKeys = _columnVisibility.entries.where((e) => e.value).map((e) => e.key).toList();

    return DataTable(
      sortColumnIndex: _sortColumnIndex,
      sortAscending: _sortAscending,
      showCheckboxColumn: false, // We use row tap for selection, not checkboxes
      columns: visibleKeys.map((key) {
        return DataColumn(
          label: Text(key),
          onSort: _onSort,
        );
      }).toList(),
      rows: _filteredBooks.map((book) {
        return DataRow(
          selected: _selectedBook == book,
          onSelectChanged: (selected) {
            if (selected == true) {
              setState(() => _selectedBook = book);
            }
          },
          cells: visibleKeys.map((key) {
            switch (key) {
              case 'Title': return DataCell(Text(book.title));
              case 'Year': return DataCell(Text(book.year.toString()));
              case 'Author': return DataCell(Text(book.author));
              case 'Genre': return DataCell(Text(book.genre));
              case 'Language': return DataCell(Text(book.language));
              default: return const DataCell(Text(""));
            }
          }).toList(),
        );
      }).toList(),
    );
  }
}
