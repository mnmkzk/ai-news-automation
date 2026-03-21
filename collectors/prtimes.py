import logging
import time

import requests
from bs4 import BeautifulSoup

import config
from collectors.base import Article, BaseCollector

logger = logging.getLogger(__name__)


class PRTimesCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "prtimes"

    def collect(self) -> list[Article]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        resp = requests.get(
            config.PRTIMES_SEARCH_URL,
            headers=headers,
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        articles = []

        # PR TIMESの検索結果からプレスリリースを取得
        for item in soup.select("article.list-article")[:config.MAX_ARTICLES_PER_SOURCE]:
            title_el = item.select_one("h2 a, .list-article__title a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            if url and not url.startswith("http"):
                url = "https://prtimes.jp" + url

            summary_el = item.select_one(".list-article__summary, .list-article__text")
            summary = summary_el.get_text(strip=True) if summary_el else ""

            date_el = item.select_one("time, .list-article__date")
            pub_date = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else ""

            articles.append(Article(
                title=title,
                url=url,
                source_name=self.source_name,
                summary_raw=summary,
                published_at=pub_date,
                language="ja",
            ))

        logger.info(f"PR TIMES: {len(articles)} articles found")
        return articles
