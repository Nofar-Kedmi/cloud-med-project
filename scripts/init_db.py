import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app import create_app
from app.db_indexes import ensure_indexes
from app.extensions import require_db


def main():
    app = create_app()

    with app.app_context():
        require_db()
        ensure_indexes()
        print(f"Database indexes ensured for '{app.config['MONGODB_DB_NAME']}'.")


if __name__ == "__main__":
    main()
