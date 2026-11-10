from __future__ import annotations

import json
import sys
from typing import Any

from .agent_server import AgentBridge


TOOLS = [
    {"name": "list_collections", "description": "List local searchable collections.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "search_local", "description": "Search non-private local documents only; this tool makes no network requests.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "collections": {"type": "array", "items": {"type": "string"}}}, "required": ["query"], "additionalProperties": False}},
    {"name": "get_document", "description": "Retrieve a non-private local document by ID.", "inputSchema": {"type": "object", "properties": {"document_id": {"type": "string"}}, "required": ["document_id"], "additionalProperties": False}},
]


def handle(message: dict[str, Any], bridge: AgentBridge) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        result = {"protocolVersion": message.get("params", {}).get("protocolVersion", "2024-11-05"),
                  "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": "local-agent-search", "version": "0.2.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params", {})
        name, args = params.get("name"), params.get("arguments", {})
        if name == "list_collections":
            output = bridge.list_collections()
        elif name == "search_local":
            output = bridge.search_local(query=str(args.get("query", "")), collections=args.get("collections"))
        elif name == "get_document":
            output = bridge.get_document(str(args.get("document_id", "")))
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Unknown tool"}}
        result = {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}], "isError": "error" in output}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> None:
    bridge = AgentBridge()
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = handle(message, bridge)
        except Exception:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Invalid request"}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
