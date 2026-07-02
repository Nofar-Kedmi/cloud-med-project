import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app import create_app
from app.db_indexes import ensure_indexes
from app.extensions import require_db
from app.models.user import User


DEFAULT_USERS = [
    {
        "email": "admin@medical.local",
        "password": "admin123",
        "role": "admin",
        "full_name": "System Admin",
    },
    {
        "email": "doctor@medical.local",
        "password": "doctor123",
        "role": "doctor",
        "full_name": "Dr. Jane Smith",
    },
    {
        "email": "pharmacist@medical.local",
        "password": "pharmacist123",
        "role": "pharmacist",
        "full_name": "Alex Pharmacist",
    },
]


def main():
    app = create_app()

    with app.app_context():
        require_db()
        ensure_indexes()

        print(f"Connected to database: {app.config['MONGODB_DB_NAME']}")

        for entry in DEFAULT_USERS:
            existing = User.find_by_email(entry["email"])
            if existing:
                print(f"Skipped existing user: {entry['email']}")
                continue
            User.create(
                email=entry["email"],
                password=entry["password"],
                role=entry["role"],
                full_name=entry["full_name"],
            )
            print(f"Created user: {entry['email']} ({entry['role']})")

        print("\nSeed complete. Default credentials:")
        for entry in DEFAULT_USERS:
            print(f"  {entry['role']:11} {entry['email']} / {entry['password']}")


if __name__ == "__main__":
    main()
