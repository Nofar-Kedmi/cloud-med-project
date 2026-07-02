from app.models.patient import Patient
from app.utils.validators import validate_patient_data


class PatientNotFoundError(Exception):
    pass


class PatientValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def create_patient(data: dict) -> Patient:
    cleaned, errors = validate_patient_data(data)
    if errors:
        raise PatientValidationError(errors)
    return Patient.create(cleaned)


def update_patient(patient_id: str, data: dict) -> Patient:
    existing = Patient.find_by_patient_id(patient_id)
    if existing is None:
        raise PatientNotFoundError(f"Patient {patient_id} not found.")

    cleaned, errors = validate_patient_data(data, is_update=True)
    if errors:
        raise PatientValidationError(errors)

    patient = Patient.update(patient_id, cleaned)
    if patient is None:
        raise PatientNotFoundError(f"Patient {patient_id} not found.")
    return patient


def get_patient(patient_id: str) -> Patient:
    patient = Patient.find_by_patient_id(patient_id)
    if patient is None:
        raise PatientNotFoundError(f"Patient {patient_id} not found.")
    return patient


def list_patients(page: int = 1, per_page: int = 20) -> dict:
    patients = Patient.find_all(page=page, per_page=per_page)
    total = Patient.count()
    return {
        "patients": patients,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": max(1, (total + per_page - 1) // per_page),
    }
