from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4


class SQLiteStore:
    """Small durable local store. Keep the database on a trusted local disk."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    is_private INTEGER NOT NULL DEFAULT 0,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(collection_id, content_hash)
                );
                CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_id);
                CREATE TABLE IF NOT EXISTS access_grants (
                    grant_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    def save_document(self, *, title: str, text: str, collection_id: str,
                      source_id: str, is_private: bool) -> Dict[str, Any]:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        created_at = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            row = db.execute(
                "SELECT document_id FROM documents WHERE collection_id=? AND content_hash=?",
                (collection_id, content_hash),
            ).fetchone()
            if row:
                db.execute("UPDATE documents SET title=?, source_id=?, is_private=? WHERE document_id=?",
                           (title, source_id, int(is_private), row["document_id"]))
                document_id = row["document_id"]
            else:
                document_id = f"doc-{uuid4().hex}"
                db.execute("""INSERT INTO documents
                    (document_id,title,text,collection_id,source_id,is_private,content_hash,created_at)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (document_id, title, text, collection_id, source_id, int(is_private), content_hash, created_at))
        return {"document_id": document_id, "title": title, "collection_id": collection_id,
                "source_id": source_id, "is_private": is_private, "created_at": created_at}

    def documents(self, collections: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        with self.connect() as db:
            if collections:
                placeholders = ",".join("?" for _ in collections)
                rows = db.execute(f"SELECT * FROM documents WHERE collection_id IN ({placeholders})", collections).fetchall()
            else:
                rows = db.execute("SELECT * FROM documents").fetchall()
        return [dict(row) for row in rows]

    def list_collections(self) -> List[str]:
        with self.connect() as db:
            rows = db.execute("SELECT DISTINCT collection_id FROM documents ORDER BY collection_id").fetchall()
        return [row[0] for row in rows]

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM documents WHERE document_id=?", (document_id,)).fetchone()
        return dict(row) if row else None

    def add_grant(self, *, source_id: str, collection_id: str, purpose: str,
                  granted_by: str, expires_at: str) -> Dict[str, Any]:
        grant = {"grant_id": f"grant-{uuid4().hex}", "source_id": source_id,
                 "collection_id": collection_id, "purpose": purpose,
                 "granted_by": granted_by, "created_at": datetime.now(timezone.utc).isoformat(),
                 "expires_at": expires_at, "revoked_at": None}
        with self.connect() as db:
            db.execute("""INSERT INTO access_grants
                (grant_id,source_id,collection_id,purpose,granted_by,created_at,expires_at,revoked_at)
                VALUES (:grant_id,:source_id,:collection_id,:purpose,:granted_by,:created_at,:expires_at,:revoked_at)""", grant)
        return grant

    def get_active_grant(self, grant_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM access_grants WHERE grant_id=?", (grant_id,)).fetchone()
        if not row:
            return None
        grant = dict(row)
        if grant["revoked_at"] or datetime.fromisoformat(grant["expires_at"]) <= datetime.now(timezone.utc):
            return None
        return grant

    def revoke_grant(self, grant_id: str) -> bool:
        with self.connect() as db:
            cursor = db.execute("UPDATE access_grants SET revoked_at=? WHERE grant_id=? AND revoked_at IS NULL",
                                (datetime.now(timezone.utc).isoformat(), grant_id))
        return cursor.rowcount > 0

    def audit(self, event_type: str, actor: str, details: Dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute("INSERT INTO audit_events VALUES (?,?,?,?,?)",
                       (f"evt-{uuid4().hex}", event_type, actor,
                        json.dumps(details, ensure_ascii=False, sort_keys=True),
                        datetime.now(timezone.utc).isoformat()))

    def recent_audit(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["details"] = json.loads(item.pop("details_json"))
            result.append(item)
        return result
