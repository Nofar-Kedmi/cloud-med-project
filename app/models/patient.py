from pymongo import ReturnDocument

from app.extensions import get_db
from app.utils.helpers import generate_sequence_id, serialize_doc, utcnow


class Patient:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.patient_id = data["patient_id"]
        self.id_number = data.get("id_number", "")
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.date_of_birth = data.get("date_of_birth")
        self.gender = data.get("gender", "")
        self.phone = data.get("phone", "")
        self.email = data.get("email", "")
        self.address = data.get("address", {})
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def _collection():
        database = get_db()
        if database is None:
            raise RuntimeError("Database is not initialized")
        return database.patients

    @classmethod
    def create(cls, data: dict):
        now = utcnow()
        doc = {
            "patient_id": generate_sequence_id("PAT"),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "id_number": data.get("id_number", ""),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "address": data.get("address", {}),
            "created_at": now,
            "updated_at": now,
        }
        result = cls._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def find_by_patient_id(cls, patient_id: str):
        doc = cls._collection().find_one({"patient_id": patient_id})
        return cls(doc) if doc else None

    @classmethod
    def find_by_patient_ids(cls, patient_ids: list[str]) -> dict[str, "Patient"]:
        unique_ids = [patient_id for patient_id in dict.fromkeys(patient_ids) if patient_id]
        if not unique_ids:
            return {}

        cursor = cls._collection().find({"patient_id": {"$in": unique_ids}})
        return {doc["patient_id"]: cls(doc) for doc in cursor}

    @classmethod
    def find_all(cls, page: int = 1, per_page: int = 20):
        skip = (page - 1) * per_page
        cursor = (
            cls._collection()
            .find()
            .sort("last_name", 1)
            .skip(skip)
            .limit(per_page)
        )
        return [cls(doc) for doc in cursor]

    @classmethod
    def find_all_sorted(cls):
        cursor = cls._collection().find().sort([("last_name", 1), ("first_name", 1)])
        return [cls(doc) for doc in cursor]

    @classmethod
    def count(cls) -> int:
        return cls._collection().count_documents({})

    @classmethod
    def search(cls, query: str, limit: int = 20):
        cursor = cls._collection().find({
            "$or": [
                {"patient_id": {"$regex": query, "$options": "i"}},
                {"id_number": {"$regex": query, "$options": "i"}},
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}}
            ]
        }).limit(limit)
        return [cls(doc) for doc in cursor]

    @classmethod
    def update(cls, patient_id: str, data: dict):
        data["updated_at"] = utcnow()
        result = cls._collection().find_one_and_update(
            {"patient_id": patient_id},
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )
        return cls(result) if result else None

    def to_dict(self):
        return serialize_doc(
            {
                "_id": self._id,
                "patient_id": self.patient_id,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "id_number": self.id_number,
                "date_of_birth": self.date_of_birth,
                "gender": self.gender,
                "phone": self.phone,
                "email": self.email,
                "address": self.address,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )
        