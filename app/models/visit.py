from app.extensions import get_db
from app.utils.helpers import generate_sequence_id, serialize_doc, utcnow


class Visit:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.visit_id = data["visit_id"]
        self.patient_id = data["patient_id"]
        self.doctor_id = data["doctor_id"]
        self.visit_date = data.get("visit_date")
        self.symptoms = data.get("symptoms", data.get("chief_complaint", ""))
        self.diagnosis = data.get("diagnosis", "")
        self.vitals = data.get("vitals", {})
        self.external_refs = data.get("external_refs", {})
        self.created_at = data.get("created_at")

    @staticmethod
    def _collection():
        database = get_db()
        if database is None:
            raise RuntimeError("Database is not initialized")
        return database.visits

    @classmethod
    def create(cls, data: dict):
        doc = {
            "visit_id": generate_sequence_id("VIS"),
            "patient_id": data["patient_id"],
            "doctor_id": data["doctor_id"],
            "visit_date": data["visit_date"],
            "symptoms": data.get("symptoms", ""),
            "diagnosis": data.get("diagnosis", ""),
            "vitals": data.get("vitals", {}),
            "external_refs": data.get("external_refs", {}),
            "created_at": utcnow(),
        }
        result = cls._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def find_by_id(cls, visit_id):
        doc = cls._collection().find_one({"visit_id": visit_id})
        return cls(doc) if doc else None

    @classmethod
    def find_by_visit_id(cls, visit_id: str):
        return cls.find_by_id(visit_id)

    @classmethod
    def find_by_patient_id(cls, patient_id: str):
        cursor = cls._collection().find({"patient_id": patient_id}).sort("visit_date", -1)
        return [cls(doc) for doc in cursor]

    @classmethod
    def find_by_doctor_id(cls, doctor_id: str, limit: int = 10):
        cursor = (
            cls._collection()
            .find({"doctor_id": doctor_id})
            .sort("visit_date", -1)
            .limit(limit)
        )
        return [cls(doc) for doc in cursor]

    @classmethod
    def count_by_doctor(cls, doctor_id: str) -> int:
        return cls._collection().count_documents({"doctor_id": doctor_id})

    def to_dict(self):
        return serialize_doc(
            {
                "_id": self._id,
                "visit_id": self.visit_id,
                "patient_id": self.patient_id,
                "doctor_id": self.doctor_id,
                "visit_date": self.visit_date,
                "symptoms": self.symptoms,
                "diagnosis": self.diagnosis,
                "vitals": self.vitals,
                "external_refs": self.external_refs,
                "created_at": self.created_at,
            }
        )
