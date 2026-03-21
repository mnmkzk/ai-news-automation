"""Unit tests for output/note_formatter.py — note report generation."""

from datetime import date
from unittest.mock import patch

import pytest

from output.note_formatter import generate_note_report


def _make_summarized_item(summary_title="テストタイトル", what="これはテスト",
                          why="すごいポイント", how="生活が変わる",
                          raw_summary="", article_title="元タイトル",
                          source_name="test_source",
                          url="https://example.com/article"):
    """Create a summarized dict matching the output format."""
    return {
        "summary_title": summary_title,
        "what_is_this": what,
        "why_amazing": why,
        "how_changes_life": how,
        "raw_summary": raw_summary,
        "article": {
            "title": article_title,
            "url": url,
            "source_name": source_name,
        },
    }


class TestGenerateNoteReport:

    @patch("output.note_formatter.config")
    def test_normal_report(self, mock_config, tmp_path):
        """UT-NOTE-001: 正常レポート生成."""
        mock_config.REPORTS_DIR = tmp_path
        items = [
            _make_summarized_item(summary_title="AIニュース1"),
            _make_summarized_item(summary_title="AIニュース2"),
        ]
        path = generate_note_report(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "# 今日のAIニュースまとめ" in content
        assert "## 目次" in content
        assert "## 1. AIニュース1" in content
        assert "## 2. AIニュース2" in content
        assert "### これ、なに？" in content
        assert "ANA" in content  # footer

    @patch("output.note_formatter.config")
    def test_date_format_saturday(self, mock_config, tmp_path):
        """UT-NOTE-002: 日付フォーマット（土曜日）."""
        mock_config.REPORTS_DIR = tmp_path
        path = generate_note_report([], date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "2026年03月21日(土)" in content

    @patch("output.note_formatter.config")
    def test_all_weekdays(self, mock_config, tmp_path):
        """UT-NOTE-003: 月曜日〜日曜日の全曜日."""
        mock_config.REPORTS_DIR = tmp_path
        # 2026-03-16 is Monday through 2026-03-22 is Sunday
        expected = ["月", "火", "水", "木", "金", "土", "日"]
        for i, wd in enumerate(expected):
            d = date(2026, 3, 16 + i)
            path = generate_note_report([], d)
            content = path.read_text(encoding="utf-8")
            assert f"({wd})" in content, f"Expected ({wd}) for {d}"

    @patch("output.note_formatter.config")
    def test_table_of_contents(self, mock_config, tmp_path):
        """UT-NOTE-004: 目次の番号付きリスト."""
        mock_config.REPORTS_DIR = tmp_path
        items = [
            _make_summarized_item(summary_title=f"タイトル{c}")
            for c in "ABC"
        ]
        path = generate_note_report(items, date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "1. タイトルA" in content
        assert "2. タイトルB" in content
        assert "3. タイトルC" in content

    @patch("output.note_formatter.config")
    def test_fallback_to_raw_summary(self, mock_config, tmp_path):
        """UT-NOTE-005: セクション欠落→raw_summaryフォールバック."""
        mock_config.REPORTS_DIR = tmp_path
        item = _make_summarized_item(what="", why="", how="", raw_summary="生のサマリー")
        path = generate_note_report([item], date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "生のサマリー" in content
        assert "### これ、なに？" not in content

    @patch("output.note_formatter.config")
    def test_fallback_to_article_title(self, mock_config, tmp_path):
        """UT-NOTE-006: summary_title欠落→article.titleフォールバック."""
        mock_config.REPORTS_DIR = tmp_path
        item = _make_summarized_item(summary_title="", article_title="元のタイトル")
        path = generate_note_report([item], date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "元のタイトル" in content

    @patch("output.note_formatter.config")
    def test_fallback_to_news_number(self, mock_config, tmp_path):
        """UT-NOTE-007: summary_title・article.titleキー自体が存在しない場合."""
        mock_config.REPORTS_DIR = tmp_path
        # article dict without "title" key at all → triggers default "ニュースN"
        item = {
            "summary_title": "",
            "what_is_this": "テスト",
            "why_amazing": "",
            "how_changes_life": "",
            "raw_summary": "",
            "article": {"url": "https://example.com", "source_name": "test"},
        }
        path = generate_note_report([item], date(2026, 3, 21))
        content = path.read_text(encoding="utf-8")
        assert "ニュース1" in content

    @patch("output.note_formatter.config")
    def test_empty_list(self, mock_config, tmp_path):
        """UT-NOTE-008: 空リスト入力."""
        mock_config.REPORTS_DIR = tmp_path
        path = generate_note_report([], date(2026, 3, 21))
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "# 今日のAIニュースまとめ" in content
        assert "ANA" in content

    @patch("output.note_formatter.config")
    def test_file_path(self, mock_config, tmp_path):
        """UT-NOTE-009: ファイルパスの正確性."""
        mock_config.REPORTS_DIR = tmp_path
        path = generate_note_report([], date(2026, 3, 21))
        assert path.name == "ana_report_20260321.md"
        assert path.parent == tmp_path
