"""Unit tests for collectors/base.py — Article dataclass."""

import pytest
from collectors.base import Article, BaseCollector


class TestArticleCreation:
    """UT-BASE-001 ~ 002, 008"""

    def test_required_fields_only(self):
        """UT-BASE-001: 必須フィールドのみで生成."""
        a = Article(title="テスト", url="https://example.com", source_name="test")
        assert a.title == "テスト"
        assert a.url == "https://example.com"
        assert a.source_name == "test"
        assert a.summary_raw == ""
        assert a.published_at == ""
        assert a.language == "ja"
        assert a.metadata == {}

    def test_all_fields(self, full_article):
        """UT-BASE-002: 全フィールド指定で生成."""
        a = full_article
        assert a.title == "ChatGPTの新機能が便利"
        assert a.language == "ja"
        assert a.metadata == {"bookmarks": "150"}

    def test_empty_title_allowed(self):
        """UT-BASE-008: 空文字タイトルのArticle."""
        a = Article(title="", url="https://example.com", source_name="test")
        assert a.title == ""


class TestArticleSerialization:
    """UT-BASE-003 ~ 007"""

    def test_to_dict(self, full_article):
        """UT-BASE-003: to_dict() 正常動作."""
        d = full_article.to_dict()
        assert isinstance(d, dict)
        expected_keys = {"title", "url", "source_name", "summary_raw",
                         "published_at", "language", "metadata"}
        assert set(d.keys()) == expected_keys

    def test_from_dict(self):
        """UT-BASE-004: from_dict() 正常動作."""
        data = {
            "title": "テスト",
            "url": "https://example.com",
            "source_name": "test",
            "summary_raw": "概要",
            "published_at": "2026-03-21",
            "language": "ja",
            "metadata": {"key": "value"},
        }
        a = Article.from_dict(data)
        assert isinstance(a, Article)
        assert a.title == "テスト"
        assert a.metadata == {"key": "value"}

    def test_roundtrip(self, full_article):
        """UT-BASE-005: to_dict() → from_dict() ラウンドトリップ."""
        restored = Article.from_dict(full_article.to_dict())
        assert restored == full_article

    def test_metadata_with_emoji(self):
        """UT-BASE-006: metadataに日本語・絵文字を含む."""
        a = Article(
            title="テスト", url="https://example.com", source_name="test",
            metadata={"tag": "🤖AIテスト"},
        )
        d = a.to_dict()
        assert d["metadata"]["tag"] == "🤖AIテスト"
        restored = Article.from_dict(d)
        assert restored.metadata["tag"] == "🤖AIテスト"

    def test_from_dict_missing_required_key(self):
        """UT-BASE-007: from_dict() に必須キー欠落."""
        with pytest.raises(TypeError):
            Article.from_dict({"title": "テスト"})
