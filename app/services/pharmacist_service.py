"""Pharmacist workflows backed by db_service collections."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from pymongo import ReturnDocument

from app.services.db_service import (
    patients_collection,
    prescriptions_collection,
)

SAMPLE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PATIENT_SEARCH_RESULTS = 20


class PharmacistServiceError(Exception):
    pass


class PatientNotFoundError(PharmacistServiceError):
    pass


class PrescriptionNotFoundError(PharmacistServiceError):
    pass


def find_patients(query: str, *, limit: int = MAX_PATIENT_SEARCH_RESULTS) -> list[dict]:
    """Search patients by ID number, first name, or last name."""
    query = (query or "").strip()
    if not query:
        return []

    regex = {"$regex": re.escape(query), "$options": "i"}
    cursor = (
        patients_collection.find(
            {
                "$or": [
                    {"id_number": query},
                    {"id_number": regex},
                    {"first_name": regex},
                    {"last_name": regex},
                ]
            }
        )
        .sort([("last_name", 1), ("first_name", 1)])
        .limit(limit)
    )
    return list(cursor)


def find_patients_by_id_number(id_number: str) -> list[dict]:
    return find_patients(id_number)


def get_patient_by_patient_id(patient_id: str) -> dict | None:
    return patients_collection.find_one({"patient_id": patient_id})


def get_open_prescriptions(patient_id: str) -> list[dict]:
    cursor = prescriptions_collection.find(
        {"patient_id": patient_id, "status": "open"}
    ).sort("created_at", -1)
    return list(cursor)


def get_recently_dispensed_prescriptions(patient_id: str, *, limit: int = 10) -> list[dict]:
    cursor = prescriptions_collection.find(
        {"patient_id": patient_id, "status": "dispensed"}
    ).sort([("dispensed_at", -1), ("updated_at", -1), ("created_at", -1)]).limit(limit)
    return list(cursor)


def get_prescription(prescription_id: str) -> dict | None:
    return prescriptions_collection.find_one({"prescription_id": prescription_id})


def list_sample_prescription_files(samples_dir: Path) -> list[str]:
    if not samples_dir.is_dir():
        samples_dir.mkdir(parents=True, exist_ok=True)
        return []

    return sorted(
        path.name
        for path in samples_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SAMPLE_IMAGE_EXTENSIONS
    )


def mark_prescription_dispensed(
    prescription_id: str,
    *,
    corrected_medication_name: str | None = None,
    verified_ocr_text: str | None = None,
    pharmacist_id: str | None = None,
) -> dict:
    update_fields: dict = {
        "status": "dispensed",
        "updated_at": datetime.now(timezone.utc),
        "dispensed_at": datetime.now(timezone.utc),
    }
    if corrected_medication_name:
        update_fields["medication_name"] = corrected_medication_name
        update_fields["pharmacist_corrected_medication"] = corrected_medication_name
    if verified_ocr_text:
        update_fields["verified_ocr_text"] = verified_ocr_text
    if pharmacist_id:
        update_fields["dispensed_by"] = pharmacist_id

    result = prescriptions_collection.find_one_and_update(
        {"prescription_id": prescription_id, "status": "open"},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        existing = get_prescription(prescription_id)
        if existing is None:
            raise PrescriptionNotFoundError(f"Prescription {prescription_id} not found.")
        raise PharmacistServiceError(
            f"Prescription {prescription_id} is not open (status: {existing.get('status')})."
        )
    return result
