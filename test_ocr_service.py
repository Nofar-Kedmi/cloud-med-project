"""Run OCR on the sample prescription image and save the result."""

import traceback
from pathlib import Path
from pprint import pprint

from app.services.ocr_result_service import OCRResultServiceError, save_ocr_result
from app.services.ocr_service import extract_text_from_prescription


IMAGE_PATH = (
    Path(__file__).resolve().parent
    / "sample_files"
    / "handwritten_prescription.jpg"
)


def main() -> int:
    if not IMAGE_PATH.is_file():
        print(f"OCR test cannot run: image not found at {IMAGE_PATH}")
        return 1

    print(f"Running OCR on: {IMAGE_PATH}")
    result = extract_text_from_prescription(IMAGE_PATH)

    print("\nFull OCR result dictionary:")
    pprint(result, sort_dicts=False)

    if not result["success"]:
        print("\nOCR failed:")
        print(f"  error_type: {result['error_type']}")
        print(f"  error: {result['error']}")
        if result["traceback"]:
            print("  traceback:")
            print(result["traceback"])
        print("OCR failed, so no MongoDB document was created.")
        return 1

    try:
        document_id = save_ocr_result(
            result["image_path"],
            result["extracted_text"],
            result["provider"],
            result["model"],
        )
    except OCRResultServiceError as e:
        error_type = type(e).__name__
        error_message = str(e)
        traceback_text = traceback.format_exc()
        print("\nOCR succeeded, but MongoDB save failed:")
        print(f"  error_type: {error_type}")
        print(f"  error: {error_message}")
        print("  traceback:")
        print(traceback_text)
        return 1

    print(f"\nInserted MongoDB document id: {document_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
