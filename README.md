# 📰 Daily News Aggregator

A Python-based news aggregation application that automatically pulls articles from multiple sources and generates concise, AI-powered summaries organized by category.

## ✨ Features

- **Multi-source fetching**: Pulls articles from RSS feeds and news APIs
- **AI-powered summaries**: Uses OpenAI to generate concise, informative summaries
- **Category organization**: News organized into 5 categories:
  - 💰 Finance/Business
  - 🤖 AI & Technology
  - 🎬 Pop Culture
  - 🏛️ Politics
  - 🌍 Global Events
- **Multiple output formats**: Generates both Markdown and HTML digests
- **Scheduled execution**: Run automatically on a daily schedule
- **Async architecture**: Fast, concurrent fetching using `aiohttp`

## 📁 Project Structure

```
NewsApp/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main application entry point
│   ├── scheduler.py         # Scheduled task runner
│   ├── fetchers/            # News source fetchers
│   │   ├── base.py          # Base fetcher class & Article dataclass
│   │   ├── rss_fetcher.py   # RSS feed fetcher
│   │   └── news_api_fetcher.py  # NewsAPI.org fetcher
│   ├── summarizers/         # AI-powered summarization
│   │   └── openai_summarizer.py
│   └── formatters/          # Output formatters
│       ├── markdown_formatter.py
│       └── html_formatter.py
├── config/
│   └── sources.json         # News source configuration
├── output/                  # Generated digests
├── tests/                   # Unit tests
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- OpenAI API key

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   cd NewsApp
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   NEWS_API_KEY=your_newsapi_key_here  # Optional
   ```

## 📖 Usage

### Generate a Daily Digest

Run the main application to generate a digest:

```bash
python -m src.main
```

This will:
1. Fetch articles from all configured sources
2. Generate AI-powered summaries for each category
3. Save the digest as both Markdown and HTML in the `output/` directory

### Run with Scheduler

To run the aggregator on a daily schedule:

```bash
python -m src.scheduler
```

The default schedule time is 8:00 AM. Configure this in your `.env` file:
```
DIGEST_TIME=08:00
```

### Run Tests

```bash
pip install pytest pytest-asyncio
pytest
```

## ⚙️ Configuration

### News Sources

Edit `config/sources.json` to add or modify news sources:

```json
{
  "categories": {
    "finance_business": {
      "name": "Finance/Business",
      "sources": [
        {
          "name": "Reuters Business",
          "type": "rss",
          "url": "https://feeds.reuters.com/reuters/businessNews"
        }
      ]
    }
  },
  "settings": {
    "max_articles_per_source": 5,
    "max_articles_per_category": 10,
    "fetch_timeout_seconds": 30
  }
}
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for summary generation | Yes |
| `NEWS_API_KEY` | NewsAPI.org API key for additional sources | No |
| `OUTPUT_DIR` | Directory for generated digests | No (default: `output`) |
| `DIGEST_TIME` | Time to run daily digest (24h format) | No (default: `08:00`) |

## 📝 Output Examples

### Markdown Output

Generated digests are saved as `output/digest_YYYY-MM-DD.md` with:
- Table of contents with category links
- Category summaries
- Top 5 articles per category with links and summaries

### HTML Output

HTML digests are saved as `output/digest_YYYY-MM-DD.html` with:
- Responsive design for desktop and mobile
- Clean, modern styling
- Interactive navigation

## 🛠️ Development

### Adding a New News Source

1. Add the source to `config/sources.json` under the appropriate category
2. For RSS feeds, use `"type": "rss"`
3. For custom APIs, create a new fetcher class extending `BaseFetcher`

### Adding a New Category

1. Add the category to `config/sources.json`
2. Add an emoji mapping in `MarkdownFormatter._get_category_emoji()`
3. Add sources for the new category

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
