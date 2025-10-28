import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret")
    # Resolve a single absolute DB path under the project root's `instance/` folder
    # This avoids differences when running from different working directories
    BASE_DIR = Path(__file__).resolve().parent.parent  # project root (folder that contains `backend/`)
    DEFAULT_DB_PATH = BASE_DIR / "instance" / "mycount.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
