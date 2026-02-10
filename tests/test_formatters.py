"""Tests for the formatters."""

import pytest
from datetime import datetime

from src.formatters.markdown_formatter import MarkdownFormatter
from src.formatters.html_formatter import HTMLFormatter
from src.fetchers.base import Article


@pytest.fixture
def sample_categories():
    """Create sample category data for testing."""
    return {
        "finance_business": {
            "name": "Finance/Business",
            "summary": "Markets showed strong gains today.",
            "articles": [
                Article(
                    title="Stock Market Hits Record High",
                    url="https://example.com/stocks",
                    source="Test Finance",
                    category="Finance/Business",
                    published_at=datetime(2024, 12, 25, 10, 0, 0),
                    summary="The stock market reached all-time highs today.",
                ),
            ],
        },
        "ai_technology": {
            "name": "AI & Technology",
            "summary": "New AI developments announced.",
            "articles": [
                Article(
                    title="New AI Model Released",
                    url="https://example.com/ai",
                    source="Tech News",
                    category="AI & Technology",
                    published_at=datetime(2024, 12, 25, 9, 0, 0),
                    summary="A new state-of-the-art AI model was released.",
                ),
            ],
        },
    }


def test_markdown_formatter_contains_categories(sample_categories):
    """Test that markdown output contains all categories."""
    formatter = MarkdownFormatter()
    date = datetime(2024, 12, 25)
    
    result = formatter.format_digest(sample_categories, date)
    
    assert "Finance/Business" in result
    assert "AI & Technology" in result
    assert "Daily News Digest" in result


def test_markdown_formatter_contains_articles(sample_categories):
    """Test that markdown output contains article information."""
    formatter = MarkdownFormatter()
    date = datetime(2024, 12, 25)
    
    result = formatter.format_digest(sample_categories, date)
    
    assert "Stock Market Hits Record High" in result
    assert "New AI Model Released" in result


def test_html_formatter_produces_valid_html(sample_categories):
    """Test that HTML formatter produces valid HTML structure."""
    formatter = HTMLFormatter()
    date = datetime(2024, 12, 25)
    
    result = formatter.format_digest(sample_categories, date)
    
    assert "<!DOCTYPE html>" in result
    assert "<html" in result
    assert "</html>" in result
    assert "Finance/Business" in result
    assert "AI & Technology" in result


def test_html_formatter_contains_articles(sample_categories):
    """Test that HTML output contains article information."""
    formatter = HTMLFormatter()
    date = datetime(2024, 12, 25)
    
    result = formatter.format_digest(sample_categories, date)
    
    assert "Stock Market Hits Record High" in result
    assert "https://example.com/stocks" in result
