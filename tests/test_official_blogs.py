"""Unit tests for collectors/official_blogs.py — OfficialBlogsCollector."""

from unittest.mock import patch, MagicMock

from collectors.official_blogs import OfficialBlogsCollector
from tests.conftest import make_rss_entry, make_feed


class TestOfficialBlogsCollector:

    def _make_collector(self):
        return OfficialBlogsCollector()

    @patch("collectors.official_blogs.feedparser.parse")
    def test_two_blogs_combined(self, mock_parse):
        """UT-BLOG-001: 2ブログ統合収集."""
        feed_a = make_feed([
            make_rss_entry(title=f"OpenAI Post {i}", link=f"https://openai.com/{i}")
            for i in range(3)
        ])
        feed_b = make_feed([
            make_rss_entry(title=f"Anthropic Post {i}", link=f"https://anthropic.com/{i}")
            for i in range(3)
        ])
        mock_parse.side_effect = [feed_a, feed_b]
        result = self._make_collector().collect()
        assert len(result) == 6
        source_names = {a.source_name for a in result}
        assert "openai_blog" in source_names
        assert "anthropic_blog" in source_names

    @patch("collectors.official_blogs.feedparser.parse")
    def test_one_blog_fails(self, mock_parse):
        """UT-BLOG-002: 1ブログのみ失敗."""
        feed_b = make_feed([
            make_rss_entry(title=f"Anthropic Post {i}", link=f"https://anthropic.com/{i}")
            for i in range(3)
        ])
        mock_parse.side_effect = [Exception("Network error"), feed_b]
        result = self._make_collector().collect()
        assert len(result) == 3
        assert all(a.source_name == "anthropic_blog" for a in result)

    @patch("collectors.official_blogs.feedparser.parse")
    def test_max_5_per_blog(self, mock_parse):
        """UT-BLOG-003: 各ブログ5件制限."""
        big_feed = make_feed([
            make_rss_entry(title=f"Post {i}", link=f"https://example.com/{i}")
            for i in range(10)
        ])
        mock_parse.return_value = big_feed
        result = self._make_collector().collect()
        # 2 blogs × 5 = 10 max
        assert len(result) <= 10

    @patch("collectors.official_blogs.feedparser.parse")
    def test_description_fallback(self, mock_parse):
        """UT-BLOG-004: summaryなし→descriptionフォールバック."""
        entry = make_rss_entry(title="Test Post", link="https://example.com/1")
        # Remove summary, add description
        del entry.__dict__["summary"]
        entry.__dict__["description"] = "Fallback description"
        entry.get = lambda key, default="": entry.__dict__.get(key, default)
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) >= 1
        # At least one article should have the description as summary_raw
        assert any(a.summary_raw == "Fallback description" for a in result)

    @patch("collectors.official_blogs.feedparser.parse")
    def test_both_blogs_fail(self, mock_parse):
        """UT-BLOG-005: 両ブログとも失敗."""
        mock_parse.side_effect = Exception("Network error")
        result = self._make_collector().collect()
        assert result == []
