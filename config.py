import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR.parent.parent / "reports"
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Gemini Settings ---
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MAX_TOKENS = 4096
MAX_ARTICLES_PER_SOURCE = 10
MAX_FILTER_CANDIDATES = 15      # ルールフィルタ後にGeminiに渡す候補数
MAX_ARTICLES_TO_SUMMARIZE = 5   # Gemini選定後に要約する最終件数

# --- Article Selection ---
TWITTER_ACCOUNT_WEIGHTS = {
    "masahirochaen": 6,
    "kensuu": 5,
    "kajiken0630": 5,
    "rimojun": 4,
}

CROSS_SOURCE_TOPICS = [
    "openai", "gpt-5", "gpt-4", "chatgpt",
    "anthropic", "claude",
    "google", "gemini", "deepmind",
    "meta", "llama",
    "microsoft", "copilot",
    "sora", "dall-e",
    "deepseek", "perplexity", "mistral",
    "nvidia", "groq",
]

# --- RSS Feeds ---
RSS_FEEDS = {
    "hatena_it": "https://b.hatena.ne.jp/hotentry/it.rss",
    "reddit_chatgpt": "https://www.reddit.com/r/ChatGPT/.rss",
    "openai_blog": "https://openai.com/blog/rss.xml",
    "anthropic_blog": "https://www.anthropic.com/rss.xml",
    "rundown_ai": "https://www.therundown.ai/feed",
    "bensbites": "https://bensbites.beehiiv.com/feed",
}

# --- Product Hunt ---
PRODUCTHUNT_FEED_URL = "https://www.producthunt.com/feed"
PRODUCTHUNT_AI_KEYWORDS = [
    "ai", "artificial intelligence", "gpt", "llm", "chatbot",
    "machine learning", "copilot", "claude", "gemini", "openai",
    "automation", "generative",
]

# --- PR TIMES ---
PRTIMES_SEARCH_URL = "https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word=AI"

# --- Twitter/X Influencers ---
TWITTER_ACCOUNTS = [
    "kajiken0630",    # 深津氏
    "masahirochaen",  # 茶圓氏
    "rimojun",        # リモじゅん氏
    "kensuu",         # けんすう氏
]
NITTER_BASE_URL = "https://nitter.net"

# --- Scraping ---
REQUEST_TIMEOUT = 10
PLAYWRIGHT_TIMEOUT = 30000
SCRAPE_DELAY = 1.5

# --- Logging ---
LOG_LEVEL = "INFO"
