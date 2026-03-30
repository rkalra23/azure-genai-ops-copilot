from typing import Literal
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    department: str | None = None
    doc_type: str | None = None
    retrieval_mode: Literal["keyword", "vector", "hybrid"] | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceItem(BaseModel):
    title: str
    chunk_id: str
    doc_id: str | None = None
    effective_date: str | None = None
    score: float | None = None


class AskResponse(BaseModel):
    request_id: str
    answer: str
    retrieval_mode: str
    top_k: int
    latency_ms: int
    sources: list[SourceItem]


class FeedbackRequest(BaseModel):
    request_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    status: str
    message: str