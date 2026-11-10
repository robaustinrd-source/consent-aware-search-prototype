from __future__ import annotations

import hmac
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .consent import ConsentManager
from .indexer import LocalIndexer
from .models import (IndexFilePayload, LocalAccessGrantPayload, ProfilePayload,
                     RevokeGrantPayload, SearchRequest)
from .search_engine import LocalSearchEngine
from .storage import SQLiteStore

config.ensure_directories()
store = SQLiteStore(config.DATABASE_PATH)
engine = LocalSearchEngine(store)
consent = ConsentManager(store)
indexer = LocalIndexer(config.INGEST_DIR, config.MAX_FILE_BYTES)

app = FastAPI(title="Local-First Agent Search", version="0.3.0",
              description="Local search, profiles, and source-scoped access controls.")
app.add_middleware(CORSMiddleware, allow_origins=[], allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])


def require_local_admin(authorization: str | None = Header(default=None)) -> str:
    token = config.API_TOKEN
    if not token:
        raise HTTPException(status_code=503, detail="Admin API disabled; set SEARCH_API_TOKEN and restart")
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(supplied, token):
        raise HTTPException(status_code=401, detail="Invalid local admin token")
    return "local-owner"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-only"}


@app.get("/collections")
def list_collections() -> dict[str, list[str]]:
    return {"collections": engine.list_collections()}


@app.get("/connectors")
def list_connectors() -> dict[str, Any]:
    # Discovery only: these providers are not queried until an approved API adapter is implemented/configured.
    return {"connectors": [
        {"id": "local", "status": "active", "network": False},
        {"id": "google", "status": "not_configured", "network": True, "integration": "official API only"},
        {"id": "bing", "status": "not_configured", "network": True, "integration": "official API only"},
        {"id": "duckduckgo", "status": "not_configured", "network": True, "integration": "approved interface only"},
        {"id": "yahoo", "status": "not_configured", "network": True, "integration": "approved interface only"},
        {"id": "firefox", "status": "not_configured", "network": False, "integration": "browser extension/API required"},
        {"id": "onion", "status": "disabled", "network": True, "integration": "not implemented"},
        {"id": "private_dataset", "status": "local_only", "network": False, "integration": "owner-managed import"},
    ]}


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str, actor: str = Depends(require_local_admin)) -> dict[str, Any]:
    profile = store.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


@app.post("/profiles")
def save_profile(payload: ProfilePayload, actor: str = Depends(require_local_admin)) -> dict[str, Any]:
    unknown = set(payload.default_collections) - set(engine.list_collections())
    if unknown:
        raise HTTPException(status_code=400, detail="Default collections must already exist")
    profile = store.save_profile(**payload.model_dump())
    store.audit("profile_saved", actor, {"profile_id": payload.profile_id, "locale": payload.locale,
                "languages": payload.languages, "collection_count": len(payload.default_collections)})
    return {"profile": profile}


@app.post("/index")
def index_document(payload: IndexFilePayload, actor: str = Depends(require_local_admin)) -> dict[str, Any]:
    try:
        text = indexer.read_file(payload.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="File not found in configured ingest directory") from exc
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    doc = engine.index_document(title=payload.path.split("/")[-1], text=text,
                                collection_id=payload.collection_id, source_id=payload.source_id,
                                is_private=payload.is_private)
    store.audit("document_indexed", actor, {"document_id": doc["document_id"],
                "collection_id": payload.collection_id, "source_id": payload.source_id,
                "is_private": payload.is_private})
    return {"status": "indexed", "document": doc}


@app.post("/search")
def search_documents(payload: SearchRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    allowed_collection = None
    allowed_source = None
    actor = "anonymous-local"
    if payload.authorization_id:
        actor = require_local_admin(authorization)
        if not payload.purpose:
            raise HTTPException(status_code=400, detail="purpose is required with authorization_id")
        grant = consent.authorize(grant_id=payload.authorization_id, purpose=payload.purpose)
        if not grant:
            store.audit("private_search_denied", actor, {"authorization_id": payload.authorization_id})
            raise HTTPException(status_code=403, detail="Authorization is invalid, expired, revoked, or purpose-mismatched")
        allowed_collection, allowed_source = grant["collection_id"], grant["source_id"]
        if payload.collections and allowed_collection not in payload.collections:
            raise HTTPException(status_code=403, detail="Authorization does not cover requested collection")
    elif payload.purpose:
        raise HTTPException(status_code=400, detail="purpose requires authorization_id")

    results = engine.search(query=payload.query, collections=payload.collections or None,
                            authorized_collection=allowed_collection, authorized_source=allowed_source,
                            limit=payload.limit)
    store.audit("search_completed", actor, {"query_length": len(payload.query),
                "collections": payload.collections, "result_count": len(results),
                "private_access": bool(allowed_collection)})
    return {"query": payload.query, "results": results, "offline_only": True}


@app.post("/access-grants")
def create_access_grant(payload: LocalAccessGrantPayload, actor: str = Depends(require_local_admin)) -> dict[str, Any]:
    if payload.collection_id not in engine.list_collections():
        raise HTTPException(status_code=404, detail="Collection not found")
    if not any(d["source_id"] == payload.source_id and d["collection_id"] == payload.collection_id
               for d in store.documents([payload.collection_id])):
        raise HTTPException(status_code=404, detail="Source not found in collection")
    try:
        grant = consent.grant_local_access(source_id=payload.source_id,
                    collection_id=payload.collection_id, purpose=payload.purpose,
                    granted_by=actor, expires_in_hours=payload.expires_in_hours)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "granted", "authorization": grant}


@app.post("/access-grants/revoke")
def revoke_access_grant(payload: RevokeGrantPayload, actor: str = Depends(require_local_admin)) -> dict[str, Any]:
    if not consent.revoke(payload.authorization_id, actor):
        raise HTTPException(status_code=404, detail="Active authorization not found")
    return {"status": "revoked"}


@app.get("/audit")
def audit_log(limit: int = Query(default=50, ge=1, le=200), actor: str = Depends(require_local_admin)) -> dict[str, Any]:
    return {"events": store.recent_audit(limit)}
