import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import get_settings
from .models import (
    AskRequest,
    AskResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
)
from .retrieval import answer_question
from .telemetry import setup_telemetry


settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application: %s", settings.app_name)
    setup_telemetry(settings.azure_monitor_connection_string)
    yield
    logger.info("Stopping application: %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
    )


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    return answer_question(
        request=request,
        default_mode=settings.default_retrieval_mode,
        default_top_k=settings.default_top_k,
    )


@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(request: FeedbackRequest) -> FeedbackResponse:
    logger.info(
        "Feedback received | request_id=%s rating=%s comment=%s",
        request.request_id,
        request.rating,
        request.comment,
    )
    return FeedbackResponse(
        status="accepted",
        message="Feedback captured successfully.",
    )


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "message": "Azure GenAI Ops Copilot API is running.",
            "docs_url": "/docs",
            "health_url": "/health",
        }
    )