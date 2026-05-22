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
    rerank_mode: Literal["none", "heuristic", "azure_semantic"] | None = None
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
    rerank_mode: str | None = None
    top_k: int
    latency_ms: int
    raw_result_count: int | None = None
    filtered_result_count: int | None = None
    reranked_result_count: int | None = None
    final_context_count: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    sources: list[SourceItem]


class FeedbackRequest(BaseModel):
    request_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    status: str
    message: str