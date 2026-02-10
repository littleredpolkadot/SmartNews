"""Base fetcher class defining the interface for all news fetchers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """Represents a news article."""
    
    title: str
    url: str
    source: str
    category: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "content": self.content,
            "author": self.author,
        }


class BaseFetcher(ABC):
    """Abstract base class for news fetchers."""
    
    def __init__(self, source_name: str, category: str):
        self.source_name = source_name
        self.category = category
    
    @abstractmethod
    async def fetch(self) -> list[Article]:
        """Fetch articles from the source.
        
        Returns:
            List of Article objects.
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass
