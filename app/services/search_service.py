import os
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

MAX_RESULTS = 5

TRUSTED_MEDICAL_DOMAINS = (
    "ncbi.nlm.nih.gov",
    "medlineplus.gov",
    "mayoclinic.org",
    "nih.gov",
    "fda.gov",
    "nhs.uk",
    "who.int",
    "cdc.gov",
)

TRUSTED_DOMAIN_SCORE = 1.0
DEFAULT_DOMAIN_SCORE = 0.3


def _get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in .env file")
    return TavilyClient(api_key=api_key)


def _extract_hostname(url: str) -> str:
    hostname = urlparse(url).netloc.lower()
    if hostname.startswith("www."):
        return hostname[4:]
    return hostname


def _calculate_reliability_score(url: str) -> float:
    hostname = _extract_hostname(url)

    for domain in TRUSTED_MEDICAL_DOMAINS:
        if hostname == domain or hostname.endswith(f".{domain}"):
            return TRUSTED_DOMAIN_SCORE

    return DEFAULT_DOMAIN_SCORE


def search_medical_info(query: str) -> dict[str, Any]:
    """
    Search Tavily for medical information and return a normalized response.

    Returns a dictionary with:
        - query: the original search query
        - results: list of dicts, each with title, url, content, and reliability_score
        - error (optional): present when the search could not be completed
    """
    if not query or not query.strip():
        return {
            "query": query,
            "results": [],
            "error": "Query cannot be empty",
        }

    try:
        client = _get_tavily_client()
        response = client.search(query.strip(), max_results=MAX_RESULTS)

        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "reliability_score": _calculate_reliability_score(item.get("url", "")),
            }
            for item in response.get("results", [])
        ]

        results.sort(key=lambda item: item["reliability_score"], reverse=True)

        return {
            "query": query.strip(),
            "results": results[:MAX_RESULTS],
        }

    except ValueError as exc:
        return {
            "query": query.strip(),
            "results": [],
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "query": query.strip(),
            "results": [],
            "error": f"Tavily search failed: {exc}",
        }