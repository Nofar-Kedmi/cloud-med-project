"""MongoDB connection shared by application services."""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# 1. הגדרת נתיב וטעינת .env רק אם הוא קיים (לא יקרוס ב-Render)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
dotenv_path = PROJECT_ROOT / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print("DEBUG: Loaded local .env file")
else:
    print("DEBUG: No .env file found, relying on system environment variables")

# 2. שליפת משתני הסביבה (מה-Environment של Render או מה-.env)
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or os.getenv("MONGODB_DB_NAME")

# 3. הדפסת אבחון ל-Logs של Render
print(f"DEBUG: MONGO_URI value is: {'Present' if MONGO_URI else 'MISSING'}")
print(f"DEBUG: MONGO_DB_NAME value is: {'Present' if MONGO_DB_NAME else 'MISSING'}")

# 4. בדיקת שגיאות
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not configured! Check Render Environment settings.")
if not MONGO_DB_NAME:
    raise RuntimeError("MONGO_DB_NAME is not configured! Check Render Environment settings.")

# 5. אתחול הלקוח
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # וידוא שהחיבור אכן עובד (ping)
    mongo_client.admin.command('ping')
    print("DEBUG: MongoDB connection successful!")
except Exception as e:
    print(f"DEBUG: MongoDB connection failed: {e}")
    raise

db = mongo_client[MONGO_DB_NAME]

# הגדרת ה-Collections
prescriptions_collection = db["prescriptions"]
patients_collection = db["patients"]
ocr_results_collection = db["ocr_results"]