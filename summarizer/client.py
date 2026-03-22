import logging
import re

from google import genai
from google.genai import types

import config
from collectors.base import Article
from summarizer.prompts import SYSTEM_PROMPT, BATCH_SUMMARY_PROMPT

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    """HTMLタグを除去してAPIコストを削減."""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:2000]  # 1記事あたり最大2000文字


def _build_articles_text(articles: list[Article]) -> str:
    parts = []
    for i, a in enumerate(articles, 1):
        content = _strip_html(a.summary_raw) or a.title
        parts.append(
            f"【記事{i}】\n"
            f"タイトル: {a.title}\n"
            f"ソース: {a.source_name}\n"
            f"内容: {content}\n"
            f"URL: {a.url}"
        )
    return "\n\n".join(parts)


def _clean_field(text: str) -> str:
    """フィールド値から末尾のMarkdown記号や余分な空白を除去."""
    # 末尾の ###, ---, ** などを除去
    text = re.sub(r"[\n\r]+[\s#\-*]+$", "", text.strip())
    return text.strip()


def _parse_batch_response(text: str, articles: list[Article]) -> list[dict]:
    """Gemini応答をパースして記事ごとの要約に分割."""
    results = []
    # 「---記事N---」で分割
    sections = re.split(r"---記事\d+---", text)
    # 【...】マーカーを含まないセクション（前置きテキスト等）は除外
    sections = [s.strip() for s in sections if s.strip() and "【" in s]

    for i, section in enumerate(sections):
        article = articles[i] if i < len(articles) else None

        # 各セクションを抽出
        title_match = re.search(r"【タイトル】(.+?)(?=\n【|$)", section, re.DOTALL)
        what_match = re.search(r"【ニュース要約】(.+?)(?=\n【|$)", section, re.DOTALL)
        why_match = re.search(r"【何がすごいの？】(.+?)(?=\n【|$)", section, re.DOTALL)
        how_match = re.search(r"【あなたの生活・仕事はどう変わる？】(.+?)(?=\n【|$)", section, re.DOTALL)

        results.append({
            "article": article.to_dict() if article else {},
            "summary_title": _clean_field(title_match.group(1)) if title_match else "",
            "what_is_this": _clean_field(what_match.group(1)) if what_match else "",
            "why_amazing": _clean_field(why_match.group(1)) if why_match else "",
            "how_changes_life": _clean_field(how_match.group(1)) if how_match else "",
            "raw_summary": section,
        })

    # パース結果が記事数より少ない場合、不足分をフォールバックで補完
    for j in range(len(results), len(articles)):
        results.append({
            "article": articles[j].to_dict(),
            "summary_title": "",
            "what_is_this": "",
            "why_amazing": "",
            "how_changes_life": "",
            "raw_summary": "",
        })

    return results


def summarize_batch(articles: list[Article]) -> list[dict]:
    """記事をバッチでGeminiに送信して要約を取得."""
    if not config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set")
        return [{"article": a.to_dict(), "summary": "(no API key)"} for a in articles]

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    all_results = []

    # 5記事ずつバッチ処理
    batch_size = 5
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        articles_text = _build_articles_text(batch)

        prompt = BATCH_SUMMARY_PROMPT.format(
            count=len(batch),
            articles_text=articles_text,
            placeholder="N",
        )

        try:
            logger.info(f"Sending batch {i // batch_size + 1} ({len(batch)} articles) to Gemini...")
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=config.GEMINI_MAX_TOKENS,
                ),
            )

            response_text = response.text
            parsed = _parse_batch_response(response_text, batch)
            all_results.extend(parsed)

            try:
                usage = response.usage_metadata
                logger.info(
                    f"  -> Tokens: {usage.prompt_token_count} in / "
                    f"{usage.candidates_token_count} out"
                )
            except AttributeError:
                pass

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            for a in batch:
                all_results.append({"article": a.to_dict(), "summary": f"(error: {e})"})

    return all_results
