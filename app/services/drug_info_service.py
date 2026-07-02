"""Medication side-effect consultation for pharmacists."""

from __future__ import annotations

import requests

from app.services.search_service import search_medical_info

OPENFDA_URL = "https://api.fda.gov/drug/label.json"
TIMEOUT_SECONDS = 15


def _search_openfda(drug_name: str) -> dict:
    params = {
        "search": f'openfda.generic_name:"{drug_name}"',
        "limit": 1,
    }
    try:
        response = requests.get(OPENFDA_URL, params=params, timeout=TIMEOUT_SECONDS)
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return {}
        label = results[0]
        return {
            "source": "openfda",
            "drug": drug_name,
            "warnings": label.get("warnings", [])[:3],
            "adverse_reactions": label.get("adverse_reactions", [])[:3],
            "drug_interactions": label.get("drug_interactions", [])[:2],
        }
    except requests.RequestException:
        return {}


def get_medication_side_effects(drug_name: str) -> dict:
    drug_name = (drug_name or "").strip()
    if not drug_name:
        return {
            "drug": drug_name,
            "available": False,
            "message": "Enter a medication name.",
            "details": {},
        }

    fda = _search_openfda(drug_name)
    if fda:
        return {
            "drug": drug_name,
            "available": True,
            "message": "Side-effect information from OpenFDA.",
            "details": fda,
        }

    tavily = search_medical_info(f"{drug_name} medication side effects adverse reactions")
    if tavily.get("error"):
        return {
            "drug": drug_name,
            "available": False,
            "message": tavily["error"],
            "details": {},
        }

    return {
        "drug": drug_name,
        "available": True,
        "message": "Side-effect summary from medical literature search.",
        "details": {
            "source": "tavily",
            "results": tavily.get("results", [])[:5],
        },
    }
