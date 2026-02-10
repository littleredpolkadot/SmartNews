"""Tests for the RSS fetcher."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.fetchers.rss_fetcher import RSSFetcher
from src.fetchers.base import Article


@pytest.fixture
def rss_fetcher():
    """Create a test RSS fetcher."""
    return RSSFetcher(
        source_name="Test Source",
        category="Test Category",
        feed_url="https://example.com/feed.rss",
        max_articles=5,
        timeout=10,
    )


@pytest.mark.asyncio
async def test_rss_fetcher_creates_articles(rss_fetcher):
    """Test that RSS fetcher creates Article objects."""
    mock_feed_content = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Test Article</title>
                <link>https://example.com/article</link>
                <description>Test description</description>
                <pubDate>Wed, 25 Dec 2024 10:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_feed_content)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        articles = await rss_fetcher.fetch()
        
        assert len(articles) == 1
        assert isinstance(articles[0], Article)
        assert articles[0].title == "Test Article"
        assert articles[0].source == "Test Source"


@pytest.mark.asyncio
async def test_rss_fetcher_handles_errors(rss_fetcher):
    """Test that RSS fetcher handles HTTP errors gracefully."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        articles = await rss_fetcher.fetch()
        
        assert articles == []


def test_article_to_dict():
    """Test Article.to_dict() method."""
    article = Article(
        title="Test Article",
        url="https://example.com",
        source="Test Source",
        category="Test Category",
        published_at=datetime(2024, 12, 25, 10, 0, 0),
        summary="Test summary",
    )
    
    result = article.to_dict()
    
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"
    assert result["published_at"] == "2024-12-25T10:00:00"
