import logging
from datetime import date
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def generate_note_report(summarized: list[dict], target_date: date | None = None) -> Path:
    """要約済み記事からnote用Markdownレポートを生成."""
    d = target_date or date.today()
    date_str = d.strftime("%Y年%m月%d日")
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = weekdays[d.weekday()]

    lines = [
        f"# 今日のAIニュースまとめ ({date_str}({weekday}))",
        "",
        f"> スマホで3分で読める、今日のAIニュースをお届けします。",
        f"> 専門用語なし。誰でも分かるように解説しています。",
        "",
        "---",
        "",
    ]

    # 目次
    lines.append("## 目次")
    for i, item in enumerate(summarized, 1):
        title = item.get("summary_title") or item.get("article", {}).get("title", f"ニュース{i}")
        lines.append(f"{i}. {title}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 各記事
    for i, item in enumerate(summarized, 1):
        title = item.get("summary_title") or item.get("article", {}).get("title", f"ニュース{i}")
        source = item.get("article", {}).get("source_name", "")
        url = item.get("article", {}).get("url", "")

        lines.append(f"## {i}. {title}")
        lines.append("")

        what = item.get("what_is_this", "")
        why = item.get("why_amazing", "")
        how = item.get("how_changes_life", "")

        if what:
            lines.append(f"### これ、なに？")
            lines.append(what)
            lines.append("")

        if why:
            lines.append(f"### 何がすごいの？")
            lines.append(why)
            lines.append("")

        if how:
            lines.append(f"### あなたの生活・仕事はどう変わる？")
            lines.append(how)
            lines.append("")

        # raw_summaryがあってパース済みフィールドがない場合（フォールバック）
        if not (what or why or how):
            raw = item.get("raw_summary") or item.get("summary", "")
            if raw:
                lines.append(raw)
                lines.append("")

        if url:
            lines.append(f"*ソース: [{source}]({url})*")
            lines.append("")

        lines.append("---")
        lines.append("")

    # フッター
    lines.append("*このまとめは ANA (AI News Automation) により自動生成されました。*")

    content = "\n".join(lines)
    filename = f"ana_report_{d.strftime('%Y%m%d')}.md"
    path = config.REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path
