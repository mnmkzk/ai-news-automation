"""Unit tests for collectors/hatena.py — HatenaCollector."""

from unittest.mock import patch

import pytest
from collectors.hatena import HatenaCollector
from tests.conftest import make_rss_entry, make_feed


class TestHatenaCollector:

    def _make_collector(self):
        return HatenaCollector()

    @patch("collectors.hatena.feedparser.parse")
    def test_ai_keyword_match(self, mock_parse):
        """UT-HATENA-001: AIキーワード合致記事の収集."""
        entry = make_rss_entry(title="ChatGPTの使い方", summary="便利な活用法")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].source_name == "hatena_bookmark"
        assert result[0].language == "ja"

    @patch("collectors.hatena.feedparser.parse")
    def test_multiple_keywords(self, mock_parse):
        """UT-HATENA-002: 複数キーワードでの合致確認."""
        entries = [
            make_rss_entry(title="機械学習入門", link="https://example.com/1"),
            make_rss_entry(title="AIの最新動向", link="https://example.com/2"),
            make_rss_entry(title="GPT活用術", link="https://example.com/3"),
        ]
        mock_parse.return_value = make_feed(entries)
        result = self._make_collector().collect()
        assert len(result) == 3

    @patch("collectors.hatena.feedparser.parse")
    def test_non_ai_excluded(self, mock_parse):
        """UT-HATENA-003: AI無関係な記事は除外."""
        entry = make_rss_entry(title="今日の天気予報", summary="晴れ")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 0

    @patch("collectors.hatena.feedparser.parse")
    @patch("collectors.hatena.config.MAX_ARTICLES_PER_SOURCE", 10)
    def test_max_articles_limit(self, mock_parse):
        """UT-HATENA-004: MAX_ARTICLES_PER_SOURCE の上限."""
        entries = [
            make_rss_entry(title=f"AI記事{i}", link=f"https://example.com/{i}")
            for i in range(15)
        ]
        mock_parse.return_value = make_feed(entries)
        result = self._make_collector().collect()
        assert len(result) <= 10

    @patch("collectors.hatena.feedparser.parse")
    def test_html_unescape(self, mock_parse):
        """UT-HATENA-005: HTMLエンティティのアンエスケープ."""
        entry = make_rss_entry(
            title="AI &amp; 機械学習 &lt;最新&gt;",
            summary="ChatGPT &amp; Claude",
        )
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].title == "AI & 機械学習 <最新>"

    @patch("collectors.hatena.feedparser.parse")
    def test_missing_summary(self, mock_parse):
        """UT-HATENA-006: summary フィールド欠落."""
        # Entry without 'summary' key — .get("summary", "") returns ""
        entry = make_rss_entry(title="AI最新ニュース")
        # Remove summary from the entry's data
        del entry.__dict__["summary"]
        entry.get = lambda key, default="": entry.__dict__.get(key, default)
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].summary_raw == ""

    @patch("collectors.hatena.feedparser.parse")
    def test_bookmark_count_metadata(self, mock_parse):
        """UT-HATENA-007: はてブ数のmetadata格納."""
        entry = make_rss_entry(
            title="ChatGPT最新情報", hatena_bookmarkcount="150",
        )
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert result[0].metadata["bookmarks"] == "150"

    @patch("collectors.hatena.feedparser.parse")
    def test_empty_feed(self, mock_parse):
        """UT-HATENA-008: 空フィード."""
        mock_parse.return_value = make_feed([])
        result = self._make_collector().collect()
        assert result == []
