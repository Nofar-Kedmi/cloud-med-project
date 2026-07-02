from bson import ObjectId
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import get_db
from app.utils.helpers import serialize_doc, utcnow


class User(UserMixin):
    def __init__(self, data: dict):
        self._id = data["_id"]
        self.email = data["email"]
        self.password_hash = data["password_hash"]
        self.role = data["role"]
        self.full_name = data.get("full_name", "")
        self.created_at = data.get("created_at")

    def get_id(self):
        return str(self._id)

    @staticmethod
    def _collection():
        database = get_db()
        if database is None:
            raise RuntimeError("Database is not initialized")
        return database.users

    @classmethod
    def find_by_email(cls, email: str):
        doc = cls._collection().find_one({"email": email.lower()})
        return cls(doc) if doc else None

    @classmethod
    def find_by_id(cls, user_id: str):
        try:
            doc = cls._collection().find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
        return cls(doc) if doc else None

    @classmethod
    def create(cls, email: str, password: str, role: str, full_name: str):
        doc = {
            "email": email.lower(),
            "password_hash": generate_password_hash(password),
            "role": role,
            "full_name": full_name,
            "created_at": utcnow(),
        }
        result = cls._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return serialize_doc(
            {
                "_id": self._id,
                "email": self.email,
                "role": self.role,
                "full_name": self.full_name,
                "created_at": self.created_at,
            }
        )
