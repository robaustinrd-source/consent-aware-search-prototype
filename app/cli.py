from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
SUPPORTED_SUFFIXES = {".txt", ".md", ".json", ".csv", ".html", ".htm", ".xml"}


def _loopback_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("API URL must be an http:// loopback address")
    try:
        loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        loopback = parsed.hostname.lower() == "localhost"
    if not loopback:
        raise ValueError("For safety, the CLI only connects to localhost")
    return value.rstrip("/")


def _loopback_host(value: str) -> str:
    try:
        loopback = ipaddress.ip_address(value).is_loopback
    except ValueError:
        loopback = value.lower() == "localhost"
    if not loopback:
        raise ValueError("For safety, the development server must bind to localhost")
    return value


def _headers(needs_auth: bool = False) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.getenv("SEARCH_API_TOKEN", "")
    if needs_auth:
        if not token:
            raise RuntimeError("Set SEARCH_API_TOKEN; run `python -m app.cli serve` to create a local token")
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _request(client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> Any:
    for attempt in range(3):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                await asyncio.sleep(0.25 * (2**attempt))
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == 2:
                raise
            await asyncio.sleep(0.25 * (2**attempt))
    raise RuntimeError("request retry loop exhausted")


async def cmd_search(args: argparse.Namespace) -> int:
    base = _loopback_url(args.url)
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        result = await _request(client, "POST", f"{base}/search", json={
            "query": args.query, "collections": args.collection or [], "limit": args.limit,
        })
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


async def cmd_collections(args: argparse.Namespace) -> int:
    base = _loopback_url(args.url)
    async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
        result = await _request(client, "GET", f"{base}/collections")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


async def cmd_index(args: argparse.Namespace) -> int:
    base = _loopback_url(args.url)
    ingest_root = Path(os.getenv("SEARCH_INGEST_DIR", "./data/ingest")).expanduser().resolve()
    target = Path(args.path).expanduser().resolve()
    if not target.is_file() or not target.is_relative_to(ingest_root):
        raise ValueError(f"File must be inside configured ingest directory: {ingest_root}")
    if target.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {target.suffix}")
    relative = target.relative_to(ingest_root).as_posix()
    payload = {"path": relative, "collection_id": args.collection,
               "source_id": args.source, "is_private": args.private}
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        result = await _request(client, "POST", f"{base}/index", json=payload,
                                headers=_headers(needs_auth=True))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


async def cmd_sync(args: argparse.Namespace) -> int:
    """Index all supported files under the configured ingest root with bounded concurrency."""
    base = _loopback_url(args.url)
    root = Path(os.getenv("SEARCH_INGEST_DIR", "./data/ingest")).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Ingest directory does not exist: {root}")
    paths = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)
    if not paths:
        print(json.dumps({"indexed": 0, "failed": 0, "message": "No supported files found"}))
        return 0
    semaphore = asyncio.Semaphore(args.concurrency)
    headers = _headers(needs_auth=True)
    timeout = httpx.Timeout(30)

    async def index_one(client: httpx.AsyncClient, path: Path) -> dict[str, Any]:
        relative = path.relative_to(root).as_posix()
        payload = {"path": relative, "collection_id": args.collection,
                   "source_id": args.source, "is_private": args.private}
        async with semaphore:
            try:
                result = await _request(client, "POST", f"{base}/index", json=payload, headers=headers)
                return {"path": relative, "status": "indexed", "document_id": result["document"]["document_id"]}
            except (httpx.HTTPError, RuntimeError) as exc:
                return {"path": relative, "status": "failed", "error": str(exc)}

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        outcomes = await asyncio.gather(*(index_one(client, path) for path in paths))
    failed = sum(item["status"] == "failed" for item in outcomes)
    print(json.dumps({"root": str(root), "indexed": len(outcomes) - failed,
                      "failed": failed, "files": outcomes}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


async def cmd_interactive(args: argparse.Namespace) -> int:
    base = _loopback_url(args.url)
    print("Local search terminal. Commands: /collections, /quit. No shell commands are executed.")
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        while True:
            try:
                line = await asyncio.to_thread(input, "search> ")
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            line = line.strip()
            if not line:
                continue
            if line in {"/quit", "/exit"}:
                return 0
            try:
                if line == "/collections":
                    result = await _request(client, "GET", f"{base}/collections")
                else:
                    result = await _request(client, "POST", f"{base}/search", json={"query": line})
                print(json.dumps(result, ensure_ascii=False, indent=2))
            except (httpx.HTTPError, RuntimeError) as exc:
                print(f"Request failed: {exc}", file=sys.stderr)


def cmd_serve(args: argparse.Namespace) -> int:
    host = _loopback_host(args.host)
    if not os.getenv("SEARCH_API_TOKEN"):
        token = secrets.token_urlsafe(32)
        os.environ["SEARCH_API_TOKEN"] = token
        print("Generated local admin token (save it; it is not written to disk):", file=sys.stderr)
        print(token, file=sys.stderr)
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=args.port, reload=args.reload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="local-search", description="Local-only search terminal and sync CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the API on localhost")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="Development auto-reload")
    serve.set_defaults(func=cmd_serve, synchronous=True)

    search = sub.add_parser("search", help="Search local indexed documents")
    search.add_argument("query")
    search.add_argument("--collection", action="append")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--url", default=DEFAULT_BASE_URL)
    search.set_defaults(func=cmd_search)

    collections = sub.add_parser("collections", help="List indexed local collections")
    collections.add_argument("--url", default=DEFAULT_BASE_URL)
    collections.set_defaults(func=cmd_collections)

    index = sub.add_parser("index", help="Index one file inside the ingest directory")
    index.add_argument("path")
    index.add_argument("--collection", default="default")
    index.add_argument("--source", default="local-files")
    index.add_argument("--private", action="store_true")
    index.add_argument("--url", default=DEFAULT_BASE_URL)
    index.set_defaults(func=cmd_index)

    sync = sub.add_parser("sync", help="Asynchronously index supported files with bounded concurrency")
    sync.add_argument("--collection", default="default")
    sync.add_argument("--source", default="local-files")
    sync.add_argument("--private", action="store_true")
    sync.add_argument("--concurrency", type=int, choices=range(1, 9), default=4)
    sync.add_argument("--url", default=DEFAULT_BASE_URL)
    sync.set_defaults(func=cmd_sync)

    interactive = sub.add_parser("interactive", help="Start a safe search REPL")
    interactive.add_argument("--url", default=DEFAULT_BASE_URL)
    interactive.set_defaults(func=cmd_interactive)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if getattr(args, "synchronous", False):
            return args.func(args)
        return asyncio.run(args.func(args))
    except (ValueError, RuntimeError, httpx.HTTPError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
