from datetime import date, datetime, timezone

from pymongo import ReturnDocument

from app.extensions import get_db


def utcnow():
    return datetime.now(timezone.utc)


def to_mongo_datetime(value: date | datetime) -> datetime:
    """Convert date or datetime values to timezone-aware datetime for MongoDB."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    raise TypeError(f"Expected date or datetime, got {type(value)!r}")


def generate_sequence_id(entity_prefix: str) -> str:
    """Generate human-readable IDs like PAT-2026-0001."""
    database = get_db()
    if database is None:
        raise RuntimeError("Database is not initialized")

    year = utcnow().year
    counter_key = f"{entity_prefix}_{year}"
    doc = database.counters.find_one_and_update(
        {"_id": counter_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"{entity_prefix}-{year}-{doc['seq']:04d}"


def serialize_doc(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    result = dict(doc)
    if "_id" in result:
        result["_id"] = str(result["_id"])
    return result
