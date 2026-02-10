"""Ollama-powered summarizer for generating article summaries locally."""

import asyncio
import re
import aiohttp
from typing import Optional

from src.fetchers.base import Article


class OllamaSummarizer:
    """Generates summaries using Ollama (free, local AI)."""
    
    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _generate(self, prompt: str) -> str:
        """Generate text using Ollama API."""
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"Ollama error: {response.status}")
            data = await response.json()
            return data.get("response", "")
    
    async def score_relevance(self, article: Article) -> int:
        """Score an article's relevance/importance from 1-10.
        
        Scoring criteria:
        - Impact: How significant is this news?
        - Timeliness: Is this breaking news or a major development?
        - Audience interest: Would most readers find this important?
        
        Returns:
            Integer score from 1 (low relevance) to 10 (high relevance).
        """
        content = article.content or article.summary or ""
        
        prompt = f"""Rate the importance/relevance of this news article on a scale of 1-10.

Scoring criteria:
- 9-10: Major breaking news, significant global/national impact, affects many people
- 7-8: Important development, notable news, high public interest
- 5-6: Moderately interesting, relevant to specific audiences
- 3-4: Minor news, limited impact or interest
- 1-2: Trivial, clickbait, or low-value content

Title: {article.title}
Source: {article.source}
Content: {content[:500]}

Respond with ONLY a single number from 1 to 10. Nothing else.

Score:"""
        
        try:
            response = await self._generate(prompt)
            # Extract number from response
            match = re.search(r'\b([1-9]|10)\b', response.strip())
            if match:
                return int(match.group(1))
            return 5  # Default middle score
        except Exception as e:
            print(f"Error scoring article '{article.title[:30]}...': {e}")
            return 5  # Default score on error
    
    async def score_articles_batch(self, articles: list[Article]) -> list[tuple[Article, int]]:
        """Score multiple articles concurrently.
        
        Returns:
            List of (article, score) tuples sorted by score descending.
        """
        # Score articles concurrently (in batches to avoid overwhelming)
        batch_size = 5
        scored_articles = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            tasks = [self.score_relevance(article) for article in batch]
            scores = await asyncio.gather(*tasks, return_exceptions=True)
            
            for article, score in zip(batch, scores):
                if isinstance(score, Exception):
                    score = 5
                scored_articles.append((article, score))
        
        # Sort by score (highest first)
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return scored_articles
    
    async def summarize_article(self, article: Article) -> str:
        """Generate a concise summary for a single article."""
        content = article.content or article.summary or article.title
        
        prompt = f"""Summarize this news article in 2-3 sentences. Be concise and informative.

Title: {article.title}
Content: {content[:1000]}

Summary:"""
        
        try:
            return await self._generate(prompt)
        except Exception as e:
            print(f"Error summarizing article: {e}")
            return article.summary or content[:200] + "..."
    
    async def summarize_category(
        self,
        category_name: str,
        articles: list[Article]
    ) -> str:
        """Generate a comprehensive summary for a category."""
        if not articles:
            return f"No articles available for {category_name} today."
        
        article_texts = []
        for i, article in enumerate(articles[:10], 1):
            content = article.content or article.summary or ""
            article_texts.append(f"{i}. {article.title}\n{content[:300]}")
        
        articles_context = "\n\n".join(article_texts)
        
        prompt = f"""Write a 2-3 paragraph summary of today's {category_name} news based on these articles:

{articles_context}

Summary:"""
        
        try:
            return await self._generate(prompt)
        except Exception as e:
            print(f"Error summarizing category: {e}")
            titles = [f"• {a.title}" for a in articles[:5]]
            return f"Top stories in {category_name}:\n" + "\n".join(titles)
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
