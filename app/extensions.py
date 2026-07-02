import logging

from flask_login import LoginManager
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

mongo_client = None
db = None
login_manager = LoginManager()


def init_extensions(app):
    global mongo_client, db

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    uri = app.config.get("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI is not set; database features are disabled.")
        return

    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db_name = app.config["MONGODB_DB_NAME"]
    db = mongo_client[db_name]

    try:
        mongo_client.admin.command("ping")
        logger.info("Connected to MongoDB Atlas database '%s'.", db_name)
    except ServerSelectionTimeoutError as exc:
        logger.error("Failed to connect to MongoDB: %s", exc)
        raise

    from app.db_indexes import ensure_indexes

    ensure_indexes()


def get_db():
    return db


def require_db():
    if db is None:
        raise RuntimeError(
            "Database is not initialized. Set MONGODB_URI in your .env file "
            "and ensure load_dotenv() runs before create_app()."
        )
    return db


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.find_by_id(user_id)
