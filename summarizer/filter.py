import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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


def _normalize_platform(source_name: str) -> str:
    """twitter_kensuu → twitter のようにプラットフォーム名に正規化."""
    for prefix in ("twitter", "hatena", "reddit", "producthunt", "official", "newsletter", "prtimes"):
        if source_name.startswith(prefix):
            return prefix
    return source_name


def _parse_published(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            return datetime.fromisoformat(date_str)
        except Exception:
            return None


def _recency_score(article: Article) -> float:
    dt = _parse_published(article.published_at)
    if not dt:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - dt).days
    if days == 0:
        return 4.0
    elif days == 1:
        return 2.0
    return 0.0


def _build_cross_source_map(articles: list[Article]) -> dict[str, int]:
    """トピックキーワードごとに何プラットフォームで言及されているかを集計."""
    keyword_platforms: dict[str, set[str]] = {}
    for a in articles:
        text = (a.title + " " + a.summary_raw).lower()
        platform = _normalize_platform(a.source_name)
        for kw in config.CROSS_SOURCE_TOPICS:
            if kw in text:
                keyword_platforms.setdefault(kw, set()).add(platform)
    return {kw: len(platforms) for kw, platforms in keyword_platforms.items()}


def _cross_source_score(article: Article, cross_map: dict[str, int]) -> float:
    text = (article.title + " " + article.summary_raw).lower()
    score = 0.0
    for kw, count in cross_map.items():
        if kw in text and count >= 2:
            score += 10.0 if count >= 3 else 5.0
    return min(score, 10.0)


def _score_article(article: Article, cross_map: dict[str, int]) -> float:
    text = (article.title + " " + article.summary_raw).lower()
    score = 0.0

    # 除外キーワード
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            score -= 10

    # 実用性キーワード
    for kw in BOOST_KEYWORDS:
        if kw in text:
            score += 2

    # はてなブックマーク数
    bookmarks = article.metadata.get("bookmarks", "")
    if bookmarks and str(bookmarks).isdigit():
        score += min(int(bookmarks) / 10, 10)

    # Reddit upvoteスコア
    reddit_score = article.metadata.get("score", "")
    if reddit_score and str(reddit_score).lstrip("-").isdigit():
        score += min(max(int(reddit_score), 0) / 100, 10)

    # Twitterアカウント重み付け
    account = article.metadata.get("account", "")
    if account:
        score += config.TWITTER_ACCOUNT_WEIGHTS.get(account, 3)

    # 新鮮さ
    score += _recency_score(article)

    # クロスソースボーナス
    score += _cross_source_score(article, cross_map)

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

    # クロスソースマップを事前構築
    cross_map = _build_cross_source_map(unique)

    # スコアリングとフィルタ
    scored = [(a, _score_article(a, cross_map)) for a in unique]
    scored = [(a, s) for a, s in scored if s > -5]
    scored.sort(key=lambda x: x[1], reverse=True)

    # ソース多様性確保: 1ソースあたり最大2件
    source_count: dict[str, int] = {}
    diverse = []
    for a, s in scored:
        count = source_count.get(a.source_name, 0)
        if count < 2:
            diverse.append((a, s))
            source_count[a.source_name] = count + 1

    result = [a for a, _ in diverse[: config.MAX_FILTER_CANDIDATES]]
    logger.info(f"Filter: {len(articles)} -> {len(unique)} (dedup) -> {len(result)} candidates")
    return result
