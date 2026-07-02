"""OCR operations backed by Google Cloud Vision."""

from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import Any

from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.auth.exceptions import GoogleAuthError
from google.cloud import vision
from google.oauth2 import service_account


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDER = "google_cloud_vision"
MODEL = "document_text_detection"


def _credentials_path() -> Path:
    env_path = os.getenv("GOOGLE_VISION_CREDENTIALS_FILE", "").strip()
    if env_path:
        path = Path(env_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path
    return PROJECT_ROOT / "google_vision_credentials.json"


class GoogleCloudVisionError(RuntimeError):
    """Raised when the Vision API returns an error in its response."""


def _result(
    image_path: str,
    *,
    success: bool,
    extracted_text: str = "",
    error_type: str | None = None,
    error: str | None = None,
    traceback_text: str | None = None,
) -> dict[str, Any]:
    """Build a consistent OCR response."""
    return {
        "success": success,
        "provider": PROVIDER,
        "model": MODEL,
        "image_path": image_path,
        "extracted_text": extracted_text,
        "error_type": error_type,
        "error": error,
        "traceback": traceback_text,
    }


def _exception_result(image_path: str, e: Exception) -> dict[str, Any]:
    """Print and return the complete active exception."""
    error_type = type(e).__name__
    error_message = str(e)
    traceback_text = traceback.format_exc()

    print("OCR exception details:")
    print(f"  error_type: {error_type}")
    print(f"  error: {error_message}")
    print("  traceback:")
    print(traceback_text)

    return _result(
        image_path,
        success=False,
        error_type=error_type,
        error=error_message,
        traceback_text=traceback_text,
    )


def extract_text_from_prescription(image_path: str | Path) -> dict[str, Any]:
    """Extract text from a local prescription image using document OCR."""
    try:
        resolved_path = Path(image_path).expanduser().resolve()
    except (TypeError, ValueError) as e:
        return _exception_result(str(image_path), e)

    path_text = str(resolved_path)

    if not resolved_path.is_file():
        return _result(
            path_text,
            success=False,
            error_type="FileNotFoundError",
            error=f"Image file not found: {resolved_path}",
        )
    credentials_path = _credentials_path()
    if not credentials_path.is_file():
        return _result(
            path_text,
            success=False,
            error_type="CredentialsFileNotFoundError",
            error=f"Google Vision credentials not found: {credentials_path}",
        )

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path)
        )
        client = vision.ImageAnnotatorClient(credentials=credentials)

        image = vision.Image(content=resolved_path.read_bytes())
        response = client.document_text_detection(image=image)

        if response.error.message:
            raise GoogleCloudVisionError(response.error.message)

        extracted_text = (response.full_text_annotation.text or "").strip()
        if not extracted_text:
            return _result(
                path_text,
                success=False,
                error_type="EmptyOCRResult",
                error="Google Cloud Vision returned no readable text.",
            )

        return _result(
            path_text,
            success=True,
            extracted_text=extracted_text,
        )
    except (GoogleAuthError, GoogleAPICallError, RetryError) as e:
        return _exception_result(path_text, e)
    except (OSError, TypeError, ValueError) as e:
        return _exception_result(path_text, e)
    except Exception as e:
        return _exception_result(path_text, e)
