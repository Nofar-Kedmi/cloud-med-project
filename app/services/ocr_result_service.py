"""Persistence for OCR results."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pymongo.errors import PyMongoError

from app.services.db_service import ocr_results_collection


class OCRResultServiceError(RuntimeError):
    """Raised when an OCR result cannot be saved."""


def _serialize_result(document: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(document)
    if "_id" in serialized:
        serialized["document_id"] = str(serialized.pop("_id"))
    return serialized


def save_ocr_result(
    image_path: str | Path,
    extracted_text: str,
    provider: str,
    model: str,
    *,
    prescription_id: str | None = None,
    pharmacist_id: str | None = None,
    image_filename: str = "",
    raw_text: str = "",
    original_ocr_text: str = "",
    ocr_corrections: list[dict[str, Any]] | None = None,
) -> str:
    """Save an OCR result and return its MongoDB document id."""
    try:
        document: dict[str, Any] = {
            "image_path": str(Path(image_path).expanduser().resolve()),
            "extracted_text": extracted_text,
            "provider": provider,
            "model": model,
            "created_at": datetime.now(timezone.utc),
            "decoded_at": datetime.now(timezone.utc),
        }
        if prescription_id:
            document["prescription_id"] = prescription_id
        if pharmacist_id:
            document["pharmacist_id"] = pharmacist_id
        if image_filename:
            document["image_filename"] = image_filename
        if raw_text:
            document["raw_text"] = raw_text
        if original_ocr_text:
            document["original_ocr_text"] = original_ocr_text
        if ocr_corrections:
            document["ocr_corrections"] = ocr_corrections

        insert_result = ocr_results_collection.insert_one(document)
    except (PyMongoError, OSError, TypeError, ValueError) as exc:
        raise OCRResultServiceError(f"Could not save OCR result: {exc}") from exc

    return str(insert_result.inserted_id)


def get_latest_ocr_bundle_for_prescription(prescription_id: str) -> dict[str, str]:
    """Return the latest corrected and original OCR text for a prescription."""
    document = ocr_results_collection.find_one(
        {"prescription_id": prescription_id},
        sort=[("created_at", -1), ("decoded_at", -1)],
    )
    if not document:
        return {"corrected_text": "", "original_text": ""}

    corrected_text = (document.get("extracted_text") or "").strip()
    original_text = (
        document.get("original_ocr_text")
        or document.get("raw_text")
        or corrected_text
    ).strip()
    return {
        "corrected_text": corrected_text,
        "original_text": original_text,
    }


def get_latest_ocr_text_for_prescription(prescription_id: str) -> str:
    """Return the latest corrected OCR text for a prescription."""
    return get_latest_ocr_bundle_for_prescription(prescription_id)["corrected_text"]


def get_ocr_results_for_prescription(prescription_id: str) -> list[dict[str, Any]]:
    """Return OCR history for a prescription, newest first."""
    try:
        cursor = ocr_results_collection.find(
            {"prescription_id": prescription_id}
        ).sort("created_at", -1)
        return [_serialize_result(document) for document in cursor]
    except PyMongoError as exc:
        raise OCRResultServiceError(f"Could not load OCR results: {exc}") from exc
