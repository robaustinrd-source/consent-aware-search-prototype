from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WebhookEvent:
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class WebhookManager:
    """Local webhook manager for async, signed event delivery."""

    def __init__(self, signing_secret: Optional[str] = None) -> None:
        self.signing_secret = signing_secret
        self.events: List[WebhookEvent] = []

    def register(self, event_type: str, payload: Dict[str, Any]) -> WebhookEvent:
        event = WebhookEvent(event_type=event_type, payload=payload)
        if self.signing_secret:
            body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            event.signature = hmac.new(self.signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        self.events.append(event)
        return event

    def validate(self, event: WebhookEvent, signature: str) -> bool:
        if not self.signing_secret:
            return True
        return hmac.compare_digest(event.signature or "", signature)

    def list_events(self, event_type: Optional[str] = None) -> List[WebhookEvent]:
        if event_type is None:
            return list(self.events)
        return [event for event in self.events if event.event_type == event_type]


# Actual webhook dispatch requires destination validation, retries, and secret rotation.
