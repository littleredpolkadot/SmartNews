"""OpenAI-powered summarizer for generating article summaries."""

import os
from typing import Optional

from openai import AsyncOpenAI

from src.fetchers.base import Article


class OpenAISummarizer:
    """Generates summaries using OpenAI's API."""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_tokens: int = 500,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.client: Optional[AsyncOpenAI] = None
    
    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = AsyncOpenAI(api_key=api_key)
        return self.client
    
    async def summarize_article(self, article: Article) -> str:
        """Generate a concise summary for a single article.
        
        Args:
            article: The article to summarize.
            
        Returns:
            A concise summary of the article.
        """
        content = article.content or article.summary or article.title
        
        prompt = f"""Summarize the following news article in 2-3 sentences. 
Focus on the key facts and main takeaway. Be concise and informative.

Title: {article.title}
Source: {article.source}
Content: {content}

Summary:"""
        
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled news editor who writes concise, informative summaries."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error summarizing article '{article.title}': {e}")
            return article.summary or content[:200] + "..."
    
    async def summarize_category(
        self,
        category_name: str,
        articles: list[Article]
    ) -> str:
        """Generate a comprehensive summary for a category of articles.
        
        Args:
            category_name: Name of the category.
            articles: List of articles in the category.
            
        Returns:
            A comprehensive summary of the category's news.
        """
        if not articles:
            return f"No articles available for {category_name} today."
        
        # Build article summaries for context
        article_texts = []
        for i, article in enumerate(articles[:10], 1):
            content = article.content or article.summary or ""
            article_texts.append(
                f"{i}. {article.title} ({article.source})\n{content[:500]}"
            )
        
        articles_context = "\n\n".join(article_texts)
        
        prompt = f"""You are creating a daily news digest for the {category_name} category.
Based on the following articles, write a cohesive summary (3-5 paragraphs) that:
1. Highlights the most important developments
2. Identifies key trends or themes
3. Provides context where helpful
4. Uses clear, professional language

Articles:
{articles_context}

Write the category summary:"""
        
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced news editor creating a daily digest. Write engaging, informative summaries that help readers quickly understand the day's key developments."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.4,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error summarizing category '{category_name}': {e}")
            # Fallback to individual article titles
            titles = [f"• {a.title}" for a in articles[:5]]
            return f"Top stories in {category_name}:\n" + "\n".join(titles)
