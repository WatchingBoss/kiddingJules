import std/[json, random, strutils, os, times]

const DataFile = "books.json"

type
  Book* = object
    title*: string
    year*: int
    author*: string
    genre*: string
    language*: string
    description*: string

proc newBook*(title: string, year: int, author, genre, language, description: string): Book =
  Book(title: title, year: year, author: author, genre: genre, language: language, description: description)

proc generateBooks*(n: int): seq[Book] =
  randomize()
  result = @[]
  let genres = ["Fiction", "Non-fiction", "Sci-Fi", "Fantasy", "Biography", "History", "Thriller", "Romance"]
  let languages = ["English", "Spanish", "French", "German", "Italian", "Chinese", "Japanese"]
  let adjectives = ["Great", "Lost", "Hidden", "Secret", "Dark", "Silent", "Broken", "Final"]
  let nouns = ["World", "Time", "Journey", "Dream", "Star", "Sea", "Mountain", "City"]

  for i in 0 ..< n:
    let title = sample(adjectives) & " " & sample(nouns)
    let year = rand(1900..2023)
    let author = "Author " & $rand(1..100)
    let genre = sample(genres)
    let language = sample(languages)
    let desc = "This is a description for " & title & ". It is a very interesting book written in " & $year & "."

    result.add(newBook(title, year, author, genre, language, desc))

proc saveBooks*(books: seq[Book], filename: string = DataFile) =
  var jsonArray = newJArray()
  for b in books:
    var node = newJObject()
    node["title"] = %b.title
    node["year"] = %b.year
    node["author"] = %b.author
    node["genre"] = %b.genre
    node["language"] = %b.language
    node["description"] = %b.description
    jsonArray.add(node)
  writeFile(filename, $jsonArray)

proc loadBooks*(filename: string = DataFile): seq[Book] =
  if not fileExists(filename):
    return @[]
  try:
    let content = readFile(filename)
    let jsonNode = parseJson(content)
    result = jsonNode.to(seq[Book])
  except:
    result = @[]
