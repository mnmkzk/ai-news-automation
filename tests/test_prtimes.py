"""Unit tests for collectors/prtimes.py — PRTimesCollector."""

from unittest.mock import patch, MagicMock

import pytest
import requests

from collectors.prtimes import PRTimesCollector


def _make_html(*articles_html):
    """Build a mock PR TIMES search result HTML page."""
    body = "\n".join(articles_html)
    return f"<html><body>{body}</body></html>"


def _article_html(title="テスト記事", href="/main/html/rd/p/1.html",
                  summary="AI活用事例", date_text="2026-03-21",
                  has_title=True, has_summary=True, has_date=True):
    """Generate a single article element matching PR TIMES structure."""
    title_part = f'<h2><a href="{href}">{title}</a></h2>' if has_title else ""
    summary_part = f'<div class="list-article__summary">{summary}</div>' if has_summary else ""
    date_part = f'<time datetime="{date_text}">{date_text}</time>' if has_date else ""
    return f'<article class="list-article">{title_part}{summary_part}{date_part}</article>'


class TestPRTimesCollector:

    def _make_collector(self):
        return PRTimesCollector()

    def _mock_response(self, html_text, status_code=200):
        resp = MagicMock()
        resp.text = html_text
        resp.status_code = status_code
        resp.raise_for_status = MagicMock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = requests.HTTPError(f"{status_code} Error")
        return resp

    @patch("collectors.prtimes.requests.get")
    def test_normal_collection(self, mock_get):
        """UT-PR-001: 正常なHTML解析."""
        html = _make_html(
            _article_html(title="AI記事1", href="/main/1"),
            _article_html(title="AI記事2", href="/main/2"),
            _article_html(title="AI記事3", href="/main/3"),
        )
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert len(result) == 3
        assert all(a.language == "ja" for a in result)
        assert all(a.source_name == "prtimes" for a in result)

    @patch("collectors.prtimes.requests.get")
    def test_relative_url_conversion(self, mock_get):
        """UT-PR-002: 相対URLの絶対URL変換."""
        html = _make_html(_article_html(href="/main/html/rd/p/1.html"))
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert result[0].url == "https://prtimes.jp/main/html/rd/p/1.html"

    @patch("collectors.prtimes.requests.get")
    def test_absolute_url_kept(self, mock_get):
        """UT-PR-003: 絶対URLはそのまま保持."""
        html = _make_html(_article_html(href="https://prtimes.jp/main/html/rd/p/1.html"))
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert result[0].url == "https://prtimes.jp/main/html/rd/p/1.html"

    @patch("collectors.prtimes.requests.get")
    def test_no_title_skipped(self, mock_get):
        """UT-PR-004: タイトル要素なし→スキップ."""
        html = _make_html(
            _article_html(has_title=False),
            _article_html(title="Valid Article", href="/main/2"),
        )
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].title == "Valid Article"

    @patch("collectors.prtimes.requests.get")
    def test_http_error(self, mock_get):
        """UT-PR-005: HTTPエラー."""
        mock_get.return_value = self._mock_response("", status_code=500)
        with pytest.raises(requests.HTTPError):
            self._make_collector().collect()

    @patch("collectors.prtimes.requests.get")
    def test_missing_summary_and_date(self, mock_get):
        """UT-PR-006: 概要・日付の欠落."""
        html = _make_html(_article_html(has_summary=False, has_date=False))
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert len(result) == 1
        assert result[0].summary_raw == ""
        assert result[0].published_at == ""

    @patch("collectors.prtimes.requests.get")
    @patch("collectors.prtimes.config.MAX_ARTICLES_PER_SOURCE", 10)
    def test_max_articles_limit(self, mock_get):
        """UT-PR-007: MAX_ARTICLES_PER_SOURCE 境界値."""
        html = _make_html(*[
            _article_html(title=f"記事{i}", href=f"/main/{i}")
            for i in range(15)
        ])
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert len(result) == 10

    @patch("collectors.prtimes.requests.get")
    def test_empty_html(self, mock_get):
        """UT-PR-008: 記事0件のHTML."""
        html = "<html><body><p>検索結果なし</p></body></html>"
        mock_get.return_value = self._mock_response(html)
        result = self._make_collector().collect()
        assert result == []
