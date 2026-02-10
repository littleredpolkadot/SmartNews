"""News fetchers package for retrieving articles from various sources."""

from .base import BaseFetcher
from .rss_fetcher import RSSFetcher
from .news_api_fetcher import NewsAPIFetcher

__all__ = ["BaseFetcher", "RSSFetcher", "NewsAPIFetcher"]
