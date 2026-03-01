import os
from dotenv import load_dotenv


load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH", "./data/books.parquet")
AMOUNT_GENERATING_BOOKS = 50_000