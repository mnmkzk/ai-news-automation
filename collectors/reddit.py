import logging
from html import unescape

import feedparser

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)


class RedditCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "reddit_chatgpt"

    def collect(self) -> list[Article]:
        feed = feedparser.parse(
            config.RSS_FEEDS["reddit_chatgpt"],
            request_headers={"User-Agent": "ANA-Bot/1.0"},
        )
        articles = []

        for entry in feed.entries[: config.MAX_ARTICLES_PER_SOURCE]:
            title = unescape(entry.get("title", ""))
            summary = unescape(entry.get("summary", ""))

            articles.append(Article(
                title=title,
                url=entry.get("link", ""),
                source_name=self.source_name,
                summary_raw=summary,
                published_at=entry.get("published", ""),
                language="en",
                metadata={"score": entry.get("score", "")},
            ))

        logger.info(f"Reddit: {len(articles)} posts collected")
        return articles
