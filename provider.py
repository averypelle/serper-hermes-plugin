"""Serper (google.serper.dev) web search provider.

Search-only. Serper returns Google Search results (organic, plus optional
knowledge graph / answer box / related searches) via a simple POST API. Pair
with Firecrawl/Tavily/Exa/Parallel for ``web_extract``.

Docs: https://serper.dev/playground
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from agent.web_search_provider import WebSearchProvider, get_provider_env

logger = logging.getLogger(__name__)

_SERPER_ENDPOINT = "https://google.serper.dev/search"
_DEFAULT_TIMEOUT = 15
# Serper accepts num up to 100; clamp defensively.
_MAX_LIMIT = 100


class SerperWebSearchProvider(WebSearchProvider):
    """Serper (google.serper.dev) — Google Search as a JSON API. Search only."""

    @property
    def name(self) -> str:
        return "serper"

    @property
    def display_name(self) -> str:
        return "Serper (Google Search)"

    def is_available(self) -> bool:
        # Cheap check, no network. Called on every `hermes tools` paint.
        return bool(get_provider_env("SERPER_API_KEY"))

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return False

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        api_key = get_provider_env("SERPER_API_KEY")
        if not api_key:
            return {"success": False, "error": "SERPER_API_KEY is not set"}

        num = max(1, min(int(limit), _MAX_LIMIT))
        payload = json.dumps({"q": query, "num": num}).encode("utf-8")

        # Optional knobs, all env-configurable so users don't need to fork the plugin.
        gl = os.getenv("SERPER_GL", "").strip()   # country code, e.g. "us"
        hl = os.getenv("SERPER_HL", "").strip()   # UI language, e.g. "en"
        if gl or hl:
            body = {"q": query, "num": num}
            if gl:
                body["gl"] = gl
            if hl:
                body["hl"] = hl
            payload = json.dumps(body).encode("utf-8")

        req = urlrequest.Request(
            _SERPER_ENDPOINT,
            data=payload,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:
                raw = resp.read()
                data = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                pass
            msg = f"Serper HTTP {exc.code}: {exc.reason}"
            if body:
                msg = f"{msg} — {body}"
            logger.warning("Serper search failed: %s", msg)
            return {"success": False, "error": msg}
        except URLError as exc:
            msg = f"Serper network error: {exc.reason}"
            logger.warning("Serper search failed: %s", msg)
            return {"success": False, "error": msg}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Serper returned non-JSON response: %s", exc)
            return {"success": False, "error": f"Serper returned invalid JSON: {exc}"}

        organic: List[Dict[str, Any]] = data.get("organic") or []
        rows: List[Dict[str, Any]] = []
        for idx, item in enumerate(organic[:limit]):
            rows.append(
                {
                    "title": item.get("title", "") or "",
                    "url": item.get("link", "") or "",
                    "description": item.get("snippet", "") or "",
                    "position": item.get("position", idx + 1),
                }
            )

        # Fold in the answer box as the top result when Serper supplies one and
        # it has a link — this is the closest analog to Google's featured snippet
        # and is often the highest-signal answer for factual queries.
        answer_box = data.get("answerBox") or {}
        ab_link = answer_box.get("link") or ""
        if ab_link and not any(r["url"] == ab_link for r in rows):
            desc = (
                answer_box.get("answer")
                or answer_box.get("snippet")
                or answer_box.get("title")
                or ""
            )
            rows.insert(
                0,
                {
                    "title": answer_box.get("title", "") or "Answer",
                    "url": ab_link,
                    "description": desc,
                    "position": 0,
                },
            )
            rows = rows[:limit]

        logger.info(
            "Serper '%s': %d results (from %d organic, limit %d)",
            query,
            len(rows),
            len(organic),
            limit,
        )
        return {"success": True, "data": {"web": rows}}
