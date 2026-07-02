import os

from flask import Flask

from app.config import config
from app.extensions import init_extensions


def apply_env_overrides(app):
    """Refresh config from os.environ (supports load_dotenv before create_app)."""
    env_map = {
        "SECRET_KEY": str,
        "MONGO_URI": str,
        "MONGO_DB_NAME": str,
        "MONGODB_URI": str,
        "MONGODB_DB_NAME": str,
        "GOOGLE_APPLICATION_CREDENTIALS": str,
        "GOOGLE_DRIVE_CREDENTIALS_FILE": str,
        "GOOGLE_DRIVE_TOKEN_FILE": str,
        "GOOGLE_DRIVE_FOLDER_ID": str,
        "GOOGLE_CLOUD_PROJECT": str,
        "GOOGLE_VISION_CREDENTIALS_FILE": str,
        "TAVILY_API_KEY": str,
        "OCR_SERVICE_URL": str,
        "MAX_UPLOAD_SIZE_MB": int,
        "MEDICAL_CENTER_NAME": str,
        "DOCTOR_LICENSE_NUMBER": str,
        "FLASK_DEBUG": str,
    }
    for key, caster in env_map.items():
        if key in os.environ:
            app.config[key] = caster(os.environ[key])
    app.config["MAX_CONTENT_LENGTH"] = app.config["MAX_UPLOAD_SIZE_MB"] * 1024 * 1024


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    if config_name not in config:
        config_name = "development"

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    apply_env_overrides(app)

    init_extensions(app)
    register_blueprints(app)
    register_routes(app)

    return app


def register_blueprints(app):
    from app.controllers.admin_controller import admin_bp
    from app.controllers.api_controller import api_bp
    from app.controllers.auth_controller import auth_bp
    from app.controllers.doctor_controller import doctor_bp

    from app.controllers.pharmacist_controller import pharmacist_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(pharmacist_bp)


def register_routes(app):
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.patients_list"))
            if current_user.role == "doctor":
                return redirect(url_for("doctor.dashboard"))
            if current_user.role == "pharmacist":
                return redirect(url_for("pharmacist.search"))
            return redirect(url_for("auth.welcome"))
        return redirect(url_for("auth.login"))
