"""Cache management for pre-generated news digests."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Default cache file location
CACHE_DIR = Path(__file__).parent.parent / "output"
CACHE_FILE = CACHE_DIR / "digest_cache.json"


def save_digest_cache(
    data: dict,
    timeframe: str = "7d",
    rank_by_relevance: bool = True,
    cache_path: Optional[Path] = None
) -> Path:
    """Save digest data to cache file.
    
    Args:
        data: The digest data (category_data dict).
        timeframe: The timeframe used to generate this digest.
        rank_by_relevance: Whether relevance ranking was used.
        cache_path: Optional custom cache file path.
        
    Returns:
        Path to the saved cache file.
    """
    cache_path = cache_path or CACHE_FILE
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    cache_data = {
        "data": data,
        "last_updated": datetime.now().isoformat(),
        "timeframe": timeframe,
        "rank_by_relevance": rank_by_relevance,
        "version": "1.0",
    }
    
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, default=str)
    
    return cache_path


def load_digest_cache(
    cache_path: Optional[Path] = None,
    max_age_hours: int = 168  # 7 days by default
) -> Optional[dict]:
    """Load digest from cache file if it exists and is recent enough.
    
    Args:
        cache_path: Optional custom cache file path.
        max_age_hours: Maximum age of cache in hours before considering it stale.
        
    Returns:
        Cache data dict or None if cache doesn't exist or is too old.
    """
    cache_path = cache_path or CACHE_FILE
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        # Check if cache is too old
        last_updated = datetime.fromisoformat(cache_data["last_updated"])
        age = datetime.now() - last_updated
        
        if age > timedelta(hours=max_age_hours):
            print(f"Cache is {age.total_seconds() / 3600:.1f} hours old (max: {max_age_hours}h), considering stale")
            return None
        
        return cache_data
    
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error loading cache: {e}")
        return None


def get_cache_info(cache_path: Optional[Path] = None) -> Optional[dict]:
    """Get metadata about the cache without loading the full data.
    
    Args:
        cache_path: Optional custom cache file path.
        
    Returns:
        Dict with cache info or None if no cache exists.
    """
    cache_path = cache_path or CACHE_FILE
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        last_updated = datetime.fromisoformat(cache_data["last_updated"])
        age = datetime.now() - last_updated
        
        return {
            "last_updated": last_updated,
            "age_hours": age.total_seconds() / 3600,
            "timeframe": cache_data.get("timeframe", "unknown"),
            "rank_by_relevance": cache_data.get("rank_by_relevance", True),
            "has_data": cache_data.get("data") is not None,
        }
    
    except Exception:
        return None
