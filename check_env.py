#!/usr/bin/env python3
"""Validate .env configuration and required credential files."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent

REQUIRED_ENV_VARS = (
    "MONGO_URI",
    "MONGO_DB_NAME",
    "TAVILY_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_DRIVE_CREDENTIALS_FILE",
    "GOOGLE_VISION_CREDENTIALS_FILE",
)

REQUIRED_ROOT_FILES = (
    "credentials.json",
    "google_vision_credentials.json",
)


def main() -> int:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        print("Environment configuration check failed:\n")
        print(f"  [MISSING FILE] .env not found at {env_path}")
        return 1

    load_dotenv(env_path)

    missing: list[str] = []

    for name in REQUIRED_ENV_VARS:
        value = os.getenv(name)
        if value is None:
            missing.append(f"  [MISSING ENV] {name} is not set")
        elif not value.strip():
            missing.append(f"  [EMPTY ENV]   {name} is set but empty")

    for filename in REQUIRED_ROOT_FILES:
        file_path = PROJECT_ROOT / filename
        if not file_path.is_file():
            missing.append(f"  [MISSING FILE] {filename} not found in project root ({PROJECT_ROOT})")

    if missing:
        print("Environment configuration check failed:\n")
        print("\n".join(missing))
        return 1

    print("Environment configuration is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
