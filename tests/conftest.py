"""Shared fixtures for ANA unit tests."""

import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import date

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collectors.base import Article


# ---------------------------------------------------------------------------
# Article fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_article():
    """Minimal Article with required fields only."""
    return Article(title="テスト記事", url="https://example.com/1", source_name="test_source")


@pytest.fixture
def full_article():
    """Article with all fields populated."""
    return Article(
        title="ChatGPTの新機能が便利",
        url="https://example.com/ai-news",
        source_name="hatena_bookmark",
        summary_raw="ChatGPTに新しい画像生成機能が追加された",
        published_at="2026-03-21T10:00:00",
        language="ja",
        metadata={"bookmarks": "150"},
    )


@pytest.fixture
def en_article():
    """English article."""
    return Article(
        title="OpenAI launches GPT-5",
        url="https://openai.com/blog/gpt5",
        source_name="openai_blog",
        summary_raw="OpenAI has released GPT-5 with major improvements.",
        language="en",
    )


@pytest.fixture
def academic_article():
    """Article that should be penalised by filter (academic/theory)."""
    return Article(
        title="arxiv論文: gradient descentの新手法",
        url="https://arxiv.org/abs/1234",
        source_name="test",
        summary_raw="backpropagation loss function benchmark score",
    )


@pytest.fixture
def boost_article():
    """Article that should be boosted by filter (practical)."""
    return Article(
        title="無料で使える新機能が便利すぎる",
        url="https://example.com/free-tool",
        source_name="test",
        summary_raw="仕事の効率が上がる自動化ツール",
    )


# ---------------------------------------------------------------------------
# Mock RSS entry helpers
# ---------------------------------------------------------------------------

def make_rss_entry(title="Test Title", link="https://example.com/test",
                   summary="<p>Test summary</p>", published="2026-03-21",
                   **extra):
    """Create a mock RSS feed entry (SimpleNamespace that acts like a dict via .get)."""
    data = {
        "title": title,
        "link": link,
        "summary": summary,
        "published": published,
        **extra,
    }
    ns = SimpleNamespace(**data)
    ns.get = lambda key, default="": data.get(key, default)
    return ns


def make_feed(entries=None, bozo=False):
    """Create a mock feedparser result."""
    feed = SimpleNamespace()
    feed.entries = entries or []
    feed.bozo = bozo
    return feed


# ---------------------------------------------------------------------------
# Mock Claude API response
# ---------------------------------------------------------------------------

MOCK_CLAUDE_RESPONSE_2_ARTICLES = """\
---記事1---
【タイトル】AIで仕事が変わる
【これ、なに？】ChatGPTに新機能が追加されました。
【何がすごいの？】処理速度が3倍になりました。
【あなたの生活・仕事はどう変わる？】資料作成が1分で終わります。
---記事2---
【タイトル】無料AIツール登場
【これ、なに？】誰でも使える新ツールです。
【何がすごいの？】従来の半額で利用できます。
【あなたの生活・仕事はどう変わる？】翻訳作業が不要になります。
"""
