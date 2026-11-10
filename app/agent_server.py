from __future__ import annotations

import json
import sys
from typing import Any, Dict

from .consent import ConsentManager
from .search_engine import LocalSearchEngine


class AgentBridge:
    def __init__(self) -> None:
        self.engine = LocalSearchEngine()
        self.consent = ConsentManager()

    def list_collections(self) -> Dict[str, Any]:
        return {"collections": list(self.engine.collection_map.keys())}

    def search_local(self, *, query: str, collections=None, include_private: bool = False) -> Dict[str, Any]:
        results = self.engine.search(
            query=query,
            collections=collections,
            include_private=include_private,
        )
        return {"query": query, "results": results}

    def request_consent(self, *, subject_id: str, source_id: str, purpose: str, requested_by: str) -> Dict[str, Any]:
        return self.consent.create_request(
            subject_id=subject_id,
            source_id=source_id,
            purpose=purpose,
            requested_by=requested_by,
        )

    def approve_consent(self, *, request_id: str, approved_by: str) -> Dict[str, Any]:
        return self.consent.approve(request_id=request_id, approved_by=approved_by)


def _demo() -> None:
    bridge = AgentBridge()
    bridge.engine.index_document(
        title="Local knowledge",
        text="This system uses consent-aware workflows for safe search. It can index local files for offline AI agents.",
        collection_id="default",
        source_id="local-default",
        consent_required=False,
    )
    print(json.dumps(bridge.search_local(query="consent workflow"), indent=2))


def _stdio_loop() -> None:
    bridge = AgentBridge()
    for raw in sys.stdin:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            print(json.dumps({"error": "invalid-json"}))
            continue

        action = payload.get("action")
        if action == "list_collections":
            response = bridge.list_collections()
        elif action == "search_local":
            response = bridge.search_local(
                query=payload.get("query", ""),
                collections=payload.get("collections"),
                include_private=bool(payload.get("include_private", False)),
            )
        elif action == "request_consent":
            response = bridge.request_consent(
                subject_id=payload["subject_id"],
                source_id=payload["source_id"],
                purpose=payload["purpose"],
                requested_by=payload["requested_by"],
            )
        elif action == "approve_consent":
            response = bridge.approve_consent(
                request_id=payload["request_id"],
                approved_by=payload["approved_by"],
            )
        else:
            response = {"error": f"unknown-action:{action}"}
        print(json.dumps(response))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        _demo()
    else:
        _stdio_loop()
