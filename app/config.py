import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    MONGODB_URI = os.environ.get("MONGODB_URI", "")
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "medical_system")
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    GOOGLE_DRIVE_CREDENTIALS_FILE = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_FILE", "")
    GOOGLE_DRIVE_TOKEN_FILE = os.environ.get("GOOGLE_DRIVE_TOKEN_FILE", "")
    GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_VISION_CREDENTIALS_FILE = os.environ.get("GOOGLE_VISION_CREDENTIALS_FILE", "")
    TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
    OCR_SERVICE_URL = os.environ.get("OCR_SERVICE_URL", "http://localhost:5001")
    MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    MEDICAL_CENTER_NAME = os.environ.get("MEDICAL_CENTER_NAME", "Medical Center")
    DOCTOR_LICENSE_NUMBER = os.environ.get("DOCTOR_LICENSE_NUMBER", "")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    MONGODB_DB_NAME = "medical_system_test"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
