from app.models.prescription import Prescription
from app.utils.validators import validate_prescription_data


class PrescriptionValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class PrescriptionNotFoundError(Exception):
    pass


def create_prescription(
    *,
    visit_id: str,
    patient_id: str,
    doctor_id: str,
    data: dict,
) -> Prescription:
    cleaned, errors = validate_prescription_data(data)
    if errors:
        raise PrescriptionValidationError(errors)

    payload = {
        "visit_id": visit_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        **cleaned,
    }
    return Prescription.create(payload)


def attach_pdf_to_prescription(
    prescription_id: str,
    drive_file_url: str,
    drive_file_id: str | None = None,
) -> Prescription:
    """Persist Google Drive metadata on the prescription record."""
    if not drive_file_url:
        raise ValueError("drive_file_url is required")

    prescription = Prescription.attach_drive_file(
        prescription_id,
        drive_file_id=drive_file_id or "",
        drive_file_url=drive_file_url,
    )
    if prescription is None:
        raise PrescriptionNotFoundError(f"Prescription {prescription_id} not found.")
    return prescription


def get_prescription_for_visit(visit_id: str) -> Prescription | None:
    return Prescription.find_by_visit_id(visit_id)
