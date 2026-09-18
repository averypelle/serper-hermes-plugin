"""Serper web-search plugin for Hermes Agent.

Registers a search-only WebSearchProvider backed by https://google.serper.dev.
Set ``SERPER_API_KEY`` and select the provider via::

    web:
      search_backend: "serper"
      extract_backend: "firecrawl"   # Serper is search-only; pair with an extract provider
"""
from __future__ import annotations

from .provider import SerperWebSearchProvider


def register(ctx) -> None:
    """Plugin entry point — called once at load time by Hermes."""
    ctx.register_web_search_provider(SerperWebSearchProvider())
