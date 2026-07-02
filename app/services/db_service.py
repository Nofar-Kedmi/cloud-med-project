"""MongoDB connection shared by application services."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
print(f"DEBUG_INFO: MONGO_URI value is: {uri}")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or os.getenv("MONGODB_DB_NAME")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI or MONGODB_URI is not configured in .env")
if not MONGO_DB_NAME:
    raise RuntimeError("MONGO_DB_NAME or MONGODB_DB_NAME is not configured in .env")

mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client[MONGO_DB_NAME]
prescriptions_collection = db["prescriptions"]
patients_collection = db["patients"]
ocr_results_collection = db["ocr_results"]
