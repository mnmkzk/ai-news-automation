import logging
from html import unescape

import feedparser

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)


class ProductHuntCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "producthunt"

    def collect(self) -> list[Article]:
        feed = feedparser.parse(config.PRODUCTHUNT_FEED_URL)
        articles = []

        for entry in feed.entries:
            title = unescape(entry.get("title", ""))
            summary = unescape(entry.get("summary", entry.get("description", "")))
            text = (title + " " + summary).lower()

            if not any(kw in text for kw in config.PRODUCTHUNT_AI_KEYWORDS):
                continue

            articles.append(Article(
                title=title,
                url=entry.get("link", ""),
                source_name=self.source_name,
                summary_raw=summary,
                published_at=entry.get("published", ""),
                language="en",
            ))

            if len(articles) >= config.MAX_ARTICLES_PER_SOURCE:
                break

        logger.info(f"Product Hunt: {len(articles)} AI products found")
        return articles
