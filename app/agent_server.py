from __future__ import annotations

import json
import sys
from typing import Any, Dict

from .config import DATABASE_PATH, ensure_directories
from .search_engine import LocalSearchEngine
from .storage import SQLiteStore


class AgentBridge:
    """Read-only local agent surface: it never grants private access or calls the network."""
    def __init__(self) -> None:
        ensure_directories()
        self.store = SQLiteStore(DATABASE_PATH)
        self.engine = LocalSearchEngine(self.store)

    def list_collections(self) -> Dict[str, Any]:
        return {"collections": self.engine.list_collections()}

    def search_local(self, *, query: str, collections=None) -> Dict[str, Any]:
        results = self.engine.search(query=query, collections=collections)
        self.store.audit("agent_search", "local-agent", {"query_length": len(query), "result_count": len(results)})
        return {"query": query, "results": results, "offline_only": True}

    def get_document(self, document_id: str) -> Dict[str, Any]:
        doc = self.engine.get_document(document_id)
        if not doc:
            return {"error": "not-found-or-private"}
        self.store.audit("agent_document_read", "local-agent", {"document_id": document_id})
        return {"document": doc}


def _demo() -> None:
    bridge = AgentBridge()
    print(json.dumps(bridge.list_collections(), ensure_ascii=False, indent=2))
    print(json.dumps(bridge.search_local(query="consent workflow"), ensure_ascii=False, indent=2))


def _stdio_loop() -> None:
    bridge = AgentBridge()
    for raw in sys.stdin:
        try:
            payload = json.loads(raw)
            action = payload.get("action")
            if action == "list_collections":
                result = bridge.list_collections()
            elif action == "search_local":
                result = bridge.search_local(query=str(payload.get("query", "")),
                                             collections=payload.get("collections"))
            elif action == "get_document":
                result = bridge.get_document(str(payload.get("document_id", "")))
            else:
                result = {"error": "unknown-action"}
        except (json.JSONDecodeError, TypeError, ValueError):
            result = {"error": "invalid-request"}
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Offline local search agent bridge")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    _demo() if args.demo else _stdio_loop()
