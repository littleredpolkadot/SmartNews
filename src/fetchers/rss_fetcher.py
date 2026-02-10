"""RSS feed fetcher for news sources."""

import asyncio
from datetime import datetime
from typing import Optional
from email.utils import parsedate_to_datetime

import aiohttp
import feedparser

from .base import Article, BaseFetcher


class RSSFetcher(BaseFetcher):
    """Fetches news articles from RSS feeds."""
    
    def __init__(
        self,
        source_name: str,
        category: str,
        feed_url: str,
        max_articles: int = 10,
        timeout: int = 30
    ):
        super().__init__(source_name, category)
        self.feed_url = feed_url
        self.max_articles = max_articles
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _parse_date(self, entry: dict) -> Optional[datetime]:
        """Parse publication date from feed entry."""
        date_fields = ["published", "updated", "created"]
        
        for field in date_fields:
            if field in entry:
                try:
                    return parsedate_to_datetime(entry[field])
                except (ValueError, TypeError):
                    continue
        
        # Try parsed time tuple
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            if field in entry and entry[field]:
                try:
                    return datetime(*entry[field][:6])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_content(self, entry: dict) -> Optional[str]:
        """Extract content from feed entry."""
        # Try content field first
        if "content" in entry and entry["content"]:
            return entry["content"][0].get("value", "")
        
        # Fall back to summary
        if "summary" in entry:
            return entry["summary"]
        
        # Try description
        if "description" in entry:
            return entry["description"]
        
        return None
    
    async def fetch(self) -> list[Article]:
        """Fetch articles from the RSS feed.
        
        Returns:
            List of Article objects.
        """
        articles = []
        
        try:
            session = await self._get_session()
            
            async with session.get(self.feed_url) as response:
                if response.status != 200:
                    print(f"Error fetching {self.feed_url}: HTTP {response.status}")
                    return articles
                
                content = await response.text()
            
            # Parse feed in executor to avoid blocking
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, content)
            
            for entry in feed.entries[:self.max_articles]:
                article = Article(
                    title=entry.get("title", "Untitled"),
                    url=entry.get("link", ""),
                    source=self.source_name,
                    category=self.category,
                    published_at=self._parse_date(entry),
                    content=self._extract_content(entry),
                    author=entry.get("author"),
                )
                articles.append(article)
        
        except asyncio.TimeoutError:
            print(f"Timeout fetching {self.feed_url}")
        except aiohttp.ClientError as e:
            print(f"Error fetching {self.feed_url}: {e}")
        except Exception as e:
            print(f"Unexpected error fetching {self.feed_url}: {e}")
        
        return articles
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
