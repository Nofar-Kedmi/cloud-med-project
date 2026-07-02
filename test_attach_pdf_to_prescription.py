"""Attach the sample prescription PDF to a MongoDB prescription record."""

import os
from pathlib import Path

from services.prescription_service import attach_pdf_to_prescription


SAMPLE_FILES_DIR = Path(__file__).resolve().parent / "sample_files"


def main() -> None:
    # Run from the sample directory so the requested relative filename resolves.
    original_directory = Path.cwd()
    try:
        os.chdir(SAMPLE_FILES_DIR)
        result = attach_pdf_to_prescription(
            "RX-2026-0001", "sample_prescription.pdf"
        )
    finally:
        os.chdir(original_directory)

    print("Attach PDF to prescription result:")
    print(f"  success: {result['success']}")
    print(f"  prescription_id: {result['prescription_id']}")
    print(f"  file_id: {result['file_id']}")
    print(f"  pdf_url: {result['pdf_url']}")
    print(f"  matched_count: {result['matched_count']}")
    print(f"  modified_count: {result['modified_count']}")
    if "error" in result:
        print(f"  error: {result['error']}")


if __name__ == "__main__":
    main()
