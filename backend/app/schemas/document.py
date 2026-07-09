"""Pydantic schemas for the Documents API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Single document metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_name: str
    document_type: str
    version: int
    status: str
    page_count: int
    chunk_count: int
    embedding_model: str | None = None
    file_path: str | None = None
    created_by: str | None = None
    last_indexed: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """List of documents."""

    items: list[DocumentResponse]
    total: int


class SearchRequest(BaseModel):
    """Semantic search request payload."""

    query: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    """A single semantic search result chunk."""

    document_name: str
    page_number: int
    content: str
    score: float


class SearchResponse(BaseModel):
    """Semantic search response."""

    query: str
    results: list[SearchResultItem]
    execution_time_ms: int
