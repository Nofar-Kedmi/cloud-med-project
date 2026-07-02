from app.extensions import get_db


def ensure_indexes():
    database = get_db()
    if database is None:
        return

    database.users.create_index("email", unique=True)

    database.patients.create_index("patient_id", unique=True)
    database.patients.create_index([("last_name", 1), ("first_name", 1)])
    database.patients.create_index([("first_name", "text"), ("last_name", "text")])

    database.visits.create_index("visit_id", unique=True)
    database.visits.create_index([("patient_id", 1), ("visit_date", -1)])
    database.visits.create_index([("doctor_id", 1), ("visit_date", -1)])

    database.prescriptions.create_index("prescription_id", unique=True)
    database.prescriptions.create_index([("patient_id", 1), ("status", 1)])
    database.prescriptions.create_index([("doctor_id", 1), ("created_at", -1)])

    database.ocr_results.create_index("prescription_id")
    database.ocr_results.create_index([("decoded_at", -1)])
