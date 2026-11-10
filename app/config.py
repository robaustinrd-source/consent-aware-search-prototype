from __future__ import annotations

import os
import secrets
from pathlib import Path


DATA_DIR = Path(os.getenv("SEARCH_DATA_DIR", "./data")).expanduser().resolve()
INGEST_DIR = Path(os.getenv("SEARCH_INGEST_DIR", str(DATA_DIR / "ingest"))).expanduser().resolve()
DATABASE_PATH = Path(os.getenv("SEARCH_DATABASE_PATH", str(DATA_DIR / "search.sqlite3"))).expanduser().resolve()
MAX_FILE_BYTES = int(os.getenv("SEARCH_MAX_FILE_BYTES", str(10 * 1024 * 1024)))
API_TOKEN = os.getenv("SEARCH_API_TOKEN", "")


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INGEST_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def create_local_token() -> str:
    """Create a one-time token for local development; never expose this service publicly."""
    return secrets.token_urlsafe(32)
