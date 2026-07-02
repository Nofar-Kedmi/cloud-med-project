from app.extensions import get_db
from app.utils.helpers import serialize_doc, utcnow


class OCRResult:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.prescription_id = data["prescription_id"]
        self.pharmacist_id = data.get("pharmacist_id", "")
        self.image_filename = data.get("image_filename", "")
        self.raw_text = data.get("raw_text", "")
        self.decoded_at = data.get("decoded_at")

    @staticmethod
    def _collection():
        database = get_db()
        if database is None:
            raise RuntimeError("Database is not initialized")
        return database.ocr_results

    @classmethod
    def create(cls, data: dict):
        doc = {**data, "decoded_at": utcnow()}
        result = cls._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def find_by_prescription_id(cls, prescription_id: str):
        cursor = cls._collection().find({"prescription_id": prescription_id}).sort("decoded_at", -1)
        return [cls(doc) for doc in cursor]

    def to_dict(self):
        return serialize_doc(self.__dict__)
