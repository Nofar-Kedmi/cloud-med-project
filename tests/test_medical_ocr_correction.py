from app.services.medical_ocr_correction import correct_medical_ocr_text


def test_corrects_twice_zains_typo():
    result = correct_medical_ocr_text("Take 1 tablet twice Zains with food.")
    assert result["corrected_text"] == "Take 1 tablet twice daily with food."
    assert result["was_corrected"] is True


def test_corrects_common_medication_typo():
    result = correct_medical_ocr_text("Medication: metformln 500 mg")
    assert "metformin" in result["corrected_text"].lower()
    assert result["was_corrected"] is True


def test_preserves_clean_text():
    text = "Take 1 tablet twice daily."
    result = correct_medical_ocr_text(text)
    assert result["corrected_text"] == text
    assert result["was_corrected"] is False
