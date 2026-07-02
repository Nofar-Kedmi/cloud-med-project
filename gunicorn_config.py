"""Gunicorn configuration for production deployment (Render, Docker, etc.)."""

from __future__ import annotations

import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(
    os.getenv(
        "WEB_CONCURRENCY",
        max(2, multiprocessing.cpu_count() // 2 + 1),
    )
)
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
preload_app = os.getenv("GUNICORN_PRELOAD", "true").lower() in ("1", "true", "yes")
