import re
from datetime import datetime

from app.utils.helpers import to_mongo_datetime


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_GENDERS = {"male", "female", "other"}


def validate_patient_data(data: dict, *, is_update: bool = False) -> tuple[dict, list[str]]:
    errors: list[str] = []
    cleaned: dict = {}

    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()

    id_number = (data.get("id_number") or "").strip()
    if not id_number and not is_update:
        errors.append("ID number is required.") 
    cleaned["id_number"] = id_number
    
    if not first_name:
        errors.append("First name is required.")
    if not last_name:
        errors.append("Last name is required.")
    cleaned["first_name"] = first_name
    cleaned["last_name"] = last_name

    dob_raw = (data.get("date_of_birth") or "").strip()
    if not dob_raw and not is_update:
        errors.append("Date of birth is required.")
    elif dob_raw:
        try:
            parsed_date = datetime.strptime(dob_raw, "%Y-%m-%d").date()
            cleaned["date_of_birth"] = to_mongo_datetime(parsed_date)
        except ValueError:
            errors.append("Date of birth must be in YYYY-MM-DD format.")

    gender = (data.get("gender") or "").strip().lower()
    if not gender and not is_update:
        errors.append("Gender is required.")
    elif gender and gender not in VALID_GENDERS:
        errors.append("Gender must be male, female, or other.")
    elif gender:
        cleaned["gender"] = gender

    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    if email and not EMAIL_PATTERN.match(email):
        errors.append("Email address is invalid.")
    cleaned["phone"] = phone
    cleaned["email"] = email

    cleaned["address"] = {
        "street": (data.get("street") or "").strip(),
        "city": (data.get("city") or "").strip(),
        "state": (data.get("state") or "").strip(),
        "zip": (data.get("zip") or "").strip(),
    }

    return cleaned, errors


def validate_visit_data(data: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    cleaned: dict = {}

    patient_id = (data.get("patient_id") or "").strip().upper()
    if not patient_id:
        errors.append("Patient ID is required.")
    cleaned["patient_id"] = patient_id

    symptoms = (data.get("symptoms") or "").strip()
    diagnosis = (data.get("diagnosis") or "").strip()
    if not symptoms:
        errors.append("Symptoms are required.")
    if not diagnosis:
        errors.append("Diagnosis is required.")
    cleaned["symptoms"] = symptoms
    cleaned["diagnosis"] = diagnosis

    visit_date_raw = (data.get("visit_date") or "").strip()
    if not visit_date_raw:
        errors.append("Visit date is required.")
    else:
        try:
            parsed = datetime.strptime(visit_date_raw, "%Y-%m-%d").date()
            cleaned["visit_date"] = to_mongo_datetime(parsed)
        except ValueError:
            errors.append("Visit date must be in YYYY-MM-DD format.")

    heart_rate_raw = (data.get("heart_rate") or "").strip()
    temperature_raw = (data.get("temperature") or "").strip()
    heart_rate = None
    temperature = None

    if heart_rate_raw:
        try:
            heart_rate = int(heart_rate_raw)
        except ValueError:
            errors.append("Heart rate must be a whole number.")

    if temperature_raw:
        try:
            temperature = float(temperature_raw)
        except ValueError:
            errors.append("Temperature must be a number.")

    cleaned["vitals"] = {
        "blood_pressure": (data.get("blood_pressure") or "").strip(),
        "heart_rate": heart_rate,
        "temperature": temperature,
    }

    return cleaned, errors


def validate_prescription_data(data: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    cleaned: dict = {}

    medication_name = (data.get("medication_name") or "").strip()
    dosage = (data.get("dosage") or "").strip()
    frequency = (data.get("frequency") or "").strip()
    instructions = (data.get("instructions") or "").strip()

    if not medication_name:
        errors.append("Medication name is required.")
    if not dosage:
        errors.append("Dosage is required.")
    if not frequency:
        errors.append("Frequency is required.")

    cleaned["medication_name"] = medication_name
    cleaned["dosage"] = dosage
    cleaned["frequency"] = frequency
    cleaned["instructions"] = instructions

    return cleaned, errors
