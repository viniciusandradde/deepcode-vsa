"""FastAPI main application."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, rag, agents

# Configure LangSmith tracing
# LangSmith is automatically enabled when LANGCHAIN_API_KEY is set
# Set LANGCHAIN_TRACING_V2=true to enable tracing
# Set LANGCHAIN_PROJECT to organize traces in a project
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    if not os.getenv("LANGCHAIN_PROJECT"):
        os.environ.setdefault("LANGCHAIN_PROJECT", "ai-agent-template")
    print("✅ LangSmith tracing enabled")
    print(f"   Project: {os.getenv('LANGCHAIN_PROJECT')}")
else:
    print("⚠️  LangSmith tracing disabled (LANGCHAIN_API_KEY not set)")


app = FastAPI(
    title="AI Agent + RAG API",
    description="API for AI agents with RAG capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Agent + RAG API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    import os
    checks = {
        "status": "healthy",
        "checks": {
            "openrouter_api_key": bool(os.getenv("OPENROUTER_API_KEY")),
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "database": False,
        }
    }
    
    # Check database connection
    try:
        from core.database import get_conn
        conn = get_conn()
        conn.close()
        checks["checks"]["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)
    
    return checks

