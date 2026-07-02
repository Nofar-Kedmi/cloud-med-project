from datetime import datetime, timezone

from app.utils.validators import validate_prescription_data, validate_visit_data


def test_validate_visit_data_converts_visit_date_to_datetime():
    cleaned, errors = validate_visit_data(
        {
            "patient_id": "PAT-2026-0001",
            "symptoms": "Fever and cough",
            "diagnosis": "Acute bronchitis",
            "visit_date": "2026-06-28",
            "blood_pressure": "120/80",
            "heart_rate": "72",
            "temperature": "36.8",
        }
    )
    assert errors == []
    assert cleaned["visit_date"] == datetime(2026, 6, 28, tzinfo=timezone.utc)


def test_validate_prescription_data_requires_core_fields():
    _, errors = validate_prescription_data({})
    assert "Medication name is required." in errors
    assert "Dosage is required." in errors
