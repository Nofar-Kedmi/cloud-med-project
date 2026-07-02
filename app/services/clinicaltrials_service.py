"""ClinicalTrials.gov API v2 client."""

from __future__ import annotations

import requests

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
TIMEOUT_SECONDS = 15


def search_clinical_trials(
    query: str,
    *,
    page_size: int = 10,
    search_type: str = "condition",
) -> dict:
    """
    Search clinical trials by condition/symptom or general term.

    search_type: 'condition' | 'term'
    """
    query = (query or "").strip()
    if not query:
        return {"query": query, "studies": [], "error": "Query cannot be empty."}

    params: dict = {"pageSize": page_size, "format": "json"}
    if search_type == "condition":
        params["query.cond"] = query
    else:
        params["query.term"] = query

    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return {"query": query, "studies": [], "error": str(exc)}

    studies = []
    for study in payload.get("studies", []):
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        cond_mod = proto.get("conditionsModule", {})
        studies.append(
            {
                "nct_id": ident.get("nctId", ""),
                "title": ident.get("briefTitle", ""),
                "status": status_mod.get("overallStatus", ""),
                "phase": ", ".join(design.get("phases", [])),
                "conditions": ", ".join(cond_mod.get("conditions", [])),
            }
        )

    return {
        "query": query,
        "studies": studies,
        "next_page_token": payload.get("nextPageToken"),
    }
