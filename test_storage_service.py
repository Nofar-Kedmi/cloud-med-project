"""Test the Google Drive storage service with the sample PDF."""

from pathlib import Path

from services.storage_service import StorageServiceError, upload_pdf_to_drive


SAMPLE_PDF = Path(__file__).resolve().parent / "sample_files" / "sample_prescription.pdf"


def main() -> int:
    try:
        uploaded_file = upload_pdf_to_drive(SAMPLE_PDF)
    except StorageServiceError as exc:
        print(f"Upload failed: {exc}")
        return 1

    print(f"file_id: {uploaded_file['file_id']}")
    print(f"web_view_link: {uploaded_file['web_view_link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
