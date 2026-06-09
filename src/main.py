"""
This script fetches RSS articles, summarizes them with Gemini, and writes
static digest data for the web app to serve instantly.
"""
import html
import json
import os
import re
import time
from pathlib import Path

import feedparser
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

CLIENT = genai.Client(api_key=API_KEY)

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "sources.json"
OUTPUT_FILE = PROJECT_ROOT / "static" / "digest_cache.json"

MODEL_NAME = "models/gemini-flash-latest"
MAX_ARTICLES = 4
MAX_SNIPPET_CHARS = 300
REQUESTS_PER_MINUTE = 5
MIN_INTERVAL_SECONDS = 60 / REQUESTS_PER_MINUTE
LAST_CALL_TS = 0.0


def throttle_requests() -> None:
    """Simple per-process rate limiter for free-tier quotas."""
    global LAST_CALL_TS
    now = time.monotonic()
    elapsed = now - LAST_CALL_TS
    if elapsed < MIN_INTERVAL_SECONDS:
        time.sleep(MIN_INTERVAL_SECONDS - elapsed)
    LAST_CALL_TS = time.monotonic()


def get_articles_from_feed(feed_url: str, source_name: str, limit: int = MAX_ARTICLES) -> list:
    """Fetch and parse articles from an RSS feed."""
    try:
        feed = feedparser.parse(feed_url)
        entries = feed.entries or []
        for entry in entries:
            entry["_source_name"] = source_name
        sorted_entries = sorted(
            entries,
            key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or 0,
            reverse=True,
        )
        return sorted_entries[:limit]
    except Exception as exc:
        print(f"Error fetching feed {feed_url}: {exc}")
        return []


def build_prompt(category_name: str, angle: str, articles: list) -> str:
    """Build a concise prompt for Gemini."""
    lines = []
    for article in articles:
        title = article.get("title", "No Title")
        summary = article.get("summary") or article.get("description") or ""
        summary = " ".join(summary.split())[:MAX_SNIPPET_CHARS]
        lines.append(f"- {title}: {summary}")

    content_str = "\n".join(lines)
    return (
        f"Analyze the following recent article headlines and snippets for the \"{category_name}\" category.\n\n"
        f"Your instructions are: {angle}\n\n"
        "Based on these articles, provide exactly 2 concise, high-signal summary bullet points.\n"
        "Do not add any introductory or concluding text.\n\n"
        f"Articles:\n{content_str}"
    )


def generate_summary_with_gemini(category_name: str, articles: list, angle: str) -> str:
    """Generate a concise summary for a list of articles using Gemini."""
    if not articles:
        return "No articles found for this category."

    prompt = build_prompt(category_name, angle, articles)
    try:
        throttle_requests()
        response = CLIENT.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = getattr(response, "text", None)
        if not text:
            return "Summary unavailable."
        return normalize_summary(text)
    except Exception as exc:
        if "RESOURCE_EXHAUSTED" in str(exc):
            print("Rate limit hit; waiting 30 seconds before retrying.")
            time.sleep(30)
            try:
                response = CLIENT.models.generate_content(model=MODEL_NAME, contents=prompt)
                text = getattr(response, "text", None)
                if text:
                    return normalize_summary(text)
                return "Summary unavailable."
            except Exception as retry_exc:
                print(f"Retry failed for {category_name}: {retry_exc}")
        print(f"Error generating summary for {category_name}: {exc}")
        return fallback_summary(category_name, articles)


def normalize_summary(text: str) -> str:
    """Normalize model output for clean inline display."""
    cleaned = html.unescape(text)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = cleaned.replace("\n", " ")
    cleaned = cleaned.replace("•", " ")
    cleaned = cleaned.replace("*", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def fallback_summary(category_name: str, articles: list) -> str:
    """Fallback summary built from article titles when the API fails."""
    titles = [a.get("title", "") for a in articles if a.get("title")]
    if not titles:
        return f"No summary available for {category_name}."
    first = titles[0]
    second = titles[1] if len(titles) > 1 else titles[0]
    return f"Key items: {first}. Also: {second}."


def format_article(article: dict) -> dict:
    """Normalize article data for JSON output."""
    summary = article.get("summary") or article.get("description") or ""
    summary = re.sub(r"<[^>]+>", " ", summary)
    title = html.unescape(article.get("title") or "")
    return {
        "title": title,
        "url": article.get("link"),
        "source": article.get("_source_name") or (article.get("source") or {}).get("title"),
        "published_at": article.get("published"),
        "summary": html.unescape(" ".join(summary.split())[:MAX_SNIPPET_CHARS]),
    }


def main() -> None:
    """Run the news aggregation and summarization pipeline."""
    with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
        config = json.load(handle)

    categories = config.get("categories", {})
    final_digest = {}

    for cat_id, cat_details in categories.items():
        category_name = cat_details.get("name", "Unnamed Category")
        angle = cat_details.get("angle", "Summarize the key events.")
        print(f"Processing category: {category_name}...")

        all_articles = []
        for source in cat_details.get("sources", []):
            url = source.get("url")
            if not url:
                continue
            source_name = source.get("name") or category_name
            all_articles.extend(get_articles_from_feed(url, source_name, limit=MAX_ARTICLES))

        all_articles.sort(
            key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or 0,
            reverse=True,
        )
        top_articles = all_articles[:MAX_ARTICLES]

        summary = generate_summary_with_gemini(category_name, top_articles, angle)
        formatted_articles = [format_article(article) for article in top_articles]

        final_digest[cat_id] = {
            "name": category_name,
            "summary": summary,
            "articles": formatted_articles,
        }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(final_digest, handle, indent=2)

    print(f"Digest saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
