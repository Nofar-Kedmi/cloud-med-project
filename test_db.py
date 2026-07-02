import os
from pymongo import MongoClient

# ננסה לשלוף את משתני הסביבה
uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGO_DB_NAME")

print(f"Testing connection...")
print(f"MONGO_URI found: {'Yes' if uri else 'No'}")
print(f"MONGO_DB_NAME found: {'Yes' if db_name else 'No'}")

if uri:
    try:
        client = MongoClient(uri)
        # ננסה לבצע פעולה פשוטה כדי לבדוק חיבור
        client.admin.command('ping')
        print("Success: Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Error: Could not connect to MongoDB. Details: {e}")
else:
    print("Error: MONGO_URI is missing in the environment.")