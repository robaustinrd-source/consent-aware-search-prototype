from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .consent import ConsentManager
from .indexer import LocalIndexer
from .models import (
    ConsentApprovePayload,
    ConsentRequestPayload,
    IndexFilePayload,
    SearchRequest,
)
from .search_engine import LocalSearchEngine

app = FastAPI(title="Consent-Aware Local Search Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = LocalSearchEngine()
consent = ConsentManager()
indexer = LocalIndexer()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/collections")
def list_collections() -> dict:
    return {"collections": list(engine.collection_map.keys())}


@app.post("/index")
def index_document(payload: IndexFilePayload) -> dict:
    try:
        text = indexer.read_file(payload.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    normalized = indexer.normalize_text(text)
    doc = engine.index_document(
        title=payload.path.split("/")[-1],
        text=normalized,
        collection_id=payload.collection_id,
        source_id=payload.source_id,
        consent_required=payload.consent_required,
    )
    return {"status": "indexed", "document": doc}


@app.post("/search")
def search_documents(payload: SearchRequest) -> dict:
    results = engine.search(
        query=payload.query,
        collections=payload.collections,
        include_private=payload.include_private,
        language=payload.language,
    )
    return {"query": payload.query, "results": results}


@app.post("/consent/request")
def create_consent_request(payload: ConsentRequestPayload) -> dict:
    record = consent.create_request(
        subject_id=payload.subject_id,
        source_id=payload.source_id,
        purpose=payload.purpose,
        requested_by=payload.requested_by,
        expires_in_hours=payload.expires_in_hours,
    )
    return {"status": "requested", "request": record}


@app.post("/consent/approve")
def approve_consent_request(payload: ConsentApprovePayload) -> dict:
    try:
        record = consent.approve(request_id=payload.request_id, approved_by=payload.approved_by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "approved", "request": record}


@app.get("/consent/requests")
def list_consent_requests() -> dict:
    return {"requests": consent.list_requests()}


@app.on_event("startup")
def seed_demo_data() -> None:
    sample_text = """
    Consent-aware workflows protect privacy in local search-based AI systems.
    A user may authorize access to approved private documents.
    Offline agents should use explicit consent and local-only data sources.
    """
    if not engine.documents:
        engine.index_document(
            title="sample-knowledge",
            text=sample_text,
            collection_id="default",
            source_id="local-default",
            consent_required=False,
        )
