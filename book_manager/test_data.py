import os
from book import generate_books, save_books, load_books, Book

def test_data_generation_and_persistence():
    print("Testing Data Generation...")
    books = generate_books(5)
    assert len(books) == 5
    print(f"Generated {len(books)} books.")
    for b in books:
        print(f" - {b.title} ({b.year}) by {b.author}")
        assert b.description is not None

    filename = "test_books.json"
    print(f"\nTesting Persistence to {filename}...")
    save_books(books, filename)

    assert os.path.exists(filename)
    print("File created.")

    loaded_books = load_books(filename)
    assert len(loaded_books) == 5
    print(f"Loaded {len(loaded_books)} books.")

    assert loaded_books[0].title == books[0].title
    assert loaded_books[0].year == books[0].year

    # Clean up
    os.remove(filename)
    print("\nTest Passed!")

if __name__ == "__main__":
    test_data_generation_and_persistence()
