from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConnectorStatus:
    connector_id: str
    name: str
    status: str
    network: bool = False
    requires_consent: bool = True
    requires_api_key: bool = False
    notes: str = ""


@dataclass
class ProviderConfig:
    connector_id: str
    name: str
    enabled: bool = False
    priority: int = 100
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 15
    allow_private_results: bool = False
    consent_required: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)


class ConnectorAdapter:
    """Base adapter for provider-bound search connectors."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_id=self.config.connector_id,
            name=self.config.name,
            status="not_configured" if not self.config.enabled else "ready",
            network=True,
            requires_consent=self.config.consent_required,
            requires_api_key=self.config.api_key is None and self.config.enabled,
            notes="Use only provider-approved APIs or user-authorized integrations.",
        )

    async def search(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        raise NotImplementedError("Connector adapter must implement search().")


class ConnectorRegistry:
    """Allowlisted registry of approved external connectors."""

    def __init__(self) -> None:
        self.connectors: Dict[str, ConnectorAdapter] = {}

    def register(self, adapter: ConnectorAdapter) -> None:
        self.connectors[adapter.config.connector_id] = adapter

    def status(self) -> List[ConnectorStatus]:
        return [self.connectors[name].status() for name in sorted(self.connectors)]

    def by_id(self, connector_id: str) -> Optional[ConnectorAdapter]:
        return self.connectors.get(connector_id)


DEFAULT_PROVIDER_CONFS: List[ProviderConfig] = [
    ProviderConfig("google", "Google", enabled=False, priority=10, consent_required=True),
    ProviderConfig("bing", "Bing", enabled=False, priority=20, consent_required=True),
    ProviderConfig("duckduckgo", "DuckDuckGo", enabled=False, priority=30, consent_required=True),
    ProviderConfig("yahoo", "Yahoo", enabled=False, priority=40, consent_required=True),
    ProviderConfig("firefox", "Firefox", enabled=False, priority=50, consent_required=False),
    ProviderConfig("onion", "Tor Onion", enabled=False, priority=60, consent_required=True),
    ProviderConfig("private_dataset", "Private Dataset", enabled=False, priority=70, consent_required=True),
]

# No live provider calls are made here. The registry is a scaffold for explicit allowlisting.
