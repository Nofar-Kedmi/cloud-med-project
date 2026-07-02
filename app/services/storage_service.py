"""Google Drive storage operations."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from google.auth.exceptions import GoogleAuthError, RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError as exc:
    _GOOGLE_IMPORT_ERROR: ImportError | None = exc
else:
    _GOOGLE_IMPORT_ERROR = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
PLACEHOLDER_FOLDER_IDS = {"", "your-drive-folder-id", "your_folder_id"}


class StorageServiceError(RuntimeError):
    """Raised when a storage operation cannot be completed."""


def _resolve_path(env_key: str, default: Path) -> Path:
    value = os.environ.get(env_key, "").strip()
    if value:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path
    return default


def _credentials_path() -> Path:
    return _resolve_path(
        "GOOGLE_DRIVE_CREDENTIALS_FILE",
        _resolve_path("GOOGLE_APPLICATION_CREDENTIALS", PROJECT_ROOT / "credentials.json"),
    )


def _token_path() -> Path:
    return _resolve_path("GOOGLE_DRIVE_TOKEN_FILE", PROJECT_ROOT / "token.json")


def _drive_folder_id() -> str | None:
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if folder_id in PLACEHOLDER_FOLDER_IDS:
        return None
    return folder_id


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _validate_oauth_client_file(credentials_path: Path) -> None:
    try:
        payload = json.loads(credentials_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageServiceError(
            f"Could not read Google Drive OAuth client file at {credentials_path}: {exc}"
        ) from exc

    if payload.get("type") == "service_account":
        raise StorageServiceError(
            f"{credentials_path.name} is a service account key. Google Drive uploads in this "
            "app use an OAuth Desktop client (credentials.json with an 'installed' section). "
            "Create an OAuth 2.0 Client ID of type Desktop in Google Cloud Console."
        )

    if "installed" not in payload:
        raise StorageServiceError(
            f"{credentials_path.name} must be a Desktop OAuth client ('installed' key). "
            "Web OAuth clients require redirect URIs that do not match run_local_server. "
            "In Google Cloud Console: APIs & Services → Credentials → Create OAuth client ID → "
            "Application type: Desktop app."
        )


def _scopes_match(credentials: Credentials) -> bool:
    granted = {scope for scope in (credentials.scopes or [])}
    required = set(SCOPES)
    return required.issubset(granted)


def _save_token(credentials: Credentials) -> None:
    token_path = _token_path()
    try:
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    except OSError as exc:
        raise StorageServiceError(f"Could not save {token_path.name}: {exc}") from exc


def _delete_token() -> None:
    token_path = _token_path()
    if token_path.is_file():
        token_path.unlink(missing_ok=True)


def _auth_setup_instructions() -> str:
    return (
        "Google Drive is not authorized yet. Run this once from your project folder:\n"
        "  python scripts/authenticate_google_drive.py\n"
        "Complete the browser sign-in, then retry saving the visit."
    )


def authenticate_google_drive(*, open_browser: bool = True) -> Credentials:
    """
    Run the OAuth Desktop flow interactively and persist token.json.

    Use this before uploading from the Flask app. Visit save must not trigger
    a browser login mid-request.
    """
    credentials_path = _credentials_path()
    if not credentials_path.is_file():
        raise StorageServiceError(
            f"Missing Google Drive OAuth credentials at {credentials_path}. "
            "Set GOOGLE_DRIVE_CREDENTIALS_FILE or place credentials.json in the project root."
        )

    _validate_oauth_client_file(credentials_path)

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        credentials = flow.run_local_server(port=0, open_browser=open_browser)
    except (OSError, ValueError, GoogleAuthError) as exc:
        raise StorageServiceError(
            "Google OAuth authentication failed. Ensure credentials.json is a Desktop OAuth "
            "client and that http://localhost redirect URIs are allowed in Google Cloud Console. "
            f"Details: {exc}"
        ) from exc

    _save_token(credentials)
    return credentials


def _load_token_credentials() -> Credentials | None:
    token_path = _token_path()
    if not token_path.is_file():
        return None

    try:
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except (OSError, ValueError) as exc:
        raise StorageServiceError(
            f"Could not read {token_path.name}. Delete it and run "
            "python scripts/authenticate_google_drive.py"
        ) from exc

    if not _scopes_match(credentials):
        _delete_token()
        raise StorageServiceError(
            f"{token_path.name} was created with different OAuth scopes. "
            "Run python scripts/authenticate_google_drive.py to authorize again."
        )

    return credentials


def _get_credentials() -> Any:
    """Load or refresh Google OAuth credentials from token.json."""
    credentials = _load_token_credentials()

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            _save_token(credentials)
        except RefreshError as exc:
            _delete_token()
            raise StorageServiceError(
                "Google Drive token expired and could not be refreshed. "
                f"{_auth_setup_instructions()} Details: {exc}"
            ) from exc

    if credentials and credentials.valid:
        return credentials

    if _is_interactive():
        return authenticate_google_drive()

    raise StorageServiceError(_auth_setup_instructions())


def _http_error_message(exc: HttpError, *, folder_id: str | None) -> str:
    status = getattr(getattr(exc, "resp", None), "status", "unknown")
    reason = exc._get_reason() if hasattr(exc, "_get_reason") else str(exc)

    if status == 403:
        if folder_id:
            return (
                f"Google Drive API error (403): {reason}. "
                f"The app could not upload to folder '{folder_id}'. "
                "With the drive.file scope, uploads work for files the app creates; "
                "target folders must be owned by the signed-in Google account or unset "
                "GOOGLE_DRIVE_FOLDER_ID to upload to My Drive root. "
                "If you changed scopes, delete token.json and run "
                "python scripts/authenticate_google_drive.py."
            )
        return (
            f"Google Drive API error (403): {reason}. "
            "Access denied — confirm Drive API is enabled, token.json is valid, and "
            "the signed-in account has permission to upload. "
            "Run python scripts/authenticate_google_drive.py to re-authorize."
        )

    if status == 404 and folder_id:
        return (
            f"Google Drive API error (404): {reason}. "
            f"Folder '{folder_id}' was not found. Check GOOGLE_DRIVE_FOLDER_ID in .env."
        )

    return f"Google Drive API error ({status}): {reason}"


def upload_pdf_to_drive(
    file_path: str | Path,
    *,
    drive_filename: str | None = None,
) -> dict[str, str]:
    """
    Upload a local PDF to Google Drive.

    Returns file_id, web_view_link, and file_name.
    """
    if _GOOGLE_IMPORT_ERROR is not None:
        raise StorageServiceError(
            "Google API packages are not installed. Run "
            "'python -m pip install -r requirements.txt'."
        ) from _GOOGLE_IMPORT_ERROR

    try:
        pdf_path = Path(file_path).expanduser().resolve()
    except (TypeError, ValueError) as exc:
        raise StorageServiceError("file_path must be a valid path.") from exc

    if not pdf_path.is_file():
        raise StorageServiceError(f"PDF file not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise StorageServiceError(f"File must have a .pdf extension: {pdf_path.name}")

    folder_id = _drive_folder_id()

    try:
        service = build(
            "drive", "v3", credentials=_get_credentials(), cache_discovery=False
        )
        media = MediaFileUpload(str(pdf_path), mimetype="application/pdf", resumable=True)
        body: dict[str, Any] = {"name": drive_filename or pdf_path.name}
        if folder_id:
            body["parents"] = [folder_id]

        uploaded_file = (
            service.files()
            .create(body=body, media_body=media, fields="id,webViewLink,name")
            .execute()
        )
    except StorageServiceError:
        raise
    except HttpError as exc:
        if folder_id and getattr(getattr(exc, "resp", None), "status", None) == 403:
            try:
                body = {"name": pdf_path.name}
                uploaded_file = (
                    service.files()
                    .create(body=body, media_body=media, fields="id,webViewLink,name")
                    .execute()
                )
            except HttpError as retry_exc:
                raise StorageServiceError(_http_error_message(retry_exc, folder_id=None)) from retry_exc
        else:
            raise StorageServiceError(_http_error_message(exc, folder_id=folder_id)) from exc
    except GoogleAuthError as exc:
        raise StorageServiceError(f"Google authentication failed: {exc}") from exc
    except OSError as exc:
        raise StorageServiceError(f"Could not read the PDF file: {exc}") from exc

    file_id = uploaded_file.get("id")
    web_view_link = uploaded_file.get("webViewLink")
    file_name = uploaded_file.get("name") or pdf_path.name

    if not file_id or not web_view_link:
        raise StorageServiceError("Google Drive returned incomplete file metadata.")

    return {
        "file_id": file_id,
        "web_view_link": web_view_link,
        "file_name": file_name,
    }
