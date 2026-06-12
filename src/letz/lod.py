"""LOD (Lëtzebuerger Online Dictionnaire) API client.

Provides dictionary lookup, caching, and rate limiting for the official
Luxembourgish dictionary API at https://api.lod.lu/
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

import httpx

# LOD API configuration
LOD_API_BASE = "https://api.lod.lu"
LOD_API_HEADERS = {
    "Accept": "application/json",
    "Referer": "https://lod.lu",
    "User-Agent": "letz/0.1.0 (Luxembourgish language tool)",
}

# Cache directory
CACHE_DIR = Path.home() / ".cache" / "letz"
CACHE_TTL = 86400 * 7  # 7 days


class LODClient:
    """Client for the LOD (Lëtzebuerger Online Dictionnaire) API.

    The LOD is the official multilingual Luxembourgish dictionary, providing
    definitions, translations (Luxembourgish ↔ German, French, Portuguese, English),
    and grammatical information.

    Usage:
        client = LODClient()
        result = client.lookup("Haus")
        result = client.search("Haus")
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = CACHE_TTL,
        timeout: float = 30.0,
    ):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        self._last_request_time: float = 0
        self._min_interval: float = 0.5  # Rate limit: max 2 requests/second

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                headers=LOD_API_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def _rate_limit(self) -> None:
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _get_cache_path(self, endpoint: str, query: str) -> Path:
        """Get the cache file path for a query."""
        safe_query = query.replace("/", "_").replace(" ", "_")
        safe_endpoint = endpoint.replace("/", "_")
        return self.cache_dir / f"{safe_endpoint}_{safe_query}.json"

    def _load_cache(self, endpoint: str, query: str) -> Optional[dict]:
        """Load a cached response if available and not expired."""
        cache_path = self._get_cache_path(endpoint, query)
        if not cache_path.exists():
            return None
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            if time.time() - data.get("cached_at", 0) > self.cache_ttl:
                return None
            return data.get("response")
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_cache(self, endpoint: str, query: str, response: Any) -> None:
        """Save a response to cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._get_cache_path(endpoint, query)
        data = {"cached_at": time.time(), "response": response}
        cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _request(self, endpoint: str, params: dict) -> Any:
        """Make a rate-limited, cached API request."""
        # Check cache first
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
        cached = self._load_cache(endpoint, cache_key)
        if cached is not None:
            return cached

        self._rate_limit()
        client = self._get_client()
        url = f"{LOD_API_BASE}{endpoint}"
        response = client.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        self._save_cache(endpoint, cache_key, result)
        return result

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Search the LOD dictionary for words matching the query.

        Args:
            query: Search term (Luxembourgish, German, French, etc.)
            limit: Maximum number of results

        Returns:
            List of matching dictionary entries
        """
        try:
            result = self._request("/api/v1/search", {"query": query, "limit": limit})
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                # Try common response formats
                return result.get("results", result.get("data", result.get("hits", [])))
            return []
        except httpx.HTTPError as e:
            return [{"error": str(e), "query": query}]

    def lookup(self, word: str) -> Optional[dict]:
        """Look up a specific word in the LOD dictionary.

        Args:
            word: Exact word to look up

        Returns:
            Dictionary entry if found, None otherwise
        """
        results = self.search(word, limit=5)
        if not results:
            return None

        # Try to find exact match
        for entry in results:
            if isinstance(entry, dict):
                entry_word = entry.get("word", entry.get("lemma", entry.get("title", "")))
                if entry_word.lower() == word.lower():
                    return entry

        # Return first result if no exact match
        return results[0] if results else None

    def get_definition(self, word: str) -> Optional[str]:
        """Get the definition of a word.

        Args:
            word: Word to define

        Returns:
            Definition string if found, None otherwise
        """
        entry = self.lookup(word)
        if entry is None:
            return None
        if isinstance(entry, dict):
            return entry.get("definition", entry.get("meaning", str(entry)))
        return str(entry)

    def check_spelling(self, word: str) -> dict:
        """Check if a word exists in the LOD dictionary.

        Args:
            word: Word to check

        Returns:
            Dict with 'found' (bool), 'entry' (optional), and 'suggestions' (list)
        """
        results = self.search(word, limit=10)
        found = False
        entry = None
        suggestions = []

        for r in results:
            if isinstance(r, dict):
                r_word = r.get("word", r.get("lemma", r.get("title", "")))
                if r_word.lower() == word.lower():
                    found = True
                    entry = r
                    break
                suggestions.append(r_word)

        return {
            "word": word,
            "found": found,
            "entry": entry,
            "suggestions": suggestions[:5],
        }

    def clear_cache(self) -> None:
        """Clear the LOD API cache."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()