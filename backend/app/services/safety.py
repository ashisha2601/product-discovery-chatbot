import httpx
from typing import Optional

from app.core.config import get_settings


settings = get_settings()


def search_duckduckgo_side_effects(query: str) -> Optional[str]:
    """
    Call DuckDuckGo via SearchApi.io and return a short text snippet that can
    be used as safety / side‑effect context for the LLM.

    This uses the `SEARCHAPI_API_KEY` and base URL configured in `.env`.
    """
    if not settings.searchapi_api_key:
        return None

    params = {
        "engine": "duckduckgo",
        "q": query,
    }
    headers = {"Authorization": f"Bearer {settings.searchapi_api_key}"}

    try:
        resp = httpx.get(
            settings.searchapi_base_url,
            params=params,
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

        # Prefer AI overview if present
        ai_overview = data.get("ai_overview")
        if isinstance(ai_overview, dict) and ai_overview.get("answer"):
            return ai_overview["answer"]

        # Fallback to first few organic snippets
        organic = data.get("organic_results") or []
        snippets: list[str] = []
        for item in organic[:3]:
            snippet = item.get("snippet")
            if snippet:
                snippets.append(snippet)

        if snippets:
            return "\n".join(snippets)

    except Exception:
        # In case of any network / parsing error, just return None so the
        # chatbot can fall back to its normal behaviour.
        return None

    return None


