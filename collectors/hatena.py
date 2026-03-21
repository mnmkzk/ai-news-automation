import logging
from html import unescape

import feedparser

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)


class HatenaCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "hatena_bookmark"

    def collect(self) -> list[Article]:
        feed = feedparser.parse(config.RSS_FEEDS["hatena_it"])
        articles = []

        for entry in feed.entries[: config.MAX_ARTICLES_PER_SOURCE]:
            # AI関連キーワードでフィルタ
            title = unescape(entry.get("title", ""))
            summary = unescape(entry.get("summary", ""))
            text = (title + " " + summary).lower()

            ai_keywords = [
                "ai", "人工知能", "chatgpt", "gpt", "llm", "生成ai",
                "claude", "gemini", "copilot", "機械学習", "ディープラーニング",
                "openai", "anthropic", "自動化",
            ]
            if not any(kw in text for kw in ai_keywords):
                continue

            articles.append(Article(
                title=title,
                url=entry.get("link", ""),
                source_name=self.source_name,
                summary_raw=summary,
                published_at=entry.get("published", ""),
                language="ja",
                metadata={"bookmarks": entry.get("hatena_bookmarkcount", "")},
            ))

        logger.info(f"Hatena: {len(articles)} AI-related articles found")
        return articles
