"""Groq-powered summarizer for generating article summaries (free cloud AI)."""

import asyncio
import os
import re
from typing import Optional

import aiohttp

from src.fetchers.base import Article


class GroqSummarizer:
    """Generates summaries using Groq API (free tier available, very fast)."""
    
    def __init__(
        self,
        model: str = "llama-3.1-8b-instant",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _generate(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate text using Groq API."""
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            }
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Groq API error {response.status}: {error_text}")
            data = await response.json()
            return data["choices"][0]["message"]["content"]
    
    async def score_relevance(self, article: Article) -> int:
        """Score an article's relevance/importance from 1-10."""
        content = article.content or article.summary or ""
        
        prompt = f"""Rate the importance/relevance of this news article on a scale of 1-10.

Scoring criteria:
- 9-10: Major breaking news, significant global/national impact
- 7-8: Important development, notable news, high public interest
- 5-6: Moderately interesting, relevant to specific audiences
- 3-4: Minor news, limited impact
- 1-2: Trivial or low-value content

Title: {article.title}
Source: {article.source}
Content: {content[:500]}

Respond with ONLY a single number from 1 to 10."""
        
        try:
            response = await self._generate(prompt, max_tokens=10)
            match = re.search(r'\b([1-9]|10)\b', response.strip())
            if match:
                return int(match.group(1))
            return 5
        except Exception as e:
            print(f"Error scoring article '{article.title[:30]}...': {e}")
            return 5
    
    async def score_articles_batch(self, articles: list[Article]) -> list[tuple[Article, int]]:
        """Score multiple articles concurrently."""
        batch_size = 10  # Groq is fast, can handle larger batches
        scored_articles = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            tasks = [self.score_relevance(article) for article in batch]
            scores = await asyncio.gather(*tasks, return_exceptions=True)
            
            for article, score in zip(batch, scores):
                if isinstance(score, Exception):
                    score = 5
                article.relevance_score = score
                scored_articles.append((article, score))
        
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return scored_articles
    
    async def summarize_article(self, article: Article) -> str:
        """Generate a summary for a single article."""
        content = article.content or article.summary or ""
        
        prompt = f"""Summarize this news article in 2-3 concise sentences.

Title: {article.title}
Source: {article.source}
Content: {content[:1500]}

Summary:"""
        
        try:
            return await self._generate(prompt, max_tokens=150)
        except Exception as e:
            print(f"Error summarizing article: {e}")
            return ""
    
    async def summarize_category(
        self,
        category_name: str,
        articles: list[Article],
        max_articles: int = 5,
    ) -> str:
        """Generate a summary for a category of articles."""
        if not articles:
            return "No articles available for this category."
        
        # Build article list for prompt
        article_texts = []
        for i, article in enumerate(articles[:max_articles], 1):
            content = article.content or article.summary or ""
            article_texts.append(
                f"{i}. {article.title}\n   Source: {article.source}\n   {content[:300]}"
            )
        
        articles_str = "\n\n".join(article_texts)
        
        prompt = f"""You are a news editor. Write a brief 3-4 sentence overview summarizing the key themes and developments in {category_name} based on these articles:

{articles_str}

Write an engaging summary that captures the most important trends and news. Be concise and informative.

Summary:"""
        
        try:
            return await self._generate(prompt, max_tokens=200)
        except Exception as e:
            print(f"Error generating category summary: {e}")
            return "Unable to generate summary."
