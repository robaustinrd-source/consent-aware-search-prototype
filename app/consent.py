from __future__ import annotations

from typing import Dict, List, Any, Optional
from uuid import uuid4


class ConsentManager:
    def __init__(self) -> None:
        self.requests: Dict[str, Dict[str, Any]] = {}
        self.grants: Dict[str, Dict[str, Any]] = {}

    def create_request(
        self,
        *,
        subject_id: str,
        source_id: str,
        purpose: str,
        requested_by: str,
        expires_in_hours: int = 24,
    ) -> Dict[str, Any]:
        request_id = f"request-{uuid4().hex[:10]}"
        record = {
            "request_id": request_id,
            "subject_id": subject_id,
            "source_id": source_id,
            "purpose": purpose,
            "requested_by": requested_by,
            "status": "pending",
            "expires_in_hours": expires_in_hours,
            "approved_by": None,
        }
        self.requests[request_id] = record
        return record

    def approve(self, *, request_id: str, approved_by: str) -> Dict[str, Any]:
        if request_id not in self.requests:
            raise KeyError(f"unknown consent request: {request_id}")

        record = self.requests[request_id]
        record["status"] = "approved"
        record["approved_by"] = approved_by
        self.grants[record["source_id"]] = {
            "subject_id": record["subject_id"],
            "approved_by": approved_by,
            "purpose": record["purpose"],
            "expires_in_hours": record["expires_in_hours"],
        }
        return record

    def is_authorized(self, *, subject_id: str, source_id: str, purpose: str) -> bool:
        grant = self.grants.get(source_id)
        if not grant:
            return False
        if grant.get("subject_id") != subject_id:
            return False
        if grant.get("purpose") != purpose:
            return False
        return True

    def list_requests(self) -> List[Dict[str, Any]]:
        return list(self.requests.values())
