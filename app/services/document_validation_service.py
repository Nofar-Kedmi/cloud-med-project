"""Validate prescription images with Google Cloud Vision."""

from __future__ import annotations

import os
import re
import traceback
from pathlib import Path
from typing import Any

from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.auth.exceptions import GoogleAuthError
from google.cloud import vision
from google.oauth2 import service_account


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDER = "google_cloud_vision"
MODEL = "label_detection + text_detection"
TEXT_PREVIEW_LENGTH = 400


def _credentials_path() -> Path:
    env_path = os.getenv("GOOGLE_VISION_CREDENTIALS_FILE", "").strip()
    if env_path:
        path = Path(env_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path
    return PROJECT_ROOT / "google_vision_credentials.json"

CONTEXT_KEYWORDS = {
    "document",
    "text",
    "paper",
    "form",
    "prescription",
    "medicine",
    "medication",
    "medical",
    "patient",
    "dosage",
    "drug",
    "pharmacy",
    "healthcare",
    "handwriting",
    "writing",
}


class DocumentValidationError(RuntimeError):
    """Raised when Vision reports an error in a validation response."""


def _result(
    image_path: str,
    *,
    success: bool,
    is_document: bool = False,
    confidence_score: float = 0.0,
    labels: list[dict[str, Any]] | None = None,
    detected_text_preview: str = "",
    reasons: list[str] | None = None,
    error_type: str | None = None,
    error: str | None = None,
    traceback_text: str | None = None,
) -> dict[str, Any]:
    """Build a consistent validation response."""
    return {
        "success": success,
        "image_path": image_path,
        "is_document": is_document,
        "confidence_score": confidence_score,
        "labels": labels or [],
        "detected_text_preview": detected_text_preview,
        "reasons": reasons or [],
        "provider": PROVIDER,
        "model": MODEL,
        "error_type": error_type,
        "error": error,
        "traceback": traceback_text,
    }


def _exception_result(image_path: str, e: Exception) -> dict[str, Any]:
    """Print and return the complete active exception."""
    error_type = type(e).__name__
    error_message = str(e)
    traceback_text = traceback.format_exc()

    print("Document validation exception details:")
    print(f"  error_type: {error_type}")
    print(f"  error: {error_message}")
    print("  traceback:")
    print(traceback_text)

    return _result(
        image_path,
        success=False,
        reasons=["Document validation could not be completed."],
        error_type=error_type,
        error=error_message,
        traceback_text=traceback_text,
    )


def _words(value: str) -> set[str]:
    """Return normalized words suitable for context matching."""
    return set(re.findall(r"[a-z]{3,}", value.lower()))


def _evaluate_document(
    detected_text: str, labels: list[dict[str, Any]]
) -> tuple[bool, float, list[str]]:
    """Evaluate readability and document/medical context evidence."""
    text_words = _words(detected_text)
    readable_text = len(text_words) >= 3 and len(detected_text.strip()) >= 10
    text_context = sorted(text_words & CONTEXT_KEYWORDS)

    matching_labels = []
    matching_label_score = 0.0
    for label in labels:
        if _words(label["description"]) & CONTEXT_KEYWORDS:
            matching_labels.append(label["description"])
            matching_label_score = max(matching_label_score, label["score"])

    has_context = bool(text_context or matching_labels)
    is_document = readable_text and has_context

    readability_score = min(len(text_words) / 12, 1.0)
    keyword_score = min(len(text_context) / 3, 1.0)
    context_score = max(keyword_score, matching_label_score)
    confidence_score = round(
        (0.6 * readability_score) + (0.4 * context_score), 3
    )
    if not is_document:
        confidence_score = min(confidence_score, 0.49)

    reasons = []
    if readable_text:
        reasons.append(f"Readable text detected ({len(text_words)} unique words).")
    else:
        reasons.append("Not enough readable text was detected.")

    if text_context:
        reasons.append(f"OCR context keywords found: {', '.join(text_context)}.")
    if matching_labels:
        reasons.append(f"Relevant Vision labels found: {', '.join(matching_labels)}.")
    if not has_context:
        reasons.append("No document, prescription, or medical context was detected.")

    return is_document, confidence_score, reasons


def validate_prescription_document(image_path: str | Path) -> dict[str, Any]:
    """Decide whether a local image resembles a prescription document."""
    try:
        resolved_path = Path(image_path).expanduser().resolve()
    except (TypeError, ValueError) as e:
        return _exception_result(str(image_path), e)

    path_text = str(resolved_path)

    if not resolved_path.is_file():
        return _result(
            path_text,
            success=False,
            reasons=["The requested image file does not exist."],
            error_type="FileNotFoundError",
            error=f"Image file not found: {resolved_path}",
        )
    credentials_path = _credentials_path()
    if not credentials_path.is_file():
        return _result(
            path_text,
            success=False,
            reasons=["Google Cloud Vision credentials are unavailable."],
            error_type="CredentialsFileNotFoundError",
            error=f"Google Vision credentials not found: {credentials_path}",
        )

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path)
        )
        client = vision.ImageAnnotatorClient(credentials=credentials)
        image = vision.Image(content=resolved_path.read_bytes())

        label_response = client.label_detection(image=image)
        text_response = client.text_detection(image=image)

        if label_response.error.message:
            raise DocumentValidationError(
                f"Label detection failed: {label_response.error.message}"
            )
        if text_response.error.message:
            raise DocumentValidationError(
                f"Text detection failed: {text_response.error.message}"
            )

        labels = [
            {
                "description": annotation.description,
                "score": round(float(annotation.score), 3),
            }
            for annotation in label_response.label_annotations
        ]
        detected_text = (
            text_response.text_annotations[0].description
            if text_response.text_annotations
            else ""
        ).strip()
        text_preview = " ".join(detected_text.split())[:TEXT_PREVIEW_LENGTH]
        is_document, confidence_score, reasons = _evaluate_document(
            detected_text, labels
        )

        return _result(
            path_text,
            success=True,
            is_document=is_document,
            confidence_score=confidence_score,
            labels=labels,
            detected_text_preview=text_preview,
            reasons=reasons,
        )
    except (GoogleAuthError, GoogleAPICallError, RetryError) as e:
        return _exception_result(path_text, e)
    except (OSError, TypeError, ValueError) as e:
        return _exception_result(path_text, e)
    except Exception as e:
        return _exception_result(path_text, e)
