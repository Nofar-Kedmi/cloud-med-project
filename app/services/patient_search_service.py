import re

from app.models.patient import Patient


def search_patients(query: str, limit: int = 20) -> list[Patient]:
    query = (query or "").strip()
    if not query:
        return []

    if query.upper().startswith("PAT-"):
        patient = Patient.find_by_patient_id(query.upper())
        return [patient] if patient else []

    try:
        text_results = Patient.search_by_name(query, limit=limit)
        if text_results:
            return text_results
    except Exception:
        pass

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    collection = Patient._collection()
    cursor = collection.find(
        {
            "$or": [
                {"patient_id": pattern},
                {"first_name": pattern},
                {"last_name": pattern},
            ]
        }
    ).limit(limit)
    return [Patient(doc) for doc in cursor]
