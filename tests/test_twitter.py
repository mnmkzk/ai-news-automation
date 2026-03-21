"""Unit tests for collectors/twitter.py — TwitterCollector."""

from unittest.mock import patch

from collectors.twitter import TwitterCollector
from tests.conftest import make_rss_entry, make_feed


class TestTwitterCollector:

    def _make_collector(self):
        return TwitterCollector()

    @patch("collectors.twitter.config.TWITTER_ACCOUNTS", ["testuser"])
    @patch("collectors.twitter.feedparser.parse")
    def test_ai_tweet_collected(self, mock_parse):
        """UT-TW-001: AI関連ツイートの収集."""
        entry = make_rss_entry(title="ChatGPTすごい", link="https://twitter.com/1")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].source_name == "twitter_testuser"

    @patch("collectors.twitter.config.TWITTER_ACCOUNTS", ["testuser"])
    @patch("collectors.twitter.feedparser.parse")
    def test_non_ai_excluded(self, mock_parse):
        """UT-TW-002: AI無関係ツイートの除外."""
        entry = make_rss_entry(title="今日のランチ", link="https://twitter.com/1")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 0

    @patch("collectors.twitter.config.TWITTER_ACCOUNTS", ["testuser"])
    @patch("collectors.twitter.feedparser.parse")
    def test_nitter_unavailable(self, mock_parse):
        """UT-TW-003: Nitter不通（bozo=True, entries=[]）."""
        mock_parse.return_value = make_feed([], bozo=True)
        result = self._make_collector().collect()
        assert result == []

    @patch("collectors.twitter.config.TWITTER_ACCOUNTS", ["user1", "user2"])
    @patch("collectors.twitter.feedparser.parse")
    def test_one_account_fails(self, mock_parse):
        """UT-TW-004: 1アカウント失敗→他は継続."""
        entry = make_rss_entry(title="AI最新情報", link="https://twitter.com/1")
        mock_parse.side_effect = [Exception("Timeout"), make_feed([entry])]
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].source_name == "twitter_user2"

    @patch("collectors.twitter.config.TWITTER_ACCOUNTS", ["testuser"])
    @patch("collectors.twitter.feedparser.parse")
    def test_title_truncated_at_200(self, mock_parse):
        """UT-TW-005: タイトル200文字制限."""
        long_title = "AI" + "あ" * 300
        entry = make_rss_entry(title=long_title, link="https://twitter.com/1")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert len(result[0].title) <= 200

    @patch("collectors.twitter.config.TWITTER_ACCOUNTS", ["testuser"])
    @patch("collectors.twitter.feedparser.parse")
    def test_title_exactly_200(self, mock_parse):
        """UT-TW-006: タイトルちょうど200文字."""
        title = "AI" + "x" * 198  # 200 chars total
        entry = make_rss_entry(title=title, link="https://twitter.com/1")
        mock_parse.return_value = make_feed([entry])
        result = self._make_collector().collect()
        assert len(result) == 1
        assert len(result[0].title) == 200
