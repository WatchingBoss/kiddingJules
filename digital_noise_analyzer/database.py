import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

from config import DATABASE_URL

# Create an asynchronous engine to connect to the database
engine = create_async_engine(DATABASE_URL, echo=False)

# Create a factory for asynchronous sessions
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Base class for declarative models with async support
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Article model corresponding to the 'articles' table
class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    found_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:30]}...', source='{self.source}')>"


# Asynchronous function to initialize the database and create tables
async def init_db():
    """Initializes the database and creates all necessary tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
