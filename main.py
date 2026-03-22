"""ANA (AI News Automation) - Daily AI news pipeline."""

import argparse
import logging
from datetime import date

import config
from storage import json_store

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ana")


def collect_all() -> list:
    """Phase 1: Collect articles from all sources."""
    from collectors.hatena import HatenaCollector
    from collectors.reddit import RedditCollector
    from collectors.official_blogs import OfficialBlogsCollector
    from collectors.rss_newsletters import RSSNewsletterCollector
    from collectors.producthunt import ProductHuntCollector
    from collectors.prtimes import PRTimesCollector
    from collectors.twitter import TwitterCollector

    collectors = [
        HatenaCollector(),
        RedditCollector(),
        OfficialBlogsCollector(),
        RSSNewsletterCollector(),
        ProductHuntCollector(),
        PRTimesCollector(),
        TwitterCollector(),
    ]

    all_articles = []
    for collector in collectors:
        try:
            logger.info(f"Collecting from {collector.source_name}...")
            articles = collector.collect()
            logger.info(f"  -> {len(articles)} articles collected")
            all_articles.extend(articles)
        except Exception as e:
            logger.warning(f"  -> FAILED: {collector.source_name}: {e}")

    return all_articles


def summarize_articles(articles: list, dry_run: bool = False) -> list[dict]:
    """Phase 2: Filter, select, and summarize."""
    from summarizer.filter import filter_and_deduplicate
    from summarizer.selector import select_top_articles
    from summarizer.client import summarize_batch

    # ルールベースで候補を絞り込み（最大15件）
    candidates = filter_and_deduplicate(articles)
    logger.info(f"Rule filter: {len(candidates)} candidates")

    if dry_run:
        logger.info("Dry run mode - skipping Gemini API calls")
        return [{"article": a.to_dict(), "summary": "(dry run)"} for a in candidates[:config.MAX_ARTICLES_TO_SUMMARIZE]]

    # GeminiがAI編集長として最終5件を選定
    selected = select_top_articles(candidates)
    logger.info(f"Gemini selector: {len(selected)} articles selected for summarization")

    summarized = summarize_batch(selected)
    return summarized


def generate_output(summarized: list[dict], d: date | None = None):
    """Phase 3: Generate note report and tweet drafts."""
    from output.note_formatter import generate_note_report
    from output.tweet_formatter import generate_tweet_drafts

    target_date = d or date.today()

    report_path = generate_note_report(summarized, target_date)
    logger.info(f"Note report saved to {report_path}")

    tweet_path = generate_tweet_drafts(summarized, target_date)
    logger.info(f"Tweet drafts saved to {tweet_path}")


def main():
    parser = argparse.ArgumentParser(description="ANA - AI News Automation")
    parser.add_argument("--dry-run", action="store_true", help="Skip Claude API calls")
    parser.add_argument("--skip-collect", action="store_true", help="Use cached raw data")
    parser.add_argument("--date", type=str, default=None, help="Target date (YYYYMMDD)")
    args = parser.parse_args()

    target_date = None
    if args.date:
        target_date = date(int(args.date[:4]), int(args.date[4:6]), int(args.date[6:8]))

    # Phase 1: Collect
    if args.skip_collect:
        logger.info("Skipping collection, loading cached data...")
        articles = json_store.load_raw_articles(target_date)
        if not articles:
            logger.error("No cached data found. Run without --skip-collect first.")
            return
    else:
        articles = collect_all()
        json_store.save_raw_articles(articles, target_date)

    logger.info(f"Total articles collected: {len(articles)}")

    # Phase 2: Summarize
    summarized = summarize_articles(articles, dry_run=args.dry_run)
    json_store.save_summarized(summarized, target_date)

    # Phase 3: Output
    generate_output(summarized, target_date)

    logger.info("Done!")


if __name__ == "__main__":
    main()
