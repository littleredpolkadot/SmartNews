"""Scheduler for running the news aggregation on a schedule."""

import asyncio
import os
from datetime import datetime

import schedule
from dotenv import load_dotenv

from src.main import NewsAggregator


def run_digest():
    """Run the digest generation."""
    print(f"\n🕐 Running scheduled digest at {datetime.now()}")
    
    try:
        aggregator = NewsAggregator()
        asyncio.run(aggregator.generate_digest(output_format="both"))
    except Exception as e:
        print(f"❌ Error running digest: {e}")


def main():
    """Main entry point for the scheduler."""
    load_dotenv()
    
    digest_time = os.getenv("DIGEST_TIME", "08:00")
    
    print(f"📰 News Aggregator Scheduler")
    print(f"   Scheduled time: {digest_time}")
    print(f"   Press Ctrl+C to stop\n")
    
    # Schedule daily digest
    schedule.every().day.at(digest_time).do(run_digest)
    
    # Also run once immediately
    print("Running initial digest...")
    run_digest()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        asyncio.run(asyncio.sleep(60))


if __name__ == "__main__":
    main()
