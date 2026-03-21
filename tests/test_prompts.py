"""Unit tests for summarizer/prompts.py — prompt templates."""

from summarizer.prompts import (
    SYSTEM_PROMPT,
    ARTICLE_SUMMARY_PROMPT,
    BATCH_SUMMARY_PROMPT,
    TWEET_PROMPT,
)


class TestPromptTemplates:

    def test_system_prompt_not_empty(self):
        """UT-PROMPT-001: SYSTEM_PROMPTが空でない."""
        assert len(SYSTEM_PROMPT) > 0
        assert "専門用語" in SYSTEM_PROMPT
        assert "小学" in SYSTEM_PROMPT

    def test_batch_summary_format(self):
        """UT-PROMPT-002: BATCH_SUMMARY_PROMPT の.format()成功."""
        result = BATCH_SUMMARY_PROMPT.format(
            count=3, articles_text="テスト記事", placeholder="N",
        )
        assert "3" in result
        assert "テスト記事" in result

    def test_tweet_prompt_format(self):
        """UT-PROMPT-003: TWEET_PROMPT の.format()成功."""
        result = TWEET_PROMPT.format(summary="テスト要約")
        assert "テスト要約" in result
        assert "140文字" in result

    def test_article_summary_format(self):
        """UT-PROMPT-004: ARTICLE_SUMMARY_PROMPT の.format()成功."""
        result = ARTICLE_SUMMARY_PROMPT.format(
            title="T", source="S", content="C",
        )
        assert "これ、なに？" in result
        assert "何がすごいの？" in result
        assert "あなたの生活・仕事はどう変わる？" in result
