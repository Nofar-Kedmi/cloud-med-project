from unittest.mock import MagicMock, patch

import pytest

from app.services.patient_service import PatientValidationError, create_patient


def test_create_patient_validation_error():
    with pytest.raises(PatientValidationError) as exc:
        create_patient({"first_name": "", "last_name": ""})
    assert "First name is required." in exc.value.errors


@patch("app.services.patient_service.Patient.create")
@patch("app.services.patient_service.validate_patient_data")
def test_create_patient_success(mock_validate, mock_create):
    mock_validate.return_value = (
        {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "male",
        },
        [],
    )
    mock_patient = MagicMock(patient_id="PAT-2026-0001")
    mock_create.return_value = mock_patient

    patient = create_patient({"first_name": "John", "last_name": "Doe", "gender": "male"})
    assert patient.patient_id == "PAT-2026-0001"
    mock_create.assert_called_once()
