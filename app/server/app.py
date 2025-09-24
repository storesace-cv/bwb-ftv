"""Application factory for the embedded ReportBro Designer server."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "app" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "reporting" / "templates"
SAMPLES_DIR = PROJECT_ROOT / "reporting" / "samples"
DESIGNER_HTML = STATIC_DIR / "designer.html"


def _configure_logging() -> None:
    """Configure structured logging for the Flask application."""
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    try:
        log_level = getattr(logging, log_level_name)
    except AttributeError:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def _ensure_directories() -> None:
    """Ensure that runtime directories required by the server exist."""
    for directory in (STATIC_DIR, TEMPLATES_DIR, SAMPLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    _ensure_directories()
    _configure_logging()

    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
    )

    app.config.update(
        TEMPLATES_DIR=TEMPLATES_DIR,
        SAMPLES_DIR=SAMPLES_DIR,
        DESIGNER_HTML=DESIGNER_HTML,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB upload limit
    )

    from .routes_reportbro import reportbro_blueprint

    app.register_blueprint(reportbro_blueprint)

    @app.route("/designer", methods=["GET"])
    def get_designer():
        if not DESIGNER_HTML.exists():
            return "Designer UI não foi encontrado. Execute o script de bootstrap.", 500, {
                "Content-Type": "text/plain; charset=utf-8"
            }
        return send_from_directory(STATIC_DIR, "designer.html")

    return app
