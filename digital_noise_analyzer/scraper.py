import asyncio
import logging
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from config import LENTA_RSS_URL, HABR_SEARCH_URL

# Setting up a logger for the scraper module
logger = logging.getLogger(__name__)


async def fetch_lenta_rss(session, keyword):
    """
    Fetches and parses news from Lenta.ru RSS feed for a given keyword.
    """
    logger.info(f"Fetching RSS from Lenta.ru for keyword: '{keyword}'")
    articles = []
    try:
        # feedparser can fetch the URL directly
        feed = feedparser.parse(LENTA_RSS_URL)
        if feed.bozo:
            logger.warning(f"Failed to parse RSS feed from Lenta.ru. Bozo bit set: {feed.bozo_exception}")
            return []

        for entry in feed.entries:
            if keyword.lower() in entry.title.lower():
                articles.append({
                    "title": entry.title,
                    "url": entry.link,
                    "source": "lenta.ru"
                })
        logger.info(f"Found {len(articles)} articles on Lenta.ru for keyword: '{keyword}'")
        return articles
    except Exception as e:
        logger.error(f"Error fetching or parsing Lenta.ru RSS for keyword '{keyword}': {e}")
        return []


async def fetch_habr_html(session, keyword):
    """
    Fetches and parses articles from Habr.com search results for a given keyword.
    """
    search_url = HABR_SEARCH_URL.format(keyword=keyword)
    logger.info(f"Fetching HTML from Habr.com for keyword: '{keyword}' from {search_url}")
    articles = []
    # Add a common browser User-Agent header to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(search_url, headers=headers) as response:
            response.raise_for_status()
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        # Updated selector based on HTML analysis
        posts = soup.find_all('article', class_='tm-articles-list__item')

        for post in posts:
            # Updated selector for the title link
            title_element = post.find('a', class_='tm-title__link')
            if title_element:
                title = title_element.text.strip()
                # Construct absolute URL if the link is relative
                relative_url = title_element['href']
                url = f"https://habr.com{relative_url}"
                articles.append({
                    "title": title,
                    "url": url,
                    "source": "habr.com"
                })
        logger.info(f"Found {len(articles)} articles on Habr.com for keyword: '{keyword}'")
        return articles
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error fetching Habr.com for keyword '{keyword}': {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching or parsing Habr.com for keyword '{keyword}': {e}")
        return []


async def collect_data(keywords):
    """
    Collects data from all sources for a list of keywords concurrently.
    """
    logger.info(f"Starting data collection for keywords: {keywords}")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for keyword in keywords:
            tasks.append(fetch_lenta_rss(session, keyword))
            tasks.append(fetch_habr_html(session, keyword))

        results = await asyncio.gather(*tasks)

        # Flatten the list of lists into a single list
        all_articles = [article for sublist in results for article in sublist]
        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles
