"""Flask web application for the News Aggregator."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from threading import Thread

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

from src.main import NewsAggregator, TimeFrame
from src.cache import load_digest_cache, save_digest_cache

load_dotenv()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static")
)

# Store for current digest data
digest_cache = {
    "data": None,
    "last_updated": None,
    "is_generating": False,
    "timeframe": "7d",
    "rank_by_relevance": True,
}


def load_cached_digest():
    """Load digest from file cache on startup."""
    global digest_cache
    
    cached = load_digest_cache(max_age_hours=168)  # Accept cache up to 7 days old
    if cached:
        digest_cache["data"] = cached["data"]
        digest_cache["last_updated"] = datetime.fromisoformat(cached["last_updated"])
        digest_cache["timeframe"] = cached.get("timeframe", "7d")
        digest_cache["rank_by_relevance"] = cached.get("rank_by_relevance", True)
        print(f"📰 Loaded cached digest from {digest_cache['last_updated']}")
        return True
    return False


# Load cache on module import (when app starts)
load_cached_digest()


def run_async(coro):
    """Run async coroutine in a new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def generate_digest_async(timeframe: str = "24h", rank_by_relevance: bool = True):
    """Generate digest and return category data."""
    # Map string to TimeFrame enum
    timeframe_map = {
        "24h": TimeFrame.HOURS_24,
        "3d": TimeFrame.DAYS_3,
        "7d": TimeFrame.WEEK,
        "all": TimeFrame.ALL,
    }
    tf = timeframe_map.get(timeframe, TimeFrame.HOURS_24)
    
    aggregator = NewsAggregator()
    
    # Fetch articles with timeframe and relevance ranking
    articles_by_category = await aggregator.fetch_all(
        timeframe=tf,
        rank_by_relevance=rank_by_relevance,
    )
    
    # Generate summaries
    category_data = await aggregator.generate_summaries(articles_by_category)
    
    # Convert articles to serializable format
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
    
    return category_data


def generate_digest_background(timeframe: str = "24h", rank_by_relevance: bool = True):
    """Background task to generate digest."""
    global digest_cache
    
    try:
        data = run_async(generate_digest_async(timeframe, rank_by_relevance))
        digest_cache["data"] = data
        digest_cache["last_updated"] = datetime.now()
        digest_cache["timeframe"] = timeframe
        digest_cache["rank_by_relevance"] = rank_by_relevance
        
        # Save to file cache for persistence
        save_digest_cache(
            data=data,
            timeframe=timeframe,
            rank_by_relevance=rank_by_relevance,
        )
        print(f"💾 Saved digest to cache")
    except Exception as e:
        print(f"Error generating digest: {e}")
    finally:
        digest_cache["is_generating"] = False


# Timeframe labels for display
TIMEFRAME_OPTIONS = [
    {"value": "24h", "label": "Past 24 Hours"},
    {"value": "3d", "label": "Past 3 Days"},
    {"value": "7d", "label": "Past Week"},
    {"value": "all", "label": "All Available"},
]


@app.route("/")
def index():
    """Main page with the news digest."""
    return render_template(
        "index.html",
        digest=digest_cache["data"],
        last_updated=digest_cache["last_updated"],
        is_generating=digest_cache["is_generating"],
        current_timeframe=digest_cache.get("timeframe", "24h"),
        rank_by_relevance=digest_cache.get("rank_by_relevance", True),
        timeframe_options=TIMEFRAME_OPTIONS,
        now=datetime.now(),
    )


@app.route("/api/refresh", methods=["POST"])
def refresh_digest():
    """Trigger digest regeneration."""
    global digest_cache
    
    if digest_cache["is_generating"]:
        return jsonify({"status": "already_generating"})
    
    # Get options from request
    data = request.get_json() or {}
    timeframe = data.get("timeframe", "24h")
    rank_by_relevance = data.get("rank_by_relevance", True)
    
    digest_cache["is_generating"] = True
    
    # Run in background thread
    thread = Thread(target=generate_digest_background, args=(timeframe, rank_by_relevance))
    thread.start()
    
    return jsonify({"status": "generating"})


@app.route("/api/status")
def get_status():
    """Get current digest status."""
    return jsonify({
        "is_generating": digest_cache["is_generating"],
        "has_data": digest_cache["data"] is not None,
        "last_updated": digest_cache["last_updated"].isoformat() if digest_cache["last_updated"] else None,
        "timeframe": digest_cache.get("timeframe", "24h"),
        "rank_by_relevance": digest_cache.get("rank_by_relevance", True),
    })


@app.route("/api/digest")
def get_digest():
    """Get current digest data as JSON."""
    if digest_cache["data"] is None:
        return jsonify({"error": "No digest available"}), 404
    
    return jsonify({
        "data": digest_cache["data"],
        "last_updated": digest_cache["last_updated"].isoformat() if digest_cache["last_updated"] else None,
        "timeframe": digest_cache.get("timeframe", "24h"),
        "rank_by_relevance": digest_cache.get("rank_by_relevance", True),
    })


# Category emoji mapping
CATEGORY_EMOJIS = {
    "finance_business": "💰",
    "ai_technology": "🤖",
    "pop_culture": "🎬",
    "politics": "🏛️",
    "global_events": "🌍",
}


@app.context_processor
def utility_processor():
    """Add utility functions to templates."""
    def get_emoji(cat_id):
        return CATEGORY_EMOJIS.get(cat_id, "📰")
    return dict(get_emoji=get_emoji)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
