from flask import current_app


def search_medical_research(diagnosis: str, max_results: int = 3) -> dict:
    diagnosis = (diagnosis or "").strip()
    if not diagnosis:
        return {
            "available": False,
            "message": "Enter a diagnosis before searching.",
            "results": [],
        }

    api_key = current_app.config.get("TAVILY_API_KEY", "")
    if not api_key:
        return {
            "available": False,
            "message": "Tavily API key is not configured in .env.",
            "results": [],
        }

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=f"{diagnosis} clinical guidelines medical research",
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
        )
    except Exception as exc:
        return {
            "available": False,
            "message": f"Medical research lookup failed: {exc}",
            "results": [],
        }

    results = []
    for item in response.get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
        )

    return {
        "available": True,
        "message": response.get("answer") or "Recent medical articles and guidelines.",
        "results": results,
    }
