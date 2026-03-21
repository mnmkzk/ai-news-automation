"""Unit tests for collectors/rss_newsletters.py — RSSNewsletterCollector."""

from unittest.mock import patch

from collectors.rss_newsletters import RSSNewsletterCollector
from tests.conftest import make_rss_entry, make_feed


class TestRSSNewsletterCollector:

    def _make_collector(self):
        return RSSNewsletterCollector()

    @patch("collectors.rss_newsletters.feedparser.parse")
    @patch("collectors.rss_newsletters.NEWSLETTER_FEEDS", {
        "rundown_ai": "https://rundown.ai/feed",
        "bensbites": "https://bensbites.com/feed",
    })
    def test_normal_collection(self, mock_parse):
        """UT-NEWS-001: 正常収集."""
        feed = make_feed([
            make_rss_entry(title=f"Newsletter {i}", link=f"https://example.com/{i}")
            for i in range(3)
        ])
        mock_parse.return_value = feed
        result = self._make_collector().collect()
        assert len(result) == 6  # 2 feeds × 3 entries
        assert all(a.language == "en" for a in result)

    @patch("collectors.rss_newsletters.feedparser.parse")
    @patch("collectors.rss_newsletters.NEWSLETTER_FEEDS", {
        "rundown_ai": None,
        "bensbites": "https://bensbites.com/feed",
    })
    def test_none_url_skipped(self, mock_parse):
        """UT-NEWS-002: URL が None のニュースレターをスキップ."""
        feed = make_feed([
            make_rss_entry(title="Newsletter 1", link="https://example.com/1"),
        ])
        mock_parse.return_value = feed
        result = self._make_collector().collect()
        assert len(result) == 1
        # feedparser.parse should only be called once (for bensbites)
        assert mock_parse.call_count == 1

    @patch("collectors.rss_newsletters.feedparser.parse")
    @patch("collectors.rss_newsletters.NEWSLETTER_FEEDS", {
        "rundown_ai": "https://rundown.ai/feed",
        "bensbites": "https://bensbites.com/feed",
    })
    def test_one_feed_fails(self, mock_parse):
        """UT-NEWS-003: 片方のフィード失敗."""
        feed = make_feed([
            make_rss_entry(title="OK Newsletter", link="https://example.com/1"),
        ])
        mock_parse.side_effect = [Exception("Timeout"), feed]
        result = self._make_collector().collect()
        assert len(result) == 1

    @patch("collectors.rss_newsletters.NEWSLETTER_FEEDS", {
        "rundown_ai": None,
        "bensbites": None,
    })
    def test_all_urls_none(self):
        """UT-NEWS-004: 両方URLなし."""
        result = self._make_collector().collect()
        assert result == []
