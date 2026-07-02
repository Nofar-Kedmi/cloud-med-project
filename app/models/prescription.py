from pymongo import ReturnDocument

from app.extensions import get_db
from app.utils.helpers import generate_sequence_id, serialize_doc, utcnow


class Prescription:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.prescription_id = data["prescription_id"]
        self.visit_id = data.get("visit_id", "")
        self.patient_id = data.get("patient_id", "")
        self.doctor_id = data.get("doctor_id", "")
        self.medication_name = data.get("medication_name", "")
        self.dosage = data.get("dosage", "")
        self.frequency = data.get("frequency", "")
        self.instructions = data.get("instructions", "")
        self.medications = data.get("medications", [])
        self.general_instructions = data.get("general_instructions", "")
        self.status = data.get("status", "open")
        self.drive_file_id = data.get("drive_file_id", "")
        self.drive_file_url = data.get("drive_file_url", "")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    @staticmethod
    def _collection():
        database = get_db()
        if database is None:
            raise RuntimeError("Database is not initialized")
        return database.prescriptions

    @classmethod
    def create(cls, data: dict):
        now = utcnow()
        doc = {
            "prescription_id": generate_sequence_id("RX"),
            "visit_id": data["visit_id"],
            "patient_id": data.get("patient_id", ""),
            "doctor_id": data.get("doctor_id", ""),
            "medication_name": data.get("medication_name", ""),
            "dosage": data.get("dosage", ""),
            "frequency": data.get("frequency", ""),
            "instructions": data.get("instructions", ""),
            "status": data.get("status", "open"),
            "created_at": now,
            "updated_at": now,
        }
        result = cls._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def find_by_visit_id(cls, visit_id: str):
        doc = cls._collection().find_one({"visit_id": visit_id})
        return cls(doc) if doc else None

    @classmethod
    def find_open_by_patient_id(cls, patient_id: str):
        cursor = cls._collection().find({"patient_id": patient_id, "status": "open"})
        return [cls(doc) for doc in cursor]

    @classmethod
    def find_by_prescription_id(cls, prescription_id: str):
        doc = cls._collection().find_one({"prescription_id": prescription_id})
        return cls(doc) if doc else None

    @classmethod
    def update_status(cls, prescription_id: str, status: str):
        result = cls._collection().find_one_and_update(
            {"prescription_id": prescription_id},
            {"$set": {"status": status, "updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return cls(result) if result else None

    @classmethod
    def attach_drive_file(
        cls,
        prescription_id: str,
        *,
        drive_file_id: str,
        drive_file_url: str,
    ):
        result = cls._collection().find_one_and_update(
            {"prescription_id": prescription_id},
            {
                "$set": {
                    "drive_file_id": drive_file_id,
                    "drive_file_url": drive_file_url,
                    "updated_at": utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return cls(result) if result else None

    def to_dict(self):
        return serialize_doc(
            {
                "_id": self._id,
                "prescription_id": self.prescription_id,
                "visit_id": self.visit_id,
                "patient_id": self.patient_id,
                "doctor_id": self.doctor_id,
                "medication_name": self.medication_name,
                "dosage": self.dosage,
                "frequency": self.frequency,
                "instructions": self.instructions,
                "status": self.status,
                "drive_file_id": self.drive_file_id,
                "drive_file_url": self.drive_file_url,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )
