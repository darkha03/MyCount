import os
from pathlib import Path


class Config:
    # Secrets and security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set to True in production (Render/HTTPS). Can be overridden via env.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"

    # Resolve a single absolute DB path under the project root's `instance/` folder
    # This avoids differences when running from different working directories
    BASE_DIR = Path(__file__).resolve().parent.parent  # project root (folder that contains `backend/`)
    DEFAULT_DB_PATH = BASE_DIR / "instance" / "mycount.db"

    # Normalize DATABASE_URL for SQLAlchemy (postgres -> postgresql)
    _raw_db_url = os.environ.get("DATABASE_URL")
    if _raw_db_url and _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url or f"sqlite:///{DEFAULT_DB_PATH}"

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
