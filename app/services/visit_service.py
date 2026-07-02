from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.visit import Visit
from app.utils.validators import validate_prescription_data, validate_visit_data


class VisitValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class ClinicalEncounterError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def create_visit(doctor_id: str, data: dict) -> Visit:
    cleaned, errors = validate_visit_data(data)
    if errors:
        raise VisitValidationError(errors)

    cleaned["doctor_id"] = doctor_id
    cleaned["external_refs"] = data.get("external_refs", {})
    return Visit.create(cleaned)


def save_visit_and_prescription(doctor_id: str, data: dict) -> tuple[Visit, Prescription]:
    visit_cleaned, visit_errors = validate_visit_data(data)
    rx_cleaned, rx_errors = validate_prescription_data(data)
    errors = visit_errors + rx_errors
    if errors:
        raise ClinicalEncounterError(errors)

    visit_cleaned["doctor_id"] = doctor_id
    visit_cleaned["external_refs"] = data.get("external_refs", {})
    visit = Visit.create(visit_cleaned)

    prescription = Prescription.create(
        {
            "visit_id": visit.visit_id,
            "patient_id": visit_cleaned["patient_id"],
            "doctor_id": doctor_id,
            **rx_cleaned,
        }
    )
    return visit, prescription


def get_visits_for_doctor(doctor_id: str, limit: int = 10) -> list[Visit]:
    return Visit.find_by_doctor_id(doctor_id, limit=limit)


def get_recent_visits_for_dashboard(doctor_id: str, limit: int = 5) -> list[dict]:
    """Return recent visits enriched with patient names via a single batch lookup."""
    visits = Visit.find_by_doctor_id(doctor_id, limit=limit)
    patient_ids = [visit.patient_id for visit in visits if visit.patient_id]
    patients = Patient.find_by_patient_ids(patient_ids)

    rows: list[dict] = []
    for visit in visits:
        patient = patients.get(visit.patient_id)
        patient_name = patient.full_name.strip() if patient else ""
        rows.append(
            {
                "visit_id": visit.visit_id,
                "patient_id": visit.patient_id,
                "patient_name": patient_name,
                "patient_display": patient_name or visit.patient_id,
                "diagnosis": visit.diagnosis,
                "visit_date": visit.visit_date,
            }
        )
    return rows


def get_visits_for_patient(patient_id: str) -> list[Visit]:    return Visit.find_by_patient_id(patient_id)
