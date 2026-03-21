import logging
from urllib.parse import urlparse

import config
from collectors.base import Article

logger = logging.getLogger(__name__)

# 理論的・数学的な記事を除外するキーワード
EXCLUDE_KEYWORDS = [
    "arxiv", "論文", "paper", "theorem", "proof", "mathematical",
    "gradient descent", "backpropagation", "loss function",
    "ベンチマーク結果", "benchmark score",
]

# 実用的・面白い記事を優先するキーワード
BOOST_KEYWORDS = [
    "使い方", "活用", "便利", "無料", "新機能", "アップデート",
    "how to", "tips", "free", "launch", "new feature", "update",
    "仕事", "効率", "自動化", "時短", "簡単",
]


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}".rstrip("/").lower()


def _score_article(article: Article) -> float:
    text = (article.title + " " + article.summary_raw).lower()
    score = 0.0

    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            score -= 10

    for kw in BOOST_KEYWORDS:
        if kw in text:
            score += 2

    # ブックマーク数やスコアがあれば加点
    bookmarks = article.metadata.get("bookmarks", "")
    if bookmarks and str(bookmarks).isdigit():
        score += min(int(bookmarks) / 10, 10)

    return score


def filter_and_deduplicate(articles: list[Article]) -> list[Article]:
    # URL重複排除
    seen_urls = set()
    unique = []
    for a in articles:
        normalized = _normalize_url(a.url)
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique.append(a)

    # スコアリングとフィルタ
    scored = [(a, _score_article(a)) for a in unique]
    scored = [(a, s) for a, s in scored if s > -5]  # 明らかに除外すべきものを除く
    scored.sort(key=lambda x: x[1], reverse=True)

    result = [a for a, _ in scored[: config.MAX_ARTICLES_TO_SUMMARIZE]]
    logger.info(f"Filter: {len(articles)} -> {len(unique)} (dedup) -> {len(result)} (scored)")
    return result
