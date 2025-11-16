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
    BASE_DIR = (
        Path(__file__).resolve().parent.parent
    )  # project root (folder that contains `backend/`)
    DEFAULT_DB_PATH = BASE_DIR / "instance" / "mycount.db"

    # Normalize DATABASE_URL for SQLAlchemy and prefer appropriate drivers
    _raw_db_url = os.environ.get("DATABASE_URL")
    if _raw_db_url:
        # PythonAnywhere MySQL: mysql:// -> mysql+mysqldb://
        if _raw_db_url.startswith("mysql://"):
            _raw_db_url = _raw_db_url.replace("mysql://", "mysql+mysqldb://", 1)
        # Render/Heroku Postgres: postgres:// -> postgresql+psycopg://
        elif _raw_db_url.startswith("postgres://"):
            _raw_db_url = _raw_db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif _raw_db_url.startswith("postgresql://"):
            _raw_db_url = _raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url or f"sqlite:///{DEFAULT_DB_PATH}"

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    # Content Security Policy defaults - can be overridden via env vars or subclassing
    # Provide common CDNs used by Bootstrap/Chart.js; override in production for tighter policy
    CSP_DEFAULT_SRC = ["'self'"]
    CSP_SCRIPT_SRC = [
        "'self'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net",
        "https://unpkg.com",
    ]
    CSP_STYLE_SRC = [
        "'self'",
        "https://cdn.jsdelivr.net",
        "https://fonts.googleapis.com",
        "'unsafe-inline'",
    ]
    CSP_IMG_SRC = ["'self'", "data:"]
    CSP_FONT_SRC = ["'self'", "https://cdn.jsdelivr.net", "https://fonts.gstatic.com", "data:"]
    CSP_CONNECT_SRC = ["'self'", "https://api.github.com", "https://cdn.jsdelivr.net"]
