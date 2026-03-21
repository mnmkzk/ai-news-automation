import logging
import re

import anthropic

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


def _parse_batch_response(text: str, articles: list[Article]) -> list[dict]:
    """Claude応答をパースして記事ごとの要約に分割."""
    results = []
    # 「---記事N---」で分割
    sections = re.split(r"---記事\d+---", text)
    sections = [s.strip() for s in sections if s.strip()]

    for i, section in enumerate(sections):
        article = articles[i] if i < len(articles) else None

        # 各セクションを抽出
        title_match = re.search(r"【タイトル】(.+?)(?=\n【|$)", section, re.DOTALL)
        what_match = re.search(r"【これ、なに？】(.+?)(?=\n【|$)", section, re.DOTALL)
        why_match = re.search(r"【何がすごいの？】(.+?)(?=\n【|$)", section, re.DOTALL)
        how_match = re.search(r"【あなたの生活・仕事はどう変わる？】(.+?)(?=\n【|$)", section, re.DOTALL)

        results.append({
            "article": article.to_dict() if article else {},
            "summary_title": title_match.group(1).strip() if title_match else "",
            "what_is_this": what_match.group(1).strip() if what_match else "",
            "why_amazing": why_match.group(1).strip() if why_match else "",
            "how_changes_life": how_match.group(1).strip() if how_match else "",
            "raw_summary": section,
        })

    return results


def summarize_batch(articles: list[Article]) -> list[dict]:
    """記事をバッチでClaudeに送信して要約を取得."""
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY is not set")
        return [{"article": a.to_dict(), "summary": "(no API key)"} for a in articles]

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
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
            logger.info(f"Sending batch {i // batch_size + 1} ({len(batch)} articles) to Claude...")
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            parsed = _parse_batch_response(response_text, batch)
            all_results.extend(parsed)

            logger.info(
                f"  -> Tokens: {response.usage.input_tokens} in / "
                f"{response.usage.output_tokens} out"
            )

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            for a in batch:
                all_results.append({"article": a.to_dict(), "summary": f"(error: {e})"})

    return all_results
