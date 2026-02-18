"""FastAPI main application."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.auth import verify_api_key
from api.routes import (
    agents,
    agents_admin,
    auth,
    automation,
    chat,
    config,
    files,
    export,
    images,
    knowledge,
    planning,
    projects,
    queue,
    rag,
    reports,
    threads,
)
from core.checkpointing import initialize_checkpointer, cleanup_checkpointer
from core.scheduler import get_scheduler_service

logger = logging.getLogger(__name__)


def _configure_langsmith() -> None:
    """Configure LangSmith tracing if API key is available."""
    if os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        if not os.getenv("LANGCHAIN_PROJECT"):
            os.environ.setdefault("LANGCHAIN_PROJECT", "ai-agent-template")
        logger.info("LangSmith tracing enabled (project: %s)", os.getenv("LANGCHAIN_PROJECT"))
    else:
        logger.info("LangSmith tracing disabled (LANGCHAIN_API_KEY not set)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    _configure_langsmith()

    logger.info("Starting up application...")
    try:
        await initialize_checkpointer()
    except Exception as e:
        logger.warning("Checkpointer initialization failed: %s", e)
        logger.info("Application will continue with MemorySaver fallback")

    try:
        scheduler = get_scheduler_service()
        scheduler.start()
        logger.info("Scheduler service started")
    except Exception as e:
        logger.warning("Scheduler initialization failed: %s", e)

    yield

    logger.info("Shutting down application...")
    try:
        scheduler = get_scheduler_service()
        scheduler.shutdown(wait=True)
        logger.info("Scheduler service stopped")
    except Exception as e:
        logger.warning("Scheduler shutdown failed: %s", e)

    try:
        await cleanup_checkpointer()
    except Exception as e:
        logger.warning("Checkpointer cleanup failed: %s", e)

    # Close notification service HTTP client
    try:
        from core.notifications import notification_service

        await notification_service.close()
    except Exception as e:
        logger.warning("Notification service cleanup failed: %s", e)


app = FastAPI(
    title="DeepCode VSA API",
    description="API do Agente de Suporte Virtual para Gestao de TI.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - use specific origins from env, never wildcard with credentials
_allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with auth dependency on all API endpoints
_api_deps = [Depends(verify_api_key)]

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"], dependencies=_api_deps)
app.include_router(files.router, prefix="/api/v1/files", tags=["files"], dependencies=_api_deps)
app.include_router(images.router, prefix="/api/v1/images", tags=["images"], dependencies=_api_deps)
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"], dependencies=_api_deps)
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"], dependencies=_api_deps)
app.include_router(
    threads.router, prefix="/api/v1/threads", tags=["threads"], dependencies=_api_deps
)
app.include_router(
    reports.router, prefix="/api/v1/reports", tags=["reports"], dependencies=_api_deps
)
app.include_router(
    planning.router, prefix="/api/v1/planning", tags=["planning"], dependencies=_api_deps
)
app.include_router(config.router, prefix="/api/v1/config", tags=["config"], dependencies=_api_deps)
app.include_router(
    automation.router, prefix="/api/v1/automation", tags=["automation"], dependencies=_api_deps
)
app.include_router(queue.router, prefix="/api/v1/queue", tags=["queue"], dependencies=_api_deps)
app.include_router(
    projects.router, prefix="/api/v1/projects", tags=["projects"], dependencies=_api_deps
)
app.include_router(export.router, prefix="/api/v1/export", tags=["export"], dependencies=_api_deps)
app.include_router(
    knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"], dependencies=_api_deps
)
app.include_router(
    agents_admin.router, prefix="/api/v1/admin", tags=["admin"], dependencies=_api_deps
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "DeepCode VSA API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint (public, no auth required)."""
    checks = {
        "status": "healthy",
        "checks": {
            "llm_configured": bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")),
            "database": False,
        },
    }

    try:
        from core.database import get_conn

        with get_conn() as conn:
            conn.execute("SELECT 1")
        checks["checks"]["database"] = True
    except Exception:
        checks["checks"]["database"] = False

    return checks
