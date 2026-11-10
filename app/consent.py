from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .storage import SQLiteStore


class ConsentManager:
    """Local owner-controlled, purpose-limited access grants.

    These grants are an application control, not identity verification or a substitute
    for legal consent/provider authorization.
    """

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def grant_local_access(self, *, source_id: str, collection_id: str,
                           purpose: str, granted_by: str, expires_in_hours: int = 24) -> Dict[str, Any]:
        if not source_id.strip() or not collection_id.strip() or not purpose.strip():
            raise ValueError("source_id, collection_id, and purpose are required")
        if not 1 <= expires_in_hours <= 24 * 30:
            raise ValueError("grant duration must be between 1 hour and 30 days")
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)).isoformat()
        grant = self.store.add_grant(source_id=source_id, collection_id=collection_id,
                                     purpose=purpose.strip(), granted_by=granted_by,
                                     expires_at=expires_at)
        self.store.audit("local_access_granted", granted_by,
                         {"grant_id": grant["grant_id"], "source_id": source_id,
                          "collection_id": collection_id, "purpose": purpose.strip()})
        return grant

    def authorize(self, *, grant_id: str, purpose: str) -> Dict[str, Any] | None:
        grant = self.store.get_active_grant(grant_id)
        if not grant or grant["purpose"] != purpose:
            return None
        return grant

    def revoke(self, grant_id: str, actor: str) -> bool:
        revoked = self.store.revoke_grant(grant_id)
        self.store.audit("local_access_revoked" if revoked else "local_access_revoke_failed",
                         actor, {"grant_id": grant_id})
        return revoked
