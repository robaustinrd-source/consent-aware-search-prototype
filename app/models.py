from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, max_length=1000)
    collections: List[str] = Field(default_factory=list, max_length=50)
    limit: int = Field(default=20, ge=1, le=100)
    authorization_id: Optional[str] = None
    purpose: Optional[str] = Field(default=None, max_length=200)


class IndexFilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(..., min_length=1, max_length=500)
    collection_id: str = Field(default="default", min_length=1, max_length=100)
    source_id: str = Field(default="local-default", min_length=1, max_length=100)
    is_private: bool = False


class LocalAccessGrantPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(..., min_length=1, max_length=100)
    collection_id: str = Field(..., min_length=1, max_length=100)
    purpose: str = Field(..., min_length=3, max_length=200)
    expires_in_hours: int = Field(default=24, ge=1, le=720)


class RevokeGrantPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    authorization_id: str = Field(..., min_length=1, max_length=100)


class ProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(default="Local user", min_length=1, max_length=100)
    locale: str = Field(default="en", min_length=2, max_length=35)
    languages: List[str] = Field(default_factory=lambda: ["en"], max_length=20)
    default_collections: List[str] = Field(default_factory=list, max_length=50)
    result_format: str = Field(default="json", pattern=r"^(json|html|text)$")
