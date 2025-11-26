import 'dart:convert';
import 'dart:io';
import 'package:faker/faker.dart';
import '../models/book.dart';

class BookService {
  static const String _fileName = 'books.json';

  // Generate random books
  List<Book> generateBooks(int count) {
    final faker = Faker();
    final List<String> genres = [
      "Fiction", "Non-fiction", "Sci-Fi", "Fantasy",
      "Biography", "History", "Thriller", "Romance"
    ];
    final List<String> languages = [
      "English", "Spanish", "French", "German",
      "Italian", "Chinese", "Japanese"
    ];

    return List.generate(count, (index) {
      return Book(
        title: "${faker.job.title()} ${faker.animal.name()}", // Faker dart is slightly different structure than python
        year: faker.randomGenerator.integer(2024, min: 1900),
        author: faker.person.name(),
        genre: genres[faker.randomGenerator.integer(genres.length)],
        language: languages[faker.randomGenerator.integer(languages.length)],
        description: faker.lorem.sentences(3).join(' '),
      );
    });
  }

  // Save books to JSON file
  Future<void> saveBooks(List<Book> books) async {
    final File file = File(_fileName);
    final String jsonString = jsonEncode(books.map((b) => b.toJson()).toList());
    await file.writeAsString(jsonString);
  }

  // Load books from JSON file
  Future<List<Book>> loadBooks() async {
    try {
      final File file = File(_fileName);
      if (!await file.exists()) {
        return [];
      }
      final String jsonString = await file.readAsString();
      final List<dynamic> jsonList = jsonDecode(jsonString);
      return jsonList.map((json) => Book.fromJson(json)).toList();
    } catch (e) {
      print("Error loading books: $e");
      return [];
    }
  }
}
