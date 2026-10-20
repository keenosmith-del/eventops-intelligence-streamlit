import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)


def setting(key, default=""):
    return os.getenv(key, default)


def database_url():
    url = setting("EVENTOPS_DATABASE_URL", f"sqlite:///{ROOT / 'storage/eventops.db'}")
    if not url.startswith(("sqlite:", "postgresql+psycopg:")):
        raise ValueError("Use a dedicated SQLite or postgresql+psycopg database URL.")
    return url
