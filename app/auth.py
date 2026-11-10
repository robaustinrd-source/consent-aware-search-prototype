from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


@dataclass
class UserSession:
    user_id: str
    token: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    role: str = "local-user"


class AuthProvider:
    """Small local scaffold for trusted environments only."""

    def __init__(self) -> None:
        self.sessions: Dict[str, UserSession] = {}

    def create_session(self, user_id: str, role: str = "local-user", ttl_hours: int = 1) -> UserSession:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        session = UserSession(user_id=user_id, token=token, expires_at=expires_at, role=role)
        self.sessions[token] = session
        return session

    def validate(self, token: str) -> Optional[UserSession]:
        session = self.sessions.get(token)
        if session is None:
            return None
        if session.expires_at <= datetime.now(timezone.utc):
            self.sessions.pop(token, None)
            return None
        return session

    def revoke(self, token: str) -> bool:
        return self.sessions.pop(token, None) is not None


# Replace this with a proper identity provider or delegated auth system before production use.
