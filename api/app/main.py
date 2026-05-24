import logging
from contextlib import asynccontextmanager 
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends, FastAPI, Header, HTTPException, status
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

allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "x-api-key"],
)

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
    )

def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()

    if not settings.app_api_key:
        return

    if x_api_key != settings.app_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

@app.post("/ask", response_model=AskResponse,dependencies=[Depends(require_api_key)])
async def ask(request: AskRequest) -> AskResponse:
    logger.info(f"Incoming request: {request}")
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