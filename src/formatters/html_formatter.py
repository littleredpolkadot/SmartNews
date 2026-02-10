"""HTML formatter for generating digest output using Jinja2 templates."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.fetchers.base import Article


# Default HTML template
DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily News Digest - {{ date.strftime('%B %d, %Y') }}</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-color: #1e293b;
            --border-color: #e2e8f0;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 2rem;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        h1 {
            font-size: 2.5rem;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .date {
            font-size: 1.2rem;
            color: var(--secondary-color);
        }
        
        .toc {
            background: var(--card-background);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .toc h2 {
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        .toc ul {
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .toc a {
            color: var(--primary-color);
            text-decoration: none;
            padding: 0.5rem 1rem;
            background: var(--background-color);
            border-radius: 4px;
            transition: background 0.2s;
        }
        
        .toc a:hover {
            background: var(--primary-color);
            color: white;
        }
        
        .category {
            background: var(--card-background);
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .category-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .category-header h2 {
            font-size: 1.5rem;
        }
        
        .emoji {
            font-size: 1.5rem;
        }
        
        .summary {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--background-color);
            border-radius: 4px;
            border-left: 4px solid var(--primary-color);
        }
        
        .articles {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .article {
            padding: 1rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            transition: border-color 0.2s;
        }
        
        .article:hover {
            border-color: var(--primary-color);
        }
        
        .article h3 {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        .article h3 a {
            color: var(--text-color);
            text-decoration: none;
        }
        
        .article h3 a:hover {
            color: var(--primary-color);
        }
        
        .article-meta {
            font-size: 0.875rem;
            color: var(--secondary-color);
            margin-bottom: 0.5rem;
        }
        
        .article-summary {
            font-size: 0.95rem;
            color: var(--secondary-color);
        }
        
        footer {
            text-align: center;
            padding-top: 2rem;
            color: var(--secondary-color);
            font-size: 0.875rem;
        }
        
        @media (max-width: 600px) {
            body {
                padding: 1rem;
            }
            
            h1 {
                font-size: 1.75rem;
            }
            
            .category {
                padding: 1.25rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📰 Daily News Digest</h1>
            <p class="date">{{ date.strftime('%A, %B %d, %Y') }}</p>
        </header>
        
        <nav class="toc">
            <h2>📑 Jump to Section</h2>
            <ul>
                {% for cat_id, cat_data in categories.items() %}
                <li><a href="#{{ cat_id }}">{{ cat_data.emoji }} {{ cat_data.name }}</a></li>
                {% endfor %}
            </ul>
        </nav>
        
        {% for cat_id, cat_data in categories.items() %}
        <section class="category" id="{{ cat_id }}">
            <div class="category-header">
                <span class="emoji">{{ cat_data.emoji }}</span>
                <h2>{{ cat_data.name }}</h2>
            </div>
            
            {% if cat_data.summary %}
            <div class="summary">
                <p>{{ cat_data.summary }}</p>
            </div>
            {% endif %}
            
            {% if cat_data.articles %}
            <div class="articles">
                {% for article in cat_data.articles[:5] %}
                <article class="article">
                    <h3><a href="{{ article.url }}" target="_blank">{{ article.title }}</a></h3>
                    <p class="article-meta">
                        {{ article.source }}
                        {% if article.published_at %}
                        • {{ article.published_at.strftime('%B %d, %Y') }}
                        {% endif %}
                    </p>
                    {% if article.summary %}
                    <p class="article-summary">{{ article.summary }}</p>
                    {% endif %}
                </article>
                {% endfor %}
            </div>
            {% endif %}
        </section>
        {% endfor %}
        
        <footer>
            <p>Generated on {{ date.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        </footer>
    </div>
</body>
</html>
"""


class HTMLFormatter:
    """Formats the daily digest as HTML using Jinja2 templates."""
    
    def __init__(
        self,
        output_dir: str = "output",
        template_dir: Optional[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if template_dir and Path(template_dir).exists():
            self.env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(["html", "xml"])
            )
        else:
            self.env = None
    
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
    
    def format_digest(
        self,
        categories: dict[str, dict],
        date: Optional[datetime] = None
    ) -> str:
        """Format the complete daily digest as HTML.
        
        Args:
            categories: Dictionary with category data containing 'name', 'summary', and 'articles'.
            date: Date for the digest (defaults to today).
            
        Returns:
            Formatted HTML string.
        """
        if date is None:
            date = datetime.now()
        
        # Add emoji to each category
        for cat_id, cat_data in categories.items():
            cat_data["emoji"] = self._get_category_emoji(cat_id)
        
        # Use custom template if available
        if self.env and "digest.html" in self.env.list_templates():
            template = self.env.get_template("digest.html")
        else:
            from jinja2 import Template
            template = Template(DEFAULT_TEMPLATE)
        
        return template.render(
            categories=categories,
            date=date,
        )
    
    def save(
        self,
        content: str,
        filename: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> Path:
        """Save the digest to a file.
        
        Args:
            content: HTML content to save.
            filename: Optional custom filename.
            date: Date for default filename.
            
        Returns:
            Path to the saved file.
        """
        if date is None:
            date = datetime.now()
        
        if filename is None:
            filename = f"digest_{date.strftime('%Y-%m-%d')}.html"
        
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        
        return filepath
