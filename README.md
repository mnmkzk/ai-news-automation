# ANA (AI News Automation)

AIニュースを自動収集し、専門用語なしで一般向けに要約・配信するシステム。

## 概要

最新のAIニュースやSNSの流行を「専門用語なし」で解説。海外・国内の情報を自動収集し、一般のビジネスパーソンや主婦・学生でも直感的に理解できる内容で毎日配信します。

## 機能

### 📰 マルチソース・データ収集
- **Product Hunt**: 毎日投稿される新作AIアプリのトレンド
- **The Rundown AI / Ben's Bites**: 非エンジニア向けニュースレター
- **OpenAI / Anthropic Blog**: 公式の主要アップデート
- **はてなブックマーク（ITカテゴリ）**: 日本で話題のAIネタ
- **PR TIMES（AI検索）**: 国内企業のAI導入事例
- **X/Twitter**: AI活用インフルエンサーのバズ投稿

### ✨ 非エンジニア向け要約エンジン
Claude 3.5 Sonnets による「かみ砕き要約」：
- **【これ、なに？】**: 専門用語なし、身近な例え話で解説
- **【何がすごいの？】**: 数字や比較で凄さを強調
- **【あなたの生活・仕事はどう変わる？】**: 具体的なメリット提示

### 📄 アウトプット生成
- **note形式**: 読みやすいMarkdownレポート
- **X投稿**: 140文字以内のツイート案

## 技術スタック

- **Python 3.12**
- **Claude 3.5 Sonnet API** - 要約・翻訳
- **feedparser** - RSS収集
- **BeautifulSoup4 + lxml** - HTMLスクレイピング
- **requests** - HTTP通信
- **python-dotenv** - 環境変数管理

## セットアップ

```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# .env ファイルを作成（APIキー設定）
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

## 実行方法

```bash
# 本番実行（.env に ANTHROPIC_API_KEY 設定）
python main.py

# APIなしテスト（収集＋フィルタのみ）
python main.py --dry-run

# キャッシュ済みデータで再実行（収集をスキップ）
python main.py --skip-collect

# 特定日付で実行
python main.py --date 20260321
```

## テスト

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ -v --cov=. --cov-report=term-missing
```

**テスト結果**: 141件すべてPASS、カバレッジ **99%**

## プロジェクト構成

```
src/
├── collectors/          # データ収集（各ソース別）
│   ├── base.py         # Article dataclass + BaseCollector
│   ├── hatena.py       # はてなブックマーク
│   ├── reddit.py       # Reddit（r/ChatGPT）
│   ├── official_blogs.py    # OpenAI / Anthropic Blog
│   ├── rss_newsletters.py   # Rundown AI / Ben's Bites
│   ├── producthunt.py       # Product Hunt
│   ├── prtimes.py          # PR TIMES
│   └── twitter.py          # X/Twitter（Nitter RSS）
│
├── summarizer/         # Claude API連携
│   ├── client.py       # Anthropic SDK wrapper
│   ├── prompts.py      # プロンプトテンプレート
│   └── filter.py       # スコアリング・重複排除
│
├── output/             # 出力生成
│   ├── note_formatter.py    # note用Markdown
│   └── tweet_formatter.py   # X投稿案
│
├── storage/            # ローカル永続化
│   └── json_store.py   # JSON保存・読込
│
├── tests/              # 単体テスト（141件）
│   ├── conftest.py    # 共通フィクスチャ
│   ├── test_*.py      # 各モジュールのテスト
│   └── ...
│
├── main.py             # エントリポイント（3フェーズパイプライン）
├── config.py           # 全設定（RSS URL、API設定等）
├── requirements.txt    # 依存パッケージ
├── .gitignore         # Git除外ファイル
└── README.md          # このファイル
```

## 設計ルール

- **コレクターの独立性**: 各コレクターは BaseCollector を継承。1つの失敗が他に影響しない
- **RSS優先**: 可能な限り RSS を使用。スクレイピングは RSS 不可の場合のみ
- **APIコスト管理**: HTML タグ除去後に Claude 送信、1記事最大 2000 文字、5 記事ずつバッチ処理
- **要約の3セクション形式**: 専門用語なし、数字・比較、具体的メリット

## ライセンス

MIT

## 作成者

Claude（Anthropic SDK）による自動開発

---

詳細は `CLAUDE.md` を参照してください。
