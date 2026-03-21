# ANA (AI News Automation)

AIニュースを自動収集し、専門用語なしで一般向けに要約・配信するシステム。

## プロジェクト構成

```
ANA/
├── main.py                     # エントリポイント（収集→要約→出力の3フェーズ）
├── config.py                   # 全設定（API設定、RSS URL、スクレイピング設定）
├── collectors/                 # データ収集（各ソースごとに1ファイル）
│   ├── base.py                 # Article dataclass + BaseCollector ABC
│   ├── hatena.py               # はてブIT（RSS）
│   ├── reddit.py               # r/ChatGPT（RSS）
│   ├── official_blogs.py       # OpenAI/Anthropic Blog（RSS）
│   ├── rss_newsletters.py      # Rundown AI/Ben's Bites（RSS）
│   ├── producthunt.py          # Product Hunt（RSS+AIキーワードフィルタ）
│   ├── prtimes.py              # PR TIMES（BeautifulSoupスクレイピング）
│   └── twitter.py              # X/Twitter（Nitter RSS、失敗時スキップ）
├── summarizer/                 # Claude API連携
│   ├── client.py               # Anthropic SDK wrapper、バッチ処理（5記事/回）
│   ├── prompts.py              # プロンプトテンプレート（要約・ツイート）
│   └── filter.py               # 実用性スコアリング、重複排除
├── output/                     # 出力生成
│   ├── note_formatter.py       # note用Markdownレポート → reports/ana_report_YYYYMMDD.md
│   └── tweet_formatter.py      # X投稿案 → reports/tweets_YYYYMMDD.md
├── storage/
│   └── json_store.py           # ローカルJSON永続化（data/配下）
├── data/                       # 収集データキャッシュ（gitignore対象）
└── reports/                    # 生成レポート出力先（gitignore対象）
```

## 技術スタック

- Python 3.12
- Anthropic SDK（Claude Sonnet）— 要約・ツイート生成
- feedparser — RSS収集
- BeautifulSoup4 + lxml — HTMLスクレイピング
- requests — HTTP通信
- playwright — ブラウザ自動化（将来拡張用）
- python-dotenv — 環境変数管理

## 実行方法

```bash
# Python PATHを通す（Windows）
export PATH="/c/Users/mnmkz/AppData/Local/Programs/Python/Python312:/c/Users/mnmkz/AppData/Local/Programs/Python/Python312/Scripts:$PATH"

# 本番実行（.envにANTHROPIC_API_KEYが必要）
python main.py

# APIなしテスト（収集＋フィルタのみ、Claude呼び出しスキップ）
python main.py --dry-run

# キャッシュ済みデータで再実行（収集をスキップ）
python main.py --skip-collect

# 特定日付で実行
python main.py --date 20260321
```

## 設計ルール

- **コレクターの独立性**: 各コレクターはBaseCollectorを継承し、`collect() -> list[Article]` を実装する。1つのコレクターが失敗しても他に影響しない（main.pyのtry/exceptで保護）
- **RSS優先**: 可能な限りRSSフィードを使用。スクレイピングはRSS不可の場合のみ
- **APIコスト管理**: HTMLタグ除去後にClaude送信、1記事最大2000文字に制限、5記事ずつバッチ処理
- **要約の3セクション形式**: 【これ、なに？】【何がすごいの？】【あなたの生活・仕事はどう変わる？】
- **新しいソース追加時**: collectors/配下に新ファイルを作成し、BaseCollectorを継承 → main.pyのcollect_all()にインスタンスを追加

## 環境変数（.env）

```
ANTHROPIC_API_KEY=sk-ant-...
```

## 主要な設定値（config.py）

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| CLAUDE_MODEL | claude-sonnet-4-20250514 | 使用するClaudeモデル |
| MAX_ARTICLES_PER_SOURCE | 10 | ソースあたりの最大取得数 |
| MAX_ARTICLES_TO_SUMMARIZE | 15 | Claude要約に送る最大記事数 |
| REQUEST_TIMEOUT | 10秒 | HTTP リクエストタイムアウト |
| SCRAPE_DELAY | 1.5秒 | スクレイピング間隔 |
