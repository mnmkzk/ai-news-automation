import logging
from html import unescape

import feedparser

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)

BLOG_FEEDS = {
    "openai_blog": config.RSS_FEEDS["openai_blog"],
    "anthropic_blog": config.RSS_FEEDS["anthropic_blog"],
}


class OfficialBlogsCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "official_blogs"

    def collect(self) -> list[Article]:
        articles = []

        for name, url in BLOG_FEEDS.items():
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

        logger.info(f"Official blogs: {len(articles)} posts collected")
        return articles
