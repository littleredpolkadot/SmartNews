"""Main application module for the news aggregation application."""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from dotenv import load_dotenv

from src.fetchers import RSSFetcher
from src.fetchers.base import Article
from src.summarizers import OpenAISummarizer
from src.summarizers.ollama_summarizer import OllamaSummarizer
from src.summarizers.groq_summarizer import GroqSummarizer
from src.formatters import MarkdownFormatter, HTMLFormatter


class TimeFrame(Enum):
    """Time frame options for filtering articles."""
    HOURS_24 = "24h"
    DAYS_3 = "3d"
    WEEK = "7d"
    ALL = "all"
    
    @property
    def delta(self) -> timedelta | None:
        """Get the timedelta for this timeframe."""
        mapping = {
            "24h": timedelta(hours=24),
            "3d": timedelta(days=3),
            "7d": timedelta(days=7),
            "all": None,
        }
        return mapping.get(self.value)
    
    @property
    def label(self) -> str:
        """Human-readable label."""
        mapping = {
            "24h": "Past 24 Hours",
            "3d": "Past 3 Days",
            "7d": "Past Week",
            "all": "All Time",
        }
        return mapping.get(self.value, "All Time")


class NewsAggregator:
    """Main class for aggregating news from multiple sources."""
    
    def __init__(self, config_path: str = "config/sources.json", use_ollama: bool = False):
        load_dotenv()
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Priority: Groq (free cloud) > OpenAI (paid) > Ollama (local)
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if groq_key and groq_key != "your_groq_api_key_here":
            print("⚡ Using Groq (free cloud AI) for summaries")
            self.summarizer = GroqSummarizer()
        elif openai_key and openai_key != "your_openai_api_key_here":
            print("☁️ Using OpenAI for summaries")
            self.summarizer = OpenAISummarizer()
        else:
            print("📦 Using Ollama (local, free) for summaries")
            self.summarizer = OllamaSummarizer()
        
        self.markdown_formatter = MarkdownFormatter()
        self.html_formatter = HTMLFormatter()
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    async def fetch_category(
        self,
        category_id: str,
        category_config: dict,
        timeframe: TimeFrame = TimeFrame.ALL,
    ) -> list[Article]:
        """Fetch articles for a single category.
        
        Args:
            category_id: Unique identifier for the category.
            category_config: Configuration for the category including sources.
            timeframe: Filter articles to this time window.
            
        Returns:
            List of articles for the category.
        """
        articles = []
        fetchers = []
        
        settings = self.config.get("settings", {})
        max_per_source = settings.get("max_articles_per_source", 10)  # Fetch more initially
        timeout = settings.get("fetch_timeout_seconds", 30)
        
        # Create fetchers for each source
        for source in category_config.get("sources", []):
            if source.get("type") == "rss":
                fetcher = RSSFetcher(
                    source_name=source["name"],
                    category=category_config["name"],
                    feed_url=source["url"],
                    max_articles=max_per_source,
                    timeout=timeout,
                )
                fetchers.append(fetcher)
        
        # Fetch from all sources concurrently
        try:
            tasks = [fetcher.fetch() for fetcher in fetchers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    articles.extend(result)
                elif isinstance(result, Exception):
                    print(f"Error fetching: {result}")
        
        finally:
            # Clean up fetchers
            for fetcher in fetchers:
                await fetcher.close()
        
        # Filter by timeframe
        if timeframe.delta is not None:
            from datetime import timezone
            cutoff = datetime.now(timezone.utc) - timeframe.delta
            filtered = []
            for a in articles:
                if a.published_at:
                    # Make datetime timezone-aware if it isn't
                    pub_date = a.published_at
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    if pub_date >= cutoff:
                        filtered.append(a)
            articles = filtered
        
        # Sort by publication date (newest first) as initial ordering
        articles.sort(
            key=lambda a: a.published_at.replace(tzinfo=None) if a.published_at else datetime.min,
            reverse=True
        )
        
        # Limit articles per category
        max_per_category = settings.get("max_articles_per_category", 20)
        return articles[:max_per_category]
    
    async def fetch_all(
        self,
        timeframe: TimeFrame = TimeFrame.ALL,
        rank_by_relevance: bool = False,
    ) -> dict[str, list[Article]]:
        """Fetch articles from all categories.
        
        Args:
            timeframe: Filter articles to this time window.
            rank_by_relevance: If True, use AI to rank by importance instead of date.
        
        Returns:
            Dictionary mapping category IDs to lists of articles.
        """
        categories = self.config.get("categories", {})
        results = {}
        
        for category_id, category_config in categories.items():
            print(f"Fetching {category_config['name']}...")
            articles = await self.fetch_category(category_id, category_config, timeframe)
            print(f"  Found {len(articles)} articles")
            
            # Optionally rank by relevance using AI
            if rank_by_relevance and articles and hasattr(self.summarizer, 'score_articles_batch'):
                print(f"  🎯 Scoring relevance...")
                scored = await self.summarizer.score_articles_batch(articles)
                articles = [article for article, score in scored]
                # Store scores for display
                for i, (article, score) in enumerate(scored):
                    article.relevance_score = score
                print(f"  Top scored: {articles[0].title[:50]}... (score: {scored[0][1]})")
            
            results[category_id] = articles
        
        return results
    
    async def generate_summaries(
        self,
        articles_by_category: dict[str, list[Article]]
    ) -> dict[str, dict]:
        """Generate summaries for all categories.
        
        Args:
            articles_by_category: Dictionary mapping category IDs to article lists.
            
        Returns:
            Dictionary with category data including summaries.
        """
        categories = self.config.get("categories", {})
        results = {}
        
        for category_id, articles in articles_by_category.items():
            category_name = categories[category_id]["name"]
            print(f"Summarizing {category_name}...")
            
            # Generate category summary
            summary = await self.summarizer.summarize_category(
                category_name, articles
            )
            
            # Generate individual article summaries
            for article in articles[:5]:
                if not article.summary:
                    article.summary = await self.summarizer.summarize_article(article)
            
            results[category_id] = {
                "name": category_name,
                "summary": summary,
                "articles": articles,
            }
        
        return results
    
    async def generate_digest(
        self,
        output_format: str = "both",
        timeframe: TimeFrame = TimeFrame.ALL,
        rank_by_relevance: bool = True,
    ) -> tuple[Path, Path | None]:
        """Generate the complete daily digest.
        
        Args:
            output_format: Output format - 'markdown', 'html', or 'both'.
            timeframe: Filter articles to this time window.
            rank_by_relevance: If True, rank articles by AI-scored importance.
            
        Returns:
            Tuple of paths to the generated files.
        """
        date = datetime.now()
        
        print("=" * 50)
        print(f"Daily News Digest - {date.strftime('%Y-%m-%d')}")
        print(f"Timeframe: {timeframe.label}")
        print(f"Ranking: {'By Relevance' if rank_by_relevance else 'By Date'}")
        print("=" * 50)
        
        # Fetch articles
        print("\n📥 Fetching articles...")
        articles_by_category = await self.fetch_all(
            timeframe=timeframe,
            rank_by_relevance=rank_by_relevance,
        )
        
        total_articles = sum(len(a) for a in articles_by_category.values())
        print(f"\n✅ Fetched {total_articles} articles total")
        
        # Generate summaries
        print("\n🤖 Generating summaries...")
        category_data = await self.generate_summaries(articles_by_category)
        
        # Format and save outputs
        print("\n📝 Formatting output...")
        
        md_path = None
        html_path = None
        
        if output_format in ("markdown", "both"):
            md_content = self.markdown_formatter.format_digest(category_data, date)
            md_path = self.markdown_formatter.save(md_content, date=date)
            print(f"  Markdown: {md_path}")
        
        if output_format in ("html", "both"):
            html_content = self.html_formatter.format_digest(category_data, date)
            html_path = self.html_formatter.save(html_content, date=date)
            print(f"  HTML: {html_path}")
        
        print("\n✨ Digest generation complete!")
        
        return md_path, html_path


async def main():
    """Main entry point."""
    aggregator = NewsAggregator()
    # Default: rank by relevance, past 24 hours
    await aggregator.generate_digest(
        output_format="both",
        timeframe=TimeFrame.HOURS_24,
        rank_by_relevance=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
