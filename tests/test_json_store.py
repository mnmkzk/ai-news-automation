"""Unit tests for storage/json_store.py — JSON persistence."""

import json
from datetime import date
from unittest.mock import patch

import pytest

from collectors.base import Article
from storage.json_store import (
    _date_str,
    save_raw_articles,
    load_raw_articles,
    save_summarized,
    load_summarized,
)


class TestDateStr:

    def test_with_date(self):
        """_date_str with explicit date."""
        assert _date_str(date(2026, 3, 21)) == "20260321"

    def test_default_today(self):
        """_date_str defaults to today."""
        result = _date_str()
        assert len(result) == 8
        assert result.isdigit()


class TestRawArticles:

    @patch("storage.json_store.config")
    def test_save_load_roundtrip(self, mock_config, tmp_path):
        """UT-STORE-001: save→load ラウンドトリップ."""
        mock_config.DATA_DIR = tmp_path
        articles = [
            Article(title="記事1", url="https://example.com/1", source_name="test",
                    summary_raw="概要1", metadata={"key": "value"}),
            Article(title="記事2", url="https://example.com/2", source_name="test"),
            Article(title="記事3", url="https://example.com/3", source_name="test"),
        ]
        d = date(2026, 3, 21)
        save_raw_articles(articles, d)
        loaded = load_raw_articles(d)
        assert len(loaded) == 3
        assert loaded[0].title == "記事1"
        assert loaded[0].metadata == {"key": "value"}
        assert loaded[2].title == "記事3"

    @patch("storage.json_store.config")
    def test_load_nonexistent_file(self, mock_config, tmp_path):
        """UT-STORE-003: 存在しないファイルのload."""
        mock_config.DATA_DIR = tmp_path
        result = load_raw_articles(date(2099, 12, 31))
        assert result == []

    @patch("storage.json_store.config")
    def test_filename_contains_date(self, mock_config, tmp_path):
        """UT-STORE-005: 日付指定によるファイル名."""
        mock_config.DATA_DIR = tmp_path
        path = save_raw_articles([], date(2026, 3, 21))
        assert "20260321" in path.name

    @patch("storage.json_store.config")
    def test_utf8_no_escape(self, mock_config, tmp_path):
        """UT-STORE-006: 日本語のUTF-8保存（エスケープなし）."""
        mock_config.DATA_DIR = tmp_path
        articles = [
            Article(title="日本語テスト🤖", url="https://example.com",
                    source_name="test"),
        ]
        path = save_raw_articles(articles, date(2026, 3, 21))
        raw_content = path.read_text(encoding="utf-8")
        assert "日本語テスト🤖" in raw_content
        assert "\\u" not in raw_content

    @patch("storage.json_store.config")
    def test_empty_list(self, mock_config, tmp_path):
        """UT-STORE-007: 空リストの保存と読み込み."""
        mock_config.DATA_DIR = tmp_path
        d = date(2026, 3, 21)
        save_raw_articles([], d)
        loaded = load_raw_articles(d)
        assert loaded == []

    @patch("storage.json_store.config")
    def test_default_date_today(self, mock_config, tmp_path):
        """UT-STORE-008: 日付未指定（デフォルト=今日）."""
        mock_config.DATA_DIR = tmp_path
        path = save_raw_articles([])
        today_str = date.today().strftime("%Y%m%d")
        assert today_str in path.name


class TestSummarized:

    @patch("storage.json_store.config")
    def test_save_load_roundtrip(self, mock_config, tmp_path):
        """UT-STORE-002: save→load ラウンドトリップ（summarized）."""
        mock_config.DATA_DIR = tmp_path
        data = [
            {"article": {"title": "A"}, "summary": "要約A"},
            {"article": {"title": "B"}, "summary": "要約B"},
        ]
        d = date(2026, 3, 21)
        save_summarized(data, d)
        loaded = load_summarized(d)
        assert len(loaded) == 2
        assert loaded[0]["article"]["title"] == "A"

    @patch("storage.json_store.config")
    def test_load_nonexistent_file(self, mock_config, tmp_path):
        """UT-STORE-004: 存在しないファイルのload（summarized）."""
        mock_config.DATA_DIR = tmp_path
        result = load_summarized(date(2099, 12, 31))
        assert result == []

    @patch("storage.json_store.config")
    def test_year_boundary(self, mock_config, tmp_path):
        """UT-STORE-009: 日付境界（年末年始）."""
        mock_config.DATA_DIR = tmp_path
        save_summarized([{"data": "dec31"}], date(2026, 12, 31))
        save_summarized([{"data": "jan01"}], date(2027, 1, 1))
        dec = load_summarized(date(2026, 12, 31))
        jan = load_summarized(date(2027, 1, 1))
        assert dec[0]["data"] == "dec31"
        assert jan[0]["data"] == "jan01"
