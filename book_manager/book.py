import json
import random
from faker import Faker
from typing import List, Dict

class Book:
    def __init__(self, title, year, author, genre, language, description):
        self.title = title
        self.year = year
        self.author = author
        self.genre = genre
        self.language = language
        self.description = description

    def to_dict(self):
        return {
            "title": self.title,
            "year": self.year,
            "author": self.author,
            "genre": self.genre,
            "language": self.language,
            "description": self.description
        }

    @staticmethod
    def from_dict(data):
        return Book(
            title=data["title"],
            year=data["year"],
            author=data["author"],
            genre=data["genre"],
            language=data["language"],
            description=data["description"]
        )

def generate_books(n=50) -> List[Book]:
    fake = Faker()
    books = []
    genres = ["Fiction", "Non-fiction", "Sci-Fi", "Fantasy", "Biography", "History", "Thriller", "Romance"]
    languages = ["English", "Spanish", "French", "German", "Italian", "Chinese", "Japanese"]

    for _ in range(n):
        book = Book(
            title=fake.catch_phrase(),
            year=random.randint(1900, 2023),
            author=fake.name(),
            genre=random.choice(genres),
            language=random.choice(languages),
            description=fake.text(max_nb_chars=500)
        )
        books.append(book)
    return books

def save_books(books: List[Book], filename="books.json"):
    with open(filename, "w") as f:
        json.dump([b.to_dict() for b in books], f, indent=4)

def load_books(filename="books.json") -> List[Book]:
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            return [Book.from_dict(d) for d in data]
    except FileNotFoundError:
        return []
