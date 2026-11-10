from pydantic import BaseModel, Field
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collections: List[str] = Field(default_factory=list)
    include_private: bool = False
    language: Optional[str] = None


class SearchResult(BaseModel):
    document_id: str
    title: str
    collection_id: str
    source_id: str
    score: float
    snippet: str
    consent_required: bool = False


class ConsentRequestPayload(BaseModel):
    subject_id: str
    source_id: str
    purpose: str
    requested_by: str
    expires_in_hours: int = 24


class ConsentApprovePayload(BaseModel):
    request_id: str
    approved_by: str


class IndexFilePayload(BaseModel):
    path: str
    collection_id: str = "default"
    source_id: str = "local-default"
    consent_required: bool = False


class ConsentRequestRecord(BaseModel):
    request_id: str
    subject_id: str
    source_id: str
    purpose: str
    requested_by: str
    status: str = "pending"
    expires_in_hours: int = 24
    approved_by: Optional[str] = None


class SourceConfig(BaseModel):
    id: str
    name: str
    kind: str = "local"
    consent_required: bool = False
    enabled: bool = True
