"""News API fetcher for additional news sources."""

import os
from datetime import datetime
from typing import Optional

import aiohttp

from .base import Article, BaseFetcher


class NewsAPIFetcher(BaseFetcher):
    """Fetches news articles from NewsAPI.org."""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(
        self,
        source_name: str,
        category: str,
        query: Optional[str] = None,
        country: str = "us",
        max_articles: int = 10,
        timeout: int = 30
    ):
        super().__init__(source_name, category)
        self.query = query
        self.country = country
        self.max_articles = max_articles
        self.timeout = timeout
        self.api_key = os.getenv("NEWS_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO format date string."""
        if not date_str:
            return None
        
        try:
            # Handle ISO format with Z suffix
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None
    
    async def fetch(self) -> list[Article]:
        """Fetch articles from NewsAPI.
        
        Returns:
            List of Article objects.
        """
        articles = []
        
        if not self.api_key:
            print("NEWS_API_KEY not set, skipping NewsAPI fetch")
            return articles
        
        try:
            session = await self._get_session()
            
            # Build request URL
            if self.query:
                url = f"{self.BASE_URL}/everything"
                params = {
                    "q": self.query,
                    "pageSize": self.max_articles,
                    "apiKey": self.api_key,
                    "sortBy": "publishedAt",
                }
            else:
                url = f"{self.BASE_URL}/top-headlines"
                params = {
                    "country": self.country,
                    "pageSize": self.max_articles,
                    "apiKey": self.api_key,
                }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    print(f"NewsAPI error: {error_data.get('message', 'Unknown error')}")
                    return articles
                
                data = await response.json()
            
            for item in data.get("articles", []):
                article = Article(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", self.source_name),
                    category=self.category,
                    published_at=self._parse_date(item.get("publishedAt")),
                    content=item.get("content"),
                    summary=item.get("description"),
                    author=item.get("author"),
                )
                articles.append(article)
        
        except aiohttp.ClientError as e:
            print(f"Error fetching from NewsAPI: {e}")
        except Exception as e:
            print(f"Unexpected error fetching from NewsAPI: {e}")
        
        return articles
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
