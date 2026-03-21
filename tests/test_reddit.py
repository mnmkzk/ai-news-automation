"""Unit tests for collectors/reddit.py — RedditCollector."""

from unittest.mock import patch

from collectors.reddit import RedditCollector
from tests.conftest import make_rss_entry, make_feed


class TestRedditCollector:

    def _make_collector(self):
        return RedditCollector()

    @patch("collectors.reddit.feedparser.parse")
    def test_normal_collection_no_filter(self, mock_parse):
        """UT-REDDIT-001: 正常収集（フィルタなし）."""
        entries = [
            make_rss_entry(title="Funny cat video", link="https://reddit.com/1"),
            make_rss_entry(title="AI is great", link="https://reddit.com/2"),
            make_rss_entry(title="Random topic", link="https://reddit.com/3"),
        ]
        mock_parse.return_value = make_feed(entries)
        result = self._make_collector().collect()
        assert len(result) == 3
        assert all(a.language == "en" for a in result)
        assert all(a.source_name == "reddit_chatgpt" for a in result)

    @patch("collectors.reddit.feedparser.parse")
    def test_score_metadata(self, mock_parse):
        """UT-REDDIT-002: Redditスコアのmetadata格納."""
        entry = make_rss_entry(title="Test", score="42")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert result[0].metadata["score"] == "42"

    @patch("collectors.reddit.feedparser.parse")
    def test_empty_feed(self, mock_parse):
        """UT-REDDIT-003: 空フィード."""
        mock_parse.return_value = make_feed([])
        result = self._make_collector().collect()
        assert result == []

    @patch("collectors.reddit.feedparser.parse")
    @patch("collectors.reddit.config.MAX_ARTICLES_PER_SOURCE", 10)
    def test_max_articles_limit(self, mock_parse):
        """UT-REDDIT-004: MAX_ARTICLES_PER_SOURCE 境界値."""
        entries = [
            make_rss_entry(title=f"Post {i}", link=f"https://reddit.com/{i}")
            for i in range(15)
        ]
        mock_parse.return_value = make_feed(entries)
        result = self._make_collector().collect()
        assert len(result) == 10
