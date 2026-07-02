from datetime import date, datetime, timezone

from app.utils.helpers import to_mongo_datetime
from app.utils.validators import validate_patient_data


def test_to_mongo_datetime_from_date():
    result = to_mongo_datetime(date(1975, 2, 1))
    assert result == datetime(1975, 2, 1, tzinfo=timezone.utc)


def test_validate_patient_data_stores_datetime_for_dob():
    cleaned, errors = validate_patient_data(
        {
            "first_name": "Jane",
            "last_name": "Doe",
            "id_number": "123456789",
            "date_of_birth": "1975-02-01",
            "gender": "female",
        }
    )
    assert errors == []
    assert cleaned["date_of_birth"] == datetime(1975, 2, 1, tzinfo=timezone.utc)
    assert isinstance(cleaned["date_of_birth"], datetime)
