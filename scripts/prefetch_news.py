#!/usr/bin/env python3
"""
Pre-fetch and cache news digest.

Run this script to pre-populate the news cache so the web app
loads instantly with fresh content.

Usage:
    python scripts/prefetch_news.py [--timeframe 7d] [--no-relevance]
    
Examples:
    # Fetch past week with relevance ranking (default)
    python scripts/prefetch_news.py
    
    # Fetch past 3 days
    python scripts/prefetch_news.py --timeframe 3d
    
    # Add to crontab to run daily at 6 AM:
    # 0 6 * * * cd /path/to/NewsApp && .venv/bin/python scripts/prefetch_news.py
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import NewsAggregator, TimeFrame
from src.cache import save_digest_cache


async def prefetch_digest(timeframe: str = "7d", rank_by_relevance: bool = True):
    """Fetch news and save to cache."""
    
    timeframe_map = {
        "24h": TimeFrame.HOURS_24,
        "3d": TimeFrame.DAYS_3,
        "7d": TimeFrame.WEEK,
        "all": TimeFrame.ALL,
    }
    tf = timeframe_map.get(timeframe, TimeFrame.WEEK)
    
    print(f"🚀 Pre-fetching news digest...")
    print(f"   Timeframe: {tf.label}")
    print(f"   Relevance ranking: {'Yes' if rank_by_relevance else 'No'}")
    print()
    
    aggregator = NewsAggregator()
    
    # Fetch articles
    print("📥 Fetching articles...")
    articles_by_category = await aggregator.fetch_all(
        timeframe=tf,
        rank_by_relevance=rank_by_relevance,
    )
    
    total = sum(len(a) for a in articles_by_category.values())
    print(f"   Found {total} articles across {len(articles_by_category)} categories")
    print()
    
    # Generate summaries
    print("🤖 Generating summaries...")
    category_data = await aggregator.generate_summaries(articles_by_category)
    
    # Convert articles to serializable format (same as webapp)
    for cat_id, cat_info in category_data.items():
        cat_info["articles"] = [
            {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "published_at": a.published_at.strftime("%B %d, %Y") if a.published_at else None,
                "summary": a.summary,
                "relevance_score": getattr(a, 'relevance_score', None),
            }
            for a in cat_info.get("articles", [])[:5]
        ]
    
    # Save to cache
    print()
    print("💾 Saving to cache...")
    cache_path = save_digest_cache(
        data=category_data,
        timeframe=timeframe,
        rank_by_relevance=rank_by_relevance,
    )
    print(f"   Saved to: {cache_path}")
    
    print()
    print("✅ Pre-fetch complete! The web app will now load instantly.")


def main():
    parser = argparse.ArgumentParser(
        description="Pre-fetch and cache news digest for faster loading."
    )
    parser.add_argument(
        "--timeframe", "-t",
        choices=["24h", "3d", "7d", "all"],
        default="7d",
        help="Time period to fetch articles from (default: 7d)"
    )
    parser.add_argument(
        "--no-relevance",
        action="store_true",
        help="Disable AI relevance ranking (faster, but sorted by date only)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(prefetch_digest(
        timeframe=args.timeframe,
        rank_by_relevance=not args.no_relevance,
    ))


if __name__ == "__main__":
    main()
