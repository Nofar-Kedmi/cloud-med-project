"""Medical spell-checking and typo correction for OCR prescription text."""

from __future__ import annotations

import re
from difflib import get_close_matches

# Common OCR misreads -> canonical medical terms
TYPO_MAP: dict[str, str] = {
    "zains": "daily",
    "zain": "daily",
    "dailv": "daily",
    "dailly": "daily",
    "dauly": "daily",
    "daly": "daily",
    "daiiy": "daily",
    "dailiy": "daily",
    "twlce": "twice",
    "twce": "twice",
    "twic": "twice",
    "thrlce": "thrice",
    "thricee": "thrice",
    "weeldy": "weekly",
    "weekiy": "weekly",
    "montly": "monthly",
    "bedtlme": "bedtime",
    "mornlng": "morning",
    "evenlng": "evening",
    "orallyy": "orally",
    "oraly": "orally",
    "tabiet": "tablet",
    "tabllet": "tablet",
    "tablett": "tablet",
    "capsulee": "capsule",
    "capsul": "capsule",
    "milligram": "mg",
    "milligrams": "mg",
    "milliliter": "ml",
    "milliliters": "ml",
    "medlcation": "medication",
    "medicatlon": "medication",
    "medicationn": "medication",
    "dosagee": "dosage",
    "dosoge": "dosage",
    "frequencyy": "frequency",
    "frequeney": "frequency",
    "instruotions": "instructions",
    "instructlons": "instructions",
    "prescriptlon": "prescription",
    "metformln": "metformin",
    "ibuprufen": "ibuprofen",
    "ibuprofin": "ibuprofen",
    "acetaminophenn": "acetaminophen",
    "amoxlcillin": "amoxicillin",
    "lisinoprll": "lisinopril",
    "atorvastatln": "atorvastatin",
    "omeprazol": "omeprazole",
    "asplrin": "aspirin",
    "neede": "needed",
    "prn": "PRN",
}

MEDICAL_VOCABULARY: set[str] = {
    "daily",
    "twice",
    "once",
    "thrice",
    "weekly",
    "monthly",
    "bedtime",
    "morning",
    "evening",
    "night",
    "oral",
    "orally",
    "tablet",
    "tablets",
    "capsule",
    "capsules",
    "mg",
    "ml",
    "mcg",
    "g",
    "take",
    "every",
    "hours",
    "hour",
    "days",
    "day",
    "as",
    "needed",
    "with",
    "food",
    "water",
    "medication",
    "dosage",
    "frequency",
    "instructions",
    "prescription",
    "before",
    "after",
    "meals",
    "meal",
    "dose",
    "doses",
    "apply",
    "topical",
    "injection",
    "subcutaneous",
    "intravenous",
    "PRN",
    "metformin",
    "ibuprofen",
    "acetaminophen",
    "amoxicillin",
    "lisinopril",
    "atorvastatin",
    "omeprazole",
    "aspirin",
    "paracetamol",
    "insulin",
    "warfarin",
    "levothyroxine",
    "amlodipine",
    "losartan",
    "hydrochlorothiazide",
    "prednisone",
    "gabapentin",
    "sertraline",
}

PHRASE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\btwice\s+(?:zains|zain|dailv|dailly|dauly|daly|daiiy|dailiy)\b", re.I), "twice daily"),
    (re.compile(r"\bonce\s+(?:zains|zain|dailv|dailly|dauly|daly|daiiy|dailiy)\b", re.I), "once daily"),
    (re.compile(r"\bthree\s+times\s+(?:zains|zain|dailv|dailly|dauly|daly|daiiy|dailiy)\b", re.I), "three times daily"),
]

WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[^\w\s]")


def _correct_word(word: str) -> tuple[str, bool]:
    if not word or not word[0].isalpha():
        return word, False

    lower = word.lower()
    if lower in TYPO_MAP:
        corrected = TYPO_MAP[lower]
        if word.isupper():
            return corrected.upper(), True
        if word[0].isupper():
            return corrected.capitalize(), True
        return corrected, True

    if lower in MEDICAL_VOCABULARY:
        return word, False

    matches = get_close_matches(lower, MEDICAL_VOCABULARY, n=1, cutoff=0.82)
    if matches and lower != matches[0]:
        corrected = matches[0]
        if word.isupper():
            return corrected.upper(), True
        if word[0].isupper():
            return corrected.capitalize(), True
        return corrected, True

    return word, False


def correct_medical_ocr_text(text: str) -> dict[str, str | list[str] | bool]:
    """
    Apply medical spell-checking to raw OCR output.

    Returns corrected_text, original_text, and a list of applied corrections.
    """
    original_text = (text or "").strip()
    if not original_text:
        return {
            "original_text": "",
            "corrected_text": "",
            "corrections": [],
            "was_corrected": False,
        }

    corrected = original_text
    corrections: list[str] = []

    for pattern, replacement in PHRASE_PATTERNS:
        updated, count = pattern.subn(replacement, corrected)
        if count:
            corrections.append(f"Phrase pattern: {pattern.pattern} -> {replacement}")
            corrected = updated

    tokens = WORD_PATTERN.findall(corrected)
    rebuilt: list[str] = []
    last_end = 0

    for match in WORD_PATTERN.finditer(corrected):
        rebuilt.append(corrected[last_end : match.start()])
        word = match.group(0)
        fixed, changed = _correct_word(word)
        if changed:
            corrections.append(f"{word} -> {fixed}")
        rebuilt.append(fixed)
        last_end = match.end()
    rebuilt.append(corrected[last_end:])
    corrected = "".join(rebuilt)

    return {
        "original_text": original_text,
        "corrected_text": corrected,
        "corrections": corrections,
        "was_corrected": corrected != original_text,
    }
