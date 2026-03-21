import logging
from datetime import date
from pathlib import Path

from google import genai
from google.genai import types

import config
from summarizer.prompts import SYSTEM_PROMPT, TWEET_PROMPT

logger = logging.getLogger(__name__)


def generate_tweet_drafts(summarized: list[dict], target_date: date | None = None) -> Path:
    """要約済み記事からX投稿用のツイート案を生成."""
    d = target_date or date.today()

    tweets = []
    # 上位5件のみツイート案を作成
    top_articles = summarized[:5]

    if config.GEMINI_API_KEY:
        tweets = _generate_with_gemini(top_articles)
    else:
        tweets = _generate_simple(top_articles)

    # 保存
    lines = [
        f"# X投稿案 ({d.strftime('%Y/%m/%d')})",
        "",
        "以下の投稿案から選んで使ってください。",
        "",
    ]
    for i, tweet in enumerate(tweets, 1):
        lines.append(f"## 投稿案 {i}")
        lines.append(f"```")
        lines.append(tweet)
        lines.append(f"```")
        lines.append(f"（{len(tweet)}文字）")
        lines.append("")

    content = "\n".join(lines)
    filename = f"tweets_{d.strftime('%Y%m%d')}.md"
    path = config.REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


def _generate_with_gemini(articles: list[dict]) -> list[str]:
    """Gemini APIでツイート案を生成."""
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    tweets = []

    for item in articles:
        summary = item.get("raw_summary") or item.get("summary", "")
        title = item.get("summary_title") or item.get("article", {}).get("title", "")

        if not summary and not title:
            continue

        prompt = TWEET_PROMPT.format(summary=f"{title}\n{summary}")

        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=256,
                ),
            )
            tweet = response.text.strip()
            tweets.append(tweet)
        except Exception as e:
            logger.warning(f"Tweet generation failed: {e}")
            tweets.append(f"{title[:100]} #AIニュース")

    return tweets


def _generate_simple(articles: list[dict]) -> list[str]:
    """APIなしのシンプルなツイート生成（フォールバック）."""
    tweets = []
    for item in articles:
        title = item.get("summary_title") or item.get("article", {}).get("title", "")
        if title:
            tweet = f"{title[:100]} #AIニュース #明日話せるネタ"
            tweets.append(tweet)
    return tweets
