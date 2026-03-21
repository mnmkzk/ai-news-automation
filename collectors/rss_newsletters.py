import logging
from html import unescape

import feedparser

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)

NEWSLETTER_FEEDS = {
    "rundown_ai": config.RSS_FEEDS.get("rundown_ai"),
    "bensbites": config.RSS_FEEDS.get("bensbites"),
}


class RSSNewsletterCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "newsletters"

    def collect(self) -> list[Article]:
        articles = []

        for name, url in NEWSLETTER_FEEDS.items():
            if not url:
                continue
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[: 5]:
                    title = unescape(entry.get("title", ""))
                    summary = unescape(entry.get("summary", entry.get("description", "")))

                    articles.append(Article(
                        title=title,
                        url=entry.get("link", ""),
                        source_name=name,
                        summary_raw=summary,
                        published_at=entry.get("published", ""),
                        language="en",
                    ))
            except Exception as e:
                logger.warning(f"Failed to fetch {name}: {e}")

        logger.info(f"Newsletters: {len(articles)} posts collected")
        return articles
