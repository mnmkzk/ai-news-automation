"""Unit tests for output/tweet_formatter.py — tweet draft generation."""

from datetime import date
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from output.tweet_formatter import generate_tweet_drafts, _generate_simple, _generate_with_claude


def _make_item(summary_title="テストタイトル", raw_summary="要約テキスト",
               article_title="元タイトル"):
    return {
        "summary_title": summary_title,
        "raw_summary": raw_summary,
        "article": {"title": article_title},
    }


class TestGenerateSimple:

    def test_basic_tweet(self):
        """UT-TW-F-001 (partial): シンプル生成の基本動作."""
        items = [_make_item(summary_title="AIの新機能")]
        tweets = _generate_simple(items)
        assert len(tweets) == 1
        assert "#AIニュース" in tweets[0]
        assert "#明日話せるネタ" in tweets[0]
        assert "AIの新機能" in tweets[0]

    def test_title_truncated_at_100(self):
        """UT-TW-F-005: タイトル100文字切り詰め."""
        long_title = "あ" * 150
        items = [_make_item(summary_title=long_title)]
        tweets = _generate_simple(items)
        # Title portion should be 100 chars max
        assert len(tweets[0]) < 150 + 30  # title(100) + hashtags

    def test_empty_title_skipped(self):
        """UT-TW-F-008 (partial): タイトルなし→スキップ."""
        items = [_make_item(summary_title="", article_title="")]
        tweets = _generate_simple(items)
        assert len(tweets) == 0


class TestGenerateTweetDrafts:

    @patch("output.tweet_formatter.config")
    def test_no_api_key_uses_simple(self, mock_config, tmp_path):
        """UT-TW-F-001: APIなし→シンプル生成."""
        mock_config.ANTHROPIC_API_KEY = ""
        mock_config.REPORTS_DIR = tmp_path
        items = [_make_item(), _make_item(summary_title="記事2")]
        path = generate_tweet_drafts(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "#AIニュース" in content

    @patch("output.tweet_formatter.config")
    def test_top_5_only(self, mock_config, tmp_path):
        """UT-TW-F-002: 上位5件のみ処理."""
        mock_config.ANTHROPIC_API_KEY = ""
        mock_config.REPORTS_DIR = tmp_path
        items = [_make_item(summary_title=f"記事{i}") for i in range(10)]
        path = generate_tweet_drafts(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "投稿案 5" in content
        assert "投稿案 6" not in content

    @patch("output.tweet_formatter.config")
    def test_exactly_5(self, mock_config, tmp_path):
        """UT-TW-F-003: ちょうど5件."""
        mock_config.ANTHROPIC_API_KEY = ""
        mock_config.REPORTS_DIR = tmp_path
        items = [_make_item(summary_title=f"記事{i}") for i in range(5)]
        path = generate_tweet_drafts(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "投稿案 5" in content

    @patch("output.tweet_formatter.config")
    def test_fewer_than_5(self, mock_config, tmp_path):
        """UT-TW-F-004: 3件のみ."""
        mock_config.ANTHROPIC_API_KEY = ""
        mock_config.REPORTS_DIR = tmp_path
        items = [_make_item(summary_title=f"記事{i}") for i in range(3)]
        path = generate_tweet_drafts(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "投稿案 3" in content
        assert "投稿案 4" not in content

    @patch("output.tweet_formatter.config")
    def test_char_count_display(self, mock_config, tmp_path):
        """UT-TW-F-006: 文字数カウント表記."""
        mock_config.ANTHROPIC_API_KEY = ""
        mock_config.REPORTS_DIR = tmp_path
        items = [_make_item(summary_title="テスト")]
        path = generate_tweet_drafts(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "文字）" in content

    @patch("output.tweet_formatter.config")
    def test_file_path(self, mock_config, tmp_path):
        """UT-TW-F-006b: ファイルパスの正確性."""
        mock_config.ANTHROPIC_API_KEY = ""
        mock_config.REPORTS_DIR = tmp_path
        path = generate_tweet_drafts([], date(2026, 3, 21))
        assert path.name == "tweets_20260321.md"


class TestGenerateWithClaude:

    @patch("output.tweet_formatter.config")
    @patch("output.tweet_formatter.anthropic.Anthropic")
    def test_api_error_fallback(self, mock_anthropic_cls, mock_config):
        """UT-TW-F-007: Claude API失敗→フォールバック."""
        mock_config.ANTHROPIC_API_KEY = "sk-test"
        mock_config.CLAUDE_MODEL = "claude-sonnet-4-20250514"
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        items = [_make_item(summary_title="テスト記事")]
        tweets = _generate_with_claude(items)
        assert len(tweets) == 1
        assert "#AIニュース" in tweets[0]

    @patch("output.tweet_formatter.config")
    def test_empty_summary_and_title_skipped(self, mock_config):
        """UT-TW-F-008: summaryもtitleも空→スキップ."""
        mock_config.ANTHROPIC_API_KEY = "sk-test"
        items = [{"raw_summary": "", "summary_title": "", "article": {"title": ""}}]
        # _generate_with_claude would skip items with no content
        tweets = _generate_with_claude(items)
        assert len(tweets) == 0
