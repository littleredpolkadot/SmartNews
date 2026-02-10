"""Summarizers package for generating AI-powered summaries."""

from .openai_summarizer import OpenAISummarizer
from .ollama_summarizer import OllamaSummarizer

__all__ = ["OpenAISummarizer", "OllamaSummarizer"]
