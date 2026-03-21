"""Unit tests for summarizer/filter.py — filter & scoring."""

import pytest
from unittest.mock import patch

from collectors.base import Article
from summarizer.filter import _normalize_url, _score_article, filter_and_deduplicate


# ===========================================================================
# _normalize_url()
# ===========================================================================

class TestNormalizeUrl:

    def test_strips_query_string(self):
        """UT-FIL-001: クエリ文字列の除去."""
        assert _normalize_url("https://example.com/article?utm=123&ref=tw") == "example.com/article"

    def test_strips_fragment(self):
        """UT-FIL-002: フラグメントの除去."""
        assert _normalize_url("https://example.com/article#section1") == "example.com/article"

    def test_lowercase(self):
        """UT-FIL-003: 大文字小文字の統一."""
        assert _normalize_url("https://Example.COM/Article/") == "example.com/article"

    def test_strips_trailing_slash(self):
        """UT-FIL-004: 末尾スラッシュの除去."""
        assert _normalize_url("https://example.com/article/") == "example.com/article"

    def test_empty_string(self):
        """UT-FIL-005: 空文字列."""
        result = _normalize_url("")
        assert result == ""

    def test_no_scheme(self):
        """UT-FIL-006: スキームなしURL."""
        result = _normalize_url("example.com/article")
        # urlparse puts it in path when no scheme
        assert "example.com/article" in result


# ===========================================================================
# _score_article()
# ===========================================================================

class TestScoreArticle:

    def _make_article(self, title="", summary_raw="", metadata=None):
        return Article(
            title=title, url="https://example.com/test",
            source_name="test", summary_raw=summary_raw,
            metadata=metadata or {},
        )

    def test_single_exclude_keyword(self):
        """UT-FIL-007: 除外キーワード1つ → -10."""
        a = self._make_article(title="arxiv最新情報")
        assert _score_article(a) == -10.0

    def test_multiple_exclude_keywords(self):
        """UT-FIL-008: 除外キーワード3つ → -30."""
        a = self._make_article(title="arxiv 論文 gradient descent")
        assert _score_article(a) == -30.0

    def test_single_boost_keyword(self):
        """UT-FIL-009: ブーストキーワード1つ → +2."""
        a = self._make_article(title="無料ツール紹介")
        assert _score_article(a) >= 2.0

    def test_multiple_boost_keywords(self):
        """UT-FIL-010: ブーストキーワード3つ → +6."""
        a = self._make_article(title="無料 新機能 便利")
        assert _score_article(a) >= 6.0

    def test_mixed_exclude_and_boost(self):
        """UT-FIL-011: 除外+ブーストの混合."""
        a = self._make_article(title="arxiv 便利")
        score = _score_article(a)
        assert score == -8.0  # -10 + 2

    def test_bookmarks_boost(self):
        """UT-FIL-012: ブックマーク数による加点."""
        a = self._make_article(metadata={"bookmarks": "200"})
        score = _score_article(a)
        assert score == 10.0  # min(200/10, 10) = 10

    def test_bookmarks_cap_at_10(self):
        """UT-FIL-013: ブックマーク数の上限キャップ."""
        a = self._make_article(metadata={"bookmarks": "500"})
        score = _score_article(a)
        assert score == 10.0  # min(500/10, 10) = 10

    def test_bookmarks_non_numeric(self):
        """UT-FIL-014: ブックマーク数が非数値."""
        a = self._make_article(metadata={"bookmarks": "N/A"})
        score = _score_article(a)
        assert score == 0.0

    def test_bookmarks_zero(self):
        """UT-FIL-015: ブックマーク数 = 0."""
        a = self._make_article(metadata={"bookmarks": "0"})
        score = _score_article(a)
        assert score == 0.0  # 0 is falsy but "0".isdigit() is True → 0/10=0

    def test_empty_metadata(self):
        """UT-FIL-016: metadataが空dict."""
        a = self._make_article(metadata={})
        score = _score_article(a)
        assert score == 0.0

    def test_hatena_bookmarks_key_match(self):
        """UT-FIL-017: はてブmetadataキー一致の検証.

        hatena.py stores as metadata={"bookmarks": ...} which matches
        filter.py's metadata.get("bookmarks"). Verify they work together.
        """
        # Simulating what hatena.py actually stores
        a = self._make_article(metadata={"bookmarks": "150"})
        score = _score_article(a)
        expected_boost = min(150 / 10, 10)  # = 10.0
        assert score == expected_boost


# ===========================================================================
# filter_and_deduplicate()
# ===========================================================================

class TestFilterAndDeduplicate:

    def _make_article(self, title="テスト", url="https://example.com/test",
                      summary_raw="", metadata=None):
        return Article(
            title=title, url=url, source_name="test",
            summary_raw=summary_raw, metadata=metadata or {},
        )

    def test_dedup_same_url(self):
        """UT-FIL-018: 重複URL記事の排除."""
        a1 = self._make_article(title="記事A", url="https://example.com/1")
        a2 = self._make_article(title="記事B", url="https://example.com/1")
        result = filter_and_deduplicate([a1, a2])
        assert len(result) == 1
        assert result[0].title == "記事A"  # first one kept

    def test_dedup_query_difference(self):
        """UT-FIL-019: クエリ違いの同一URL重複排除."""
        a1 = self._make_article(url="https://example.com/article?utm=1")
        a2 = self._make_article(url="https://example.com/article?ref=2")
        result = filter_and_deduplicate([a1, a2])
        assert len(result) == 1

    def test_sorted_by_score_desc(self):
        """UT-FIL-020: スコア降順ソート."""
        low = self._make_article(title="普通の記事", url="https://example.com/1")
        high = self._make_article(title="無料 新機能 便利", url="https://example.com/2")
        result = filter_and_deduplicate([low, high])
        assert result[0].title == "無料 新機能 便利"

    def test_exclude_below_minus5(self):
        """UT-FIL-021: スコア -5 以下の除外."""
        bad = self._make_article(title="arxiv論文", url="https://example.com/1")
        good = self._make_article(title="便利ツール", url="https://example.com/2")
        result = filter_and_deduplicate([bad, good])
        assert all(a.title != "arxiv論文" for a in result)

    def test_boundary_exactly_minus5(self):
        """UT-FIL-022: スコアちょうど -5 (> -5 なので除外)."""
        # Need an article scoring exactly -5. This is hard to craft precisely,
        # but we can test the filter condition: s > -5 means -5 is excluded.
        # Use mock to control score.
        a = self._make_article(url="https://example.com/1")
        with patch("summarizer.filter._score_article", return_value=-5.0):
            result = filter_and_deduplicate([a])
            assert len(result) == 0

    def test_boundary_minus4_9_included(self):
        """UT-FIL-023: スコア -4.9 は含まれる."""
        a = self._make_article(url="https://example.com/1")
        with patch("summarizer.filter._score_article", return_value=-4.9):
            result = filter_and_deduplicate([a])
            assert len(result) == 1

    @patch("summarizer.filter.config.MAX_ARTICLES_TO_SUMMARIZE", 15)
    def test_max_articles_limit(self):
        """UT-FIL-024: MAX_ARTICLES_TO_SUMMARIZE 制限."""
        articles = [
            self._make_article(title=f"記事{i}", url=f"https://example.com/{i}")
            for i in range(20)
        ]
        result = filter_and_deduplicate(articles)
        assert len(result) <= 15

    @patch("summarizer.filter.config.MAX_ARTICLES_TO_SUMMARIZE", 15)
    def test_exactly_max_articles(self):
        """UT-FIL-025: ちょうどMAX件."""
        articles = [
            self._make_article(title=f"記事{i}", url=f"https://example.com/{i}")
            for i in range(15)
        ]
        result = filter_and_deduplicate(articles)
        assert len(result) == 15

    @patch("summarizer.filter.config.MAX_ARTICLES_TO_SUMMARIZE", 15)
    def test_fewer_than_max(self):
        """UT-FIL-026: MAX未満."""
        articles = [
            self._make_article(title=f"記事{i}", url=f"https://example.com/{i}")
            for i in range(3)
        ]
        result = filter_and_deduplicate(articles)
        assert len(result) == 3

    def test_empty_input(self):
        """UT-FIL-027: 空リスト入力."""
        result = filter_and_deduplicate([])
        assert result == []

    def test_single_article(self):
        """UT-FIL-028: 1件のみ."""
        a = self._make_article(url="https://example.com/1")
        result = filter_and_deduplicate([a])
        assert len(result) == 1
