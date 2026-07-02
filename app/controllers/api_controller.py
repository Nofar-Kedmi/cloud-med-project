from flask import Blueprint, jsonify

from app.extensions import get_db

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
def health():
    payload = {"status": "ok"}
    if get_db() is not None:
        payload["database"] = "connected"
    else:
        payload["database"] = "not_configured"
    return jsonify(payload), 200
