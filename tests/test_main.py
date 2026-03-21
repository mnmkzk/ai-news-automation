"""Unit tests for main.py — pipeline orchestration."""

from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from collectors.base import Article


def _make_articles(n, source="test"):
    return [
        Article(title=f"Article {i}", url=f"https://example.com/{i}",
                source_name=source, summary_raw=f"Summary {i}")
        for i in range(n)
    ]


# ===========================================================================
# collect_all()
# ===========================================================================

class TestCollectAll:

    @patch("collectors.twitter.TwitterCollector.collect", return_value=[])
    @patch("collectors.prtimes.PRTimesCollector.collect", return_value=[])
    @patch("collectors.producthunt.ProductHuntCollector.collect", return_value=[])
    @patch("collectors.rss_newsletters.RSSNewsletterCollector.collect", return_value=[])
    @patch("collectors.official_blogs.OfficialBlogsCollector.collect", return_value=[])
    @patch("collectors.reddit.RedditCollector.collect")
    @patch("collectors.hatena.HatenaCollector.collect")
    def test_all_collectors_success(self, mock_hatena, mock_reddit, *_others):
        """UT-MAIN-001: 全コレクター正常."""
        from main import collect_all
        mock_hatena.return_value = _make_articles(3, "hatena")
        mock_reddit.return_value = _make_articles(3, "reddit")
        # others return [] by default

        result = collect_all()
        assert len(result) == 6  # 3 + 3 + 0*5

    @patch("collectors.twitter.TwitterCollector.collect", return_value=[])
    @patch("collectors.prtimes.PRTimesCollector.collect", return_value=[])
    @patch("collectors.producthunt.ProductHuntCollector.collect", return_value=[])
    @patch("collectors.rss_newsletters.RSSNewsletterCollector.collect", return_value=[])
    @patch("collectors.official_blogs.OfficialBlogsCollector.collect", return_value=[])
    @patch("collectors.reddit.RedditCollector.collect")
    @patch("collectors.hatena.HatenaCollector.collect")
    def test_one_collector_fails(self, mock_hatena, mock_reddit, *_others):
        """UT-MAIN-002: 1コレクター失敗→他は継続."""
        from main import collect_all
        mock_hatena.side_effect = Exception("Network error")
        mock_reddit.return_value = _make_articles(3, "reddit")

        result = collect_all()
        assert len(result) == 3  # only reddit succeeded

    @patch("collectors.twitter.TwitterCollector.collect")
    @patch("collectors.prtimes.PRTimesCollector.collect")
    @patch("collectors.producthunt.ProductHuntCollector.collect")
    @patch("collectors.rss_newsletters.RSSNewsletterCollector.collect")
    @patch("collectors.official_blogs.OfficialBlogsCollector.collect")
    @patch("collectors.reddit.RedditCollector.collect")
    @patch("collectors.hatena.HatenaCollector.collect")
    def test_all_collectors_fail(self, *mock_collects):
        """UT-MAIN-003: 全コレクター失敗."""
        from main import collect_all
        for m in mock_collects:
            m.side_effect = Exception("Error")

        result = collect_all()
        assert result == []

    @patch("collectors.twitter.TwitterCollector.collect", return_value=[])
    @patch("collectors.prtimes.PRTimesCollector.collect", return_value=[])
    @patch("collectors.producthunt.ProductHuntCollector.collect", return_value=[])
    @patch("collectors.rss_newsletters.RSSNewsletterCollector.collect", return_value=[])
    @patch("collectors.official_blogs.OfficialBlogsCollector.collect", return_value=[])
    @patch("collectors.reddit.RedditCollector.collect", return_value=[])
    @patch("collectors.hatena.HatenaCollector.collect", return_value=[])
    def test_all_return_empty(self, *_):
        """UT-MAIN-004: 全コレクターが0件."""
        from main import collect_all
        result = collect_all()
        assert result == []


# ===========================================================================
# summarize_articles()
# ===========================================================================

class TestSummarizeArticles:

    @patch("summarizer.client.summarize_batch")
    @patch("summarizer.filter.filter_and_deduplicate")
    def test_dry_run_skips_api(self, mock_filter, mock_batch):
        """UT-MAIN-005: dry_run=True → API呼び出しなし."""
        from main import summarize_articles
        articles = _make_articles(5)
        mock_filter.return_value = articles

        result = summarize_articles(articles, dry_run=True)
        assert len(result) == 5
        assert all(r["summary"] == "(dry run)" for r in result)
        mock_batch.assert_not_called()

    @patch("summarizer.client.summarize_batch")
    @patch("summarizer.filter.filter_and_deduplicate")
    def test_normal_mode_calls_batch(self, mock_filter, mock_batch):
        """UT-MAIN-006: dry_run=False → summarize_batch呼び出し."""
        from main import summarize_articles
        articles = _make_articles(5)
        mock_filter.return_value = articles
        mock_batch.return_value = [{"article": a.to_dict(), "summary": "ok"} for a in articles]

        result = summarize_articles(articles, dry_run=False)
        mock_batch.assert_called_once_with(articles)
        assert len(result) == 5

    @patch("summarizer.client.summarize_batch")
    @patch("summarizer.filter.filter_and_deduplicate")
    def test_empty_input(self, mock_filter, mock_batch):
        """UT-MAIN-007: 空リスト入力."""
        from main import summarize_articles
        mock_filter.return_value = []

        result = summarize_articles([], dry_run=True)
        assert result == []


# ===========================================================================
# generate_output()
# ===========================================================================

class TestGenerateOutput:

    @patch("output.tweet_formatter.generate_tweet_drafts")
    @patch("output.note_formatter.generate_note_report")
    def test_with_date(self, mock_note, mock_tweet):
        """UT-MAIN-008: 正常出力（日付指定あり）."""
        from main import generate_output
        mock_note.return_value = "report.md"
        mock_tweet.return_value = "tweets.md"

        summarized = [{"article": {}, "summary": "test"}]
        target = date(2026, 3, 21)
        generate_output(summarized, target)

        mock_note.assert_called_once_with(summarized, target)
        mock_tweet.assert_called_once_with(summarized, target)

    @patch("output.tweet_formatter.generate_tweet_drafts")
    @patch("output.note_formatter.generate_note_report")
    def test_without_date_uses_today(self, mock_note, mock_tweet):
        """UT-MAIN-009: 日付なし→today()使用."""
        from main import generate_output
        mock_note.return_value = "report.md"
        mock_tweet.return_value = "tweets.md"

        generate_output([])
        call_date = mock_note.call_args[0][1]
        assert call_date == date.today()


# ===========================================================================
# main() — argument parsing
# ===========================================================================

class TestMainFunction:

    @patch("main.generate_output")
    @patch("main.json_store")
    @patch("main.summarize_articles")
    @patch("main.collect_all")
    def test_date_parsing(self, mock_collect, mock_summarize, mock_store, mock_output):
        """UT-MAIN-010: --date パース正常."""
        from main import main
        import sys

        mock_collect.return_value = _make_articles(3)
        mock_summarize.return_value = [{"summary": "test"}]

        with patch.object(sys, "argv", ["main.py", "--date", "20260321"]):
            main()

        save_call = mock_store.save_raw_articles.call_args
        assert save_call[0][1] == date(2026, 3, 21)
