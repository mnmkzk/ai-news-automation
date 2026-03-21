import json
from datetime import date
from pathlib import Path

from collectors.base import Article
import config


def _date_str(d: date | None = None) -> str:
    return (d or date.today()).strftime("%Y%m%d")


def save_raw_articles(articles: list[Article], d: date | None = None) -> Path:
    path = config.DATA_DIR / f"raw_{_date_str(d)}.json"
    data = [a.to_dict() for a in articles]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_raw_articles(d: date | None = None) -> list[Article]:
    path = config.DATA_DIR / f"raw_{_date_str(d)}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Article.from_dict(item) for item in data]


def save_summarized(articles: list[dict], d: date | None = None) -> Path:
    path = config.DATA_DIR / f"summarized_{_date_str(d)}.json"
    path.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_summarized(d: date | None = None) -> list[dict]:
    path = config.DATA_DIR / f"summarized_{_date_str(d)}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
