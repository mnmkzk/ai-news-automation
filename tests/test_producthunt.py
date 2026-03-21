"""Unit tests for collectors/producthunt.py — ProductHuntCollector."""

from unittest.mock import patch

from collectors.producthunt import ProductHuntCollector
from tests.conftest import make_rss_entry, make_feed


class TestProductHuntCollector:

    def _make_collector(self):
        return ProductHuntCollector()

    @patch("collectors.producthunt.feedparser.parse")
    def test_ai_keyword_match(self, mock_parse):
        """UT-PH-001: AIキーワード合致製品の収集."""
        entry = make_rss_entry(title="AI-powered chatbot", summary="Uses machine learning")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].language == "en"
        assert result[0].source_name == "producthunt"

    @patch("collectors.producthunt.feedparser.parse")
    def test_non_ai_excluded(self, mock_parse):
        """UT-PH-002: AI無関係な製品の除外."""
        entry = make_rss_entry(title="Recipe sharing app", summary="Share your favorite recipes")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 0

    @patch("collectors.producthunt.feedparser.parse")
    @patch("collectors.producthunt.config.MAX_ARTICLES_PER_SOURCE", 10)
    def test_max_early_break(self, mock_parse):
        """UT-PH-003: MAX到達での早期break."""
        entries = [
            make_rss_entry(title=f"AI tool {i}", link=f"https://ph.com/{i}",
                           summary="artificial intelligence")
            for i in range(20)
        ]
        mock_parse.return_value = make_feed(entries)
        result = self._make_collector().collect()
        assert len(result) == 10

    @patch("collectors.producthunt.feedparser.parse")
    @patch("collectors.producthunt.config.MAX_ARTICLES_PER_SOURCE", 10)
    def test_fewer_than_max(self, mock_parse):
        """UT-PH-004: AI合致がMAX未満."""
        entries = [
            make_rss_entry(title="AI tool 1", link="https://ph.com/1", summary="ai powered"),
            make_rss_entry(title="Cooking app", link="https://ph.com/2", summary="recipes"),
            make_rss_entry(title="AI tool 2", link="https://ph.com/3", summary="machine learning"),
            make_rss_entry(title="Music player", link="https://ph.com/4", summary="play music"),
            make_rss_entry(title="AI tool 3", link="https://ph.com/5", summary="chatbot"),
        ]
        mock_parse.return_value = make_feed(entries)
        result = self._make_collector().collect()
        assert len(result) == 3

    @patch("collectors.producthunt.feedparser.parse")
    def test_description_fallback(self, mock_parse):
        """UT-PH-005: descriptionフォールバック."""
        entry = make_rss_entry(title="AI Tool", link="https://ph.com/1")
        del entry.__dict__["summary"]
        entry.__dict__["description"] = "An AI-powered tool"
        entry.get = lambda key, default="": entry.__dict__.get(key, default)
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].summary_raw == "An AI-powered tool"
