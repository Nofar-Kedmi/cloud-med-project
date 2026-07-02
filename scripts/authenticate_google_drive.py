#!/usr/bin/env python3
"""Authorize Google Drive once and create token.json for the Flask app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from app.services.storage_service import StorageServiceError, authenticate_google_drive


def main() -> int:
    try:
        credentials = authenticate_google_drive()
    except StorageServiceError as exc:
        print(f"Google Drive authorization failed:\n{exc}", file=sys.stderr)
        return 1

    token_file = os.getenv("GOOGLE_DRIVE_TOKEN_FILE", "token.json")
    print("Google Drive authorization succeeded.")
    print(f"Token saved to: {PROJECT_ROOT / token_file}")
    print(f"Authorized scopes: {', '.join(credentials.scopes or [])}")
    print("\nYou can now save visits and upload prescription PDFs from the app.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
