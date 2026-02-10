"""Image search tool using Tavily."""

from __future__ import annotations

import os
from typing import Any

import httpx
from langchain_core.tools import tool


TAVILY_ENDPOINT = "https://api.tavily.com/search"


async def search_images(
    query: str, limit: int = 8, safe_search: bool = True
) -> list[dict[str, Any]]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY não configurado")

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_images": True,
        "max_results": min(limit, 20),
        "safe_search": safe_search,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(TAVILY_ENDPOINT, json=payload)
        resp.raise_for_status()
        data = resp.json()

    results: list[dict[str, Any]] = []
    for item in data.get("images", [])[:limit]:
        results.append(
            {
                "title": item.get("title") or item.get("description"),
                "thumbnail_url": item.get("thumbnail_url") or item.get("thumbnail"),
                "image_url": item.get("url") or item.get("image_url"),
                "page_url": item.get("source") or item.get("page_url"),
                "source": "tavily",
            }
        )
    return results


@tool
async def image_search(
    query: str, limit: int = 8, safe_search: bool = True
) -> list[dict[str, Any]]:
    """Busca imagens na web (Tavily)."""
    return await search_images(query, limit, safe_search)
