# News Aggregation Application

## Project Overview
This is a Python-based daily news aggregation application that automatically pulls articles from multiple sources and generates concise, AI-powered summaries organized by category.

## Categories
- Finance/Business
- AI & Technology
- Pop Culture
- Politics
- Global Events

## Project Structure
- `src/` - Main application source code
- `src/fetchers/` - News source fetchers (RSS, APIs)
- `src/summarizers/` - AI-powered summary generation
- `src/formatters/` - Output formatters (Markdown, HTML)
- `config/` - Configuration files for news sources
- `output/` - Generated daily digests
- `tests/` - Unit tests

## Development Guidelines
- Use Python 3.11+
- Follow PEP 8 style guidelines
- Use async/await for concurrent news fetching
- Store API keys in environment variables
- Use type hints throughout the codebase

## Key Dependencies
- aiohttp - Async HTTP client
- feedparser - RSS feed parsing
- openai - AI summary generation
- python-dotenv - Environment variable management
- jinja2 - Template rendering for output
- schedule - Task scheduling

## Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the daily digest
python -m src.main
```
