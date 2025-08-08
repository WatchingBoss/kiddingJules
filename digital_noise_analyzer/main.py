import asyncio
import logging
from sqlalchemy import select

from config import KEYWORDS
from database import init_db, async_session, Article
from scraper import collect_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def save_to_db(articles):
    """
    Saves a list of articles to the database, avoiding duplicates.
    """
    if not articles:
        logger.info("No new articles to save.")
        return

    logger.info(f"Attempting to save {len(articles)} articles to the database...")
    new_articles_count = 0

    async with async_session() as session:
        async with session.begin():
            for article_data in articles:
                # Check if an article with the same URL already exists
                result = await session.execute(
                    select(Article).filter_by(url=article_data['url'])
                )
                existing_article = result.scalars().first()

                if not existing_article:
                    # If it doesn't exist, create and add the new article
                    new_article = Article(
                        title=article_data['title'],
                        url=article_data['url'],
                        source=article_data['source']
                    )
                    session.add(new_article)
                    new_articles_count += 1

        # The transaction is committed automatically upon exiting the 'async with session.begin()' block

    logger.info(f"Successfully added {new_articles_count} new articles to the database.")


async def main():
    """
    The main function to run the digital noise analyzer.
    """
    logger.info("Starting the digital noise analyzer script.")

    # 1. Initialize the database (create tables if they don't exist)
    await init_db()
    logger.info("Database initialized successfully.")

    # 2. Collect data from all sources
    articles = await collect_data(KEYWORDS)

    # 3. Save the collected data to the database
    await save_to_db(articles)

    logger.info("Digital noise analyzer script finished successfully.")


if __name__ == "__main__":
    asyncio.run(main())
