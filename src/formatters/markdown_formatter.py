"""Markdown formatter for generating digest output."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from src.fetchers.base import Article


class MarkdownFormatter:
    """Formats the daily digest as Markdown."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def format_digest(
        self,
        categories: dict[str, dict],
        date: Optional[datetime] = None
    ) -> str:
        """Format the complete daily digest as Markdown.
        
        Args:
            categories: Dictionary with category data containing 'name', 'summary', and 'articles'.
            date: Date for the digest (defaults to today).
            
        Returns:
            Formatted Markdown string.
        """
        if date is None:
            date = datetime.now()
        
        lines = [
            f"# Daily News Digest",
            f"### {date.strftime('%A, %B %d, %Y')}",
            "",
            "---",
            "",
        ]
        
        # Table of contents
        lines.append("## 📑 Contents\n")
        for cat_id, cat_data in categories.items():
            anchor = cat_data["name"].lower().replace(" ", "-").replace("/", "").replace("&", "and")
            lines.append(f"- [{cat_data['name']}](#{anchor})")
        lines.append("\n---\n")
        
        # Category sections
        for cat_id, cat_data in categories.items():
            emoji = self._get_category_emoji(cat_id)
            lines.append(f"## {emoji} {cat_data['name']}\n")
            
            # Category summary
            if cat_data.get("summary"):
                lines.append(cat_data["summary"])
                lines.append("")
            
            # Individual articles
            if cat_data.get("articles"):
                lines.append("### Top Stories\n")
                for article in cat_data["articles"][:5]:
                    lines.append(self._format_article(article))
            
            lines.append("\n---\n")
        
        # Footer
        lines.append(f"*Generated on {date.strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    def _format_article(self, article: Article) -> str:
        """Format a single article as Markdown."""
        lines = [f"#### [{article.title}]({article.url})"]
        lines.append(f"*{article.source}*")
        
        if article.published_at:
            lines.append(f" | {article.published_at.strftime('%B %d, %Y')}")
        
        lines.append("")
        
        if article.summary:
            lines.append(f"> {article.summary}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_category_emoji(self, category_id: str) -> str:
        """Get an emoji for the category."""
        emoji_map = {
            "finance_business": "💰",
            "ai_technology": "🤖",
            "pop_culture": "🎬",
            "politics": "🏛️",
            "global_events": "🌍",
        }
        return emoji_map.get(category_id, "📰")
    
    def save(
        self,
        content: str,
        filename: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> Path:
        """Save the digest to a file.
        
        Args:
            content: Markdown content to save.
            filename: Optional custom filename.
            date: Date for default filename.
            
        Returns:
            Path to the saved file.
        """
        if date is None:
            date = datetime.now()
        
        if filename is None:
            filename = f"digest_{date.strftime('%Y-%m-%d')}.md"
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        
        return filepath
