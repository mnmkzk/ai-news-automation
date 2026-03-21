import logging

import feedparser

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """X/Twitter collector using Nitter RSS feeds.

    Gracefully degrades: if Nitter is unavailable, returns empty list
    rather than crashing the pipeline.
    """

    @property
    def source_name(self) -> str:
        return "twitter"

    def collect(self) -> list[Article]:
        articles = []

        for account in config.TWITTER_ACCOUNTS:
            try:
                articles.extend(self._fetch_account(account))
            except Exception as e:
                logger.warning(f"Twitter: failed to fetch @{account}: {e}")

        logger.info(f"Twitter: {len(articles)} posts collected")
        return articles

    def _fetch_account(self, account: str) -> list[Article]:
        rss_url = f"{config.NITTER_BASE_URL}/{account}/rss"
        feed = feedparser.parse(rss_url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Twitter: Nitter RSS unavailable for @{account}")
            return []

        results = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            # AI関連の投稿のみ抽出
            text = title.lower()
            ai_keywords = [
                "ai", "chatgpt", "gpt", "claude", "gemini",
                "人工知能", "生成ai", "自動化", "llm", "openai",
            ]
            if not any(kw in text for kw in ai_keywords):
                continue

            results.append(Article(
                title=title[:200],
                url=entry.get("link", ""),
                source_name=f"twitter_{account}",
                summary_raw=title,
                published_at=entry.get("published", ""),
                language="ja",
                metadata={"account": account},
            ))

        return results
