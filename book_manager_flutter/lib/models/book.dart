class Book {
  final String title;
  final int year;
  final String author;
  final String genre;
  final String language;
  final String description;

  Book({
    required this.title,
    required this.year,
    required this.author,
    required this.genre,
    required this.language,
    required this.description,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      title: json['title'] as String,
      year: json['year'] as int,
      author: json['author'] as String,
      genre: json['genre'] as String,
      language: json['language'] as String,
      description: json['description'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'year': year,
      'author': author,
      'genre': genre,
      'language': language,
      'description': description,
    };
  }
}
