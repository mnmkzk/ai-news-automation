"""Unit tests for summarizer/client.py — HTML stripping, batch building, response parsing."""

from unittest.mock import patch, MagicMock
from types import SimpleNamespace

import pytest

from collectors.base import Article
from summarizer.client import _strip_html, _build_articles_text, _parse_batch_response, summarize_batch
from tests.conftest import MOCK_CLAUDE_RESPONSE_2_ARTICLES


# ===========================================================================
# _strip_html()
# ===========================================================================

class TestStripHtml:

    def test_basic_tags(self):
        """UT-CLI-001: 基本HTMLタグ除去."""
        assert _strip_html("<p>Hello <b>World</b></p>") == "Hello World"

    def test_nested_tags(self):
        """UT-CLI-002: ネストされたタグ除去."""
        assert _strip_html("<div><p><span>Test</span></p></div>") == "Test"

    def test_whitespace_collapse(self):
        """UT-CLI-003: 連続空白の圧縮."""
        assert _strip_html("Hello   \n\n  World") == "Hello World"

    def test_exactly_2000_chars(self):
        """UT-CLI-004: ちょうど2000文字."""
        text = "a" * 2000
        assert len(_strip_html(text)) == 2000

    def test_truncate_at_2000(self):
        """UT-CLI-005: 2001文字→2000文字に切り詰め."""
        text = "a" * 2001
        result = _strip_html(text)
        assert len(result) == 2000

    def test_empty_string(self):
        """UT-CLI-006: 空文字列."""
        assert _strip_html("") == ""

    def test_html_entities_not_decoded(self):
        """UT-CLI-007: HTMLエンティティはデコードされない（正規表現のみ）."""
        # _strip_html uses regex to remove tags only, not html.unescape
        result = _strip_html("&amp; &lt; &gt;")
        assert "&amp;" in result


# ===========================================================================
# _build_articles_text()
# ===========================================================================

class TestBuildArticlesText:

    def _make_article(self, title="Test", summary_raw="Summary", url="https://example.com"):
        return Article(title=title, url=url, source_name="test", summary_raw=summary_raw)

    def test_normal_build_2_articles(self):
        """UT-CLI-008: 正常構築（2件）."""
        articles = [
            self._make_article(title="記事1", summary_raw="概要1", url="https://a.com"),
            self._make_article(title="記事2", summary_raw="概要2", url="https://b.com"),
        ]
        result = _build_articles_text(articles)
        assert "【記事1】" in result
        assert "【記事2】" in result
        assert "タイトル: 記事1" in result
        assert "URL: https://a.com" in result

    def test_empty_summary_falls_back_to_title(self):
        """UT-CLI-009: summary_raw 空→titleフォールバック."""
        a = self._make_article(title="Fallback Title", summary_raw="")
        result = _build_articles_text([a])
        assert "内容: Fallback Title" in result

    def test_single_article(self):
        """UT-CLI-010: 1件のみ."""
        a = self._make_article(title="Solo", summary_raw="Only one")
        result = _build_articles_text([a])
        assert "【記事1】" in result
        assert "【記事2】" not in result


# ===========================================================================
# _parse_batch_response()
# ===========================================================================

class TestParseBatchResponse:

    def _make_articles(self, n):
        return [
            Article(title=f"Article {i}", url=f"https://example.com/{i}", source_name="test")
            for i in range(n)
        ]

    def test_normal_parse_2_articles(self):
        """UT-CLI-011: 正常パース（2記事）."""
        articles = self._make_articles(2)
        results = _parse_batch_response(MOCK_CLAUDE_RESPONSE_2_ARTICLES, articles)
        assert len(results) == 2
        assert results[0]["summary_title"] == "AIで仕事が変わる"
        assert results[0]["what_is_this"] == "ChatGPTに新機能が追加されました。"
        assert results[0]["why_amazing"] == "処理速度が3倍になりました。"
        assert results[0]["how_changes_life"] == "資料作成が1分で終わります。"
        assert results[1]["summary_title"] == "無料AIツール登場"

    def test_missing_sections(self):
        """UT-CLI-012: セクション欠落."""
        text = "---記事1---\n【タイトル】テストタイトル\n"
        articles = self._make_articles(1)
        results = _parse_batch_response(text, articles)
        assert len(results) == 1
        assert results[0]["summary_title"] == "テストタイトル"
        assert results[0]["what_is_this"] == ""
        assert results[0]["why_amazing"] == ""
        assert results[0]["how_changes_life"] == ""

    def test_fewer_sections_than_articles(self):
        """UT-CLI-013: 記事数とセクション数不一致."""
        text = "---記事1---\n【タイトル】Only One\n【これ、なに？】Description\n"
        articles = self._make_articles(3)
        results = _parse_batch_response(text, articles)
        assert len(results) == 1

    def test_unexpected_format(self):
        """UT-CLI-014: 完全に想定外のフォーマット."""
        text = "これは想定外のレスポンスです"
        articles = self._make_articles(1)
        results = _parse_batch_response(text, articles)
        # No ---記事N--- delimiter → either empty or one raw result
        # The split produces one non-empty section when no delimiter found
        assert len(results) <= 1

    def test_title_with_next_section(self):
        """UT-CLI-015: タイトル抽出が次の【で正しく止まる."""
        text = "---記事1---\n【タイトル】短いタイトル\n【これ、なに？】説明文\n"
        articles = self._make_articles(1)
        results = _parse_batch_response(text, articles)
        assert results[0]["summary_title"] == "短いタイトル"


# ===========================================================================
# summarize_batch()
# ===========================================================================

class TestSummarizeBatch:

    def _make_articles(self, n):
        return [
            Article(title=f"Article {i}", url=f"https://example.com/{i}",
                    source_name="test", summary_raw=f"Summary {i}")
            for i in range(n)
        ]

    @patch("summarizer.client.config.ANTHROPIC_API_KEY", "")
    def test_no_api_key(self):
        """UT-CLI-016: APIキー未設定."""
        articles = self._make_articles(3)
        results = summarize_batch(articles)
        assert len(results) == 3
        assert all(r["summary"] == "(no API key)" for r in results)

    @patch("summarizer.client.config.ANTHROPIC_API_KEY", "sk-test-key")
    @patch("summarizer.client.anthropic.Anthropic")
    def test_batch_size_5(self, mock_anthropic_cls):
        """UT-CLI-017: バッチ5件ずつ分割."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [SimpleNamespace(text="---記事1---\n【タイトル】Test\n")]
        mock_response.usage = SimpleNamespace(input_tokens=100, output_tokens=50)
        mock_client.messages.create.return_value = mock_response

        articles = self._make_articles(12)
        results = summarize_batch(articles)
        assert mock_client.messages.create.call_count == 3  # 5+5+2

    @patch("summarizer.client.config.ANTHROPIC_API_KEY", "sk-test-key")
    @patch("summarizer.client.anthropic.Anthropic")
    def test_exactly_5_articles(self, mock_anthropic_cls):
        """UT-CLI-018: ちょうど5件（1バッチ）."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [SimpleNamespace(text="---記事1---\n【タイトル】T\n")]
        mock_response.usage = SimpleNamespace(input_tokens=100, output_tokens=50)
        mock_client.messages.create.return_value = mock_response

        articles = self._make_articles(5)
        summarize_batch(articles)
        assert mock_client.messages.create.call_count == 1

    @patch("summarizer.client.config.ANTHROPIC_API_KEY", "sk-test-key")
    def test_empty_list(self):
        """UT-CLI-019: 0件（空リスト）."""
        results = summarize_batch([])
        assert results == []

    @patch("summarizer.client.config.ANTHROPIC_API_KEY", "sk-test-key")
    @patch("summarizer.client.anthropic.Anthropic")
    def test_api_error_handling(self, mock_anthropic_cls):
        """UT-CLI-020: API呼び出し失敗."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API rate limit")

        articles = self._make_articles(3)
        results = summarize_batch(articles)
        assert len(results) == 3
        assert all("error" in r["summary"] for r in results)
