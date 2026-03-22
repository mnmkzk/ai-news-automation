"""Geminiを使って候補記事から最終的に掲載する記事を選定するモジュール."""
import logging
import re

from google import genai
from google.genai import types

import config
from collectors.base import Article

logger = logging.getLogger(__name__)

SELECTOR_PROMPT = """以下は今日収集したAIニュースの候補{count}件です。

{articles_list}

「AIに関心のある日本の社会人」が今日最も知りたい記事を{n}件選んでください。

選定基準（優先順）:
1. 話題の新規性・インパクト（業界を変えうる発表、リリース）
2. 実務への影響度（仕事・生活に具体的に役立つ情報）
3. トピックの多様性（似たテーマが重複しないように）

選んだ記事の番号を、カンマ区切りで出力してください。
例: 1,3,7,9,12
番号のみ出力し、説明・前置きは一切不要です。"""


def select_top_articles(
    candidates: list[Article],
    n: int | None = None,
) -> list[Article]:
    """候補記事からGeminiが読者目線でn件を選定して返す.

    API失敗時は候補の先頭n件をフォールバックとして返す。
    """
    n = n or config.MAX_ARTICLES_TO_SUMMARIZE

    if len(candidates) <= n:
        return candidates

    if not config.GEMINI_API_KEY:
        logger.warning("Selector: GEMINI_API_KEY not set, using top candidates")
        return candidates[:n]

    articles_list = "\n".join(
        f"{i + 1}. {a.title}  [{a.source_name}]"
        for i, a in enumerate(candidates)
    )

    prompt = SELECTOR_PROMPT.format(
        count=len(candidates),
        articles_list=articles_list,
        n=n,
    )

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=256,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = response.text.strip()
        logger.debug(f"Selector raw response: {raw!r}")

        # "1,3,7,9,12" 形式をパース
        numbers = [int(x.strip()) for x in re.findall(r"\d+", raw)]
        selected = []
        for num in numbers:
            if 1 <= num <= len(candidates):
                article = candidates[num - 1]
                if article not in selected:
                    selected.append(article)
            if len(selected) >= n:
                break

        if not selected:
            raise ValueError(f"No valid numbers parsed from: {raw!r}")

        logger.info(
            f"Selector: {len(candidates)} candidates -> {len(selected)} selected "
            f"(indices: {[candidates.index(a) + 1 for a in selected]})"
        )
        return selected

    except Exception as e:
        logger.warning(f"Selector: Gemini selection failed ({e}), falling back to top {n}")
        return candidates[:n]
