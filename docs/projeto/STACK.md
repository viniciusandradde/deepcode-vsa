# STACK.md - Documentação Completa para Replicação

Este documento contém todas as especificações técnicas para replicar o sistema AI Agent + RAG usando Cursor ou outro IDE.

---

## ÍNDICE

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura](#2-arquitetura)
3. [Database Schema (PostgreSQL + pgvector)](#3-database-schema)
4. [Backend - API FastAPI](#4-backend-api)
5. [Backend - Core Agents](#5-core-agents)
6. [Backend - RAG Pipeline](#6-rag-pipeline)
7. [Backend - Middleware](#7-middleware)
8. [Frontend - Next.js](#8-frontend)
9. [Configuração e Deploy](#9-configuração)
10. [Scripts Utilitários](#10-scripts)

---

## 1. VISÃO GERAL

### Stack Tecnológico

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Backend API | FastAPI | >=0.115.0 |
| Agentes | LangChain + LangGraph | >=1.0.0 |
| Database | PostgreSQL + pgvector | 16 |
| Embeddings | OpenAI text-embedding-3-small | 1536 dims |
| LLM | OpenRouter (multi-provider) | - |
| Frontend | Next.js + React | 15 + 19 |
| Styling | Tailwind CSS | 3.4 |

### Estrutura de Diretórios

```
template-vsa-tech/
├── api/                    # FastAPI REST API
│   ├── main.py            # Entry point
│   ├── routes/            # Endpoints
│   │   ├── chat.py        # Chat + streaming
│   │   ├── rag.py         # RAG search/ingest
│   │   └── agents.py      # Agent management
│   └── models/            # Pydantic models
│       ├── requests.py
│       └── responses.py
├── core/                   # Core business logic
│   ├── agents/            # Agent implementations
│   │   ├── base.py        # BaseAgent ABC
│   │   ├── simple.py      # SimpleAgent
│   │   └── workflow.py    # WorkflowAgent
│   ├── rag/               # RAG pipeline
│   │   ├── ingestion.py   # Staging + chunking
│   │   ├── loaders.py     # Text splitters
│   │   └── tools.py       # kb_search_client
│   ├── middleware/        # Dynamic config
│   │   └── dynamic.py
│   ├── tools/             # Reusable tools
│   │   └── search.py      # tavily_search
│   ├── database.py        # DB connection
│   └── checkpointing.py   # State persistence
├── backend/               # LangGraph Studio
│   └── agents/
│       └── agent.py
├── frontend/              # Next.js 15
│   └── src/
│       ├── app/           # App router
│       ├── components/    # React components
│       ├── hooks/         # Custom hooks
│       ├── state/         # State management
│       └── lib/           # Utilities
├── scripts/               # Utility scripts
├── sql/kb/                # SQL schema (criar)
└── docker-compose.yml
```

---

## 2. ARQUITETURA

### Fluxo de Dados Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  Next.js 15 (port 3000)                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  ChatPane   │  │   Sidebar   │  │  Settings   │             │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘             │
│         │                │                                       │
│         └────────┬───────┘                                       │
│                  ▼                                               │
│    ┌────────────────────────────────────────┐                     │
│    │ useGenesisUI (facade)                  │                     │
│    │  ├─ ConfigContext  (models, toggles)   │                     │
│    │  ├─ SessionContext (sessions CRUD)     │                     │
│    │  └─ ChatContext    (messages, SSE)     │                     │
│    └────────────────┬───────────────────────┘                     │
└─────────────────┼───────────────────────────────────────────────┘
                  │ HTTP/SSE
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                 │
│  FastAPI (port 8000)                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Routes: /chat, /chat/stream, /rag/search, /rag/ingest   │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                    CORE AGENTS                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ SimpleAgent  │  │WorkflowAgent │  │  BaseAgent   │   │   │
│  │  └──────┬───────┘  └──────────────┘  └──────────────┘   │   │
│  │         │                                                │   │
│  │  ┌──────▼───────────────────────────────────────────┐   │   │
│  │  │ DynamicSettingsMiddleware (runtime model swap)   │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                    RAG PIPELINE                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │  Ingestion   │  │   Loaders    │  │ kb_search    │   │   │
│  │  │ (staging)    │  │ (chunking)   │  │ (search)     │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                      TOOLS                               │   │
│  │  ┌──────────────┐  ┌──────────────┐                     │   │
│  │  │ tavily_search│  │ kb_search    │                     │   │
│  │  │ (web)        │  │ (RAG)        │                     │   │
│  │  └──────────────┘  └──────────────┘                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                         │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │    kb_docs      │  │   kb_chunks     │                       │
│  │   (staging)     │  │  (embeddings)   │                       │
│  └─────────────────┘  └─────────────────┘                       │
│                                                                  │
│  Functions: kb_vector_search, kb_text_search, kb_hybrid_search  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Tenancy

O sistema suporta isolamento por tenant através de:
- `empresa`: Identificador da empresa (string)
- `client_id`: UUID do cliente (prioridade sobre empresa)

Todas as queries RAG DEVEM incluir pelo menos um filtro.

---

## 3. DATABASE SCHEMA

### 3.1 Extensões Necessárias

```sql
-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Para full-text search
```

### 3.2 Tabela kb_docs (Staging)

```sql
CREATE TABLE public.kb_docs (
    id SERIAL PRIMARY KEY,
    source_path TEXT NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    mime_type TEXT DEFAULT 'text/markdown',
    content TEXT,
    meta JSONB DEFAULT '{}',
    client_id UUID,
    empresa TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    CONSTRAINT kb_docs_unique UNIQUE (source_path, source_hash)
);

-- Índices
CREATE INDEX idx_kb_docs_empresa ON public.kb_docs(empresa);
CREATE INDEX idx_kb_docs_client_id ON public.kb_docs(client_id);
CREATE INDEX idx_kb_docs_source_path ON public.kb_docs(source_path);
```

### 3.3 Tabela kb_chunks (Vetores)

```sql
CREATE TABLE public.kb_chunks (
    id SERIAL PRIMARY KEY,
    doc_path TEXT NOT NULL,
    chunk_ix INTEGER NOT NULL,
    content TEXT,
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    meta JSONB DEFAULT '{}',
    client_id UUID,
    empresa TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    CONSTRAINT kb_chunks_unique UNIQUE (doc_path, chunk_ix)
);

-- Índices
CREATE INDEX idx_kb_chunks_empresa ON public.kb_chunks(empresa);
CREATE INDEX idx_kb_chunks_client_id ON public.kb_chunks(client_id);
CREATE INDEX idx_kb_chunks_doc_path ON public.kb_chunks(doc_path);

-- Índice HNSW para busca vetorial (pgvector)
CREATE INDEX idx_kb_chunks_embedding ON public.kb_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Índice GIN para full-text search
CREATE INDEX idx_kb_chunks_content_trgm ON public.kb_chunks
    USING gin (content gin_trgm_ops);
```

### 3.4 Funções de Busca

```sql
-- Busca Vetorial
CREATE OR REPLACE FUNCTION public.kb_vector_search(
    query_vec TEXT,
    k INTEGER,
    threshold FLOAT DEFAULT NULL,
    p_client_id UUID DEFAULT NULL,
    p_empresa TEXT DEFAULT NULL,
    p_chunking TEXT DEFAULT NULL
)
RETURNS TABLE (
    doc_path TEXT,
    chunk_ix INTEGER,
    content TEXT,
    score FLOAT,
    meta JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.doc_path,
        c.chunk_ix,
        c.content,
        1 - (c.embedding <=> query_vec::vector) AS score,
        c.meta
    FROM public.kb_chunks c
    WHERE
        (p_client_id IS NULL OR c.client_id = p_client_id)
        AND (p_empresa IS NULL OR lower(c.empresa) = lower(p_empresa))
        AND (p_chunking IS NULL OR c.meta->>'chunking' = p_chunking)
        AND (threshold IS NULL OR 1 - (c.embedding <=> query_vec::vector) >= threshold)
    ORDER BY c.embedding <=> query_vec::vector
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Busca Full-Text
CREATE OR REPLACE FUNCTION public.kb_text_search(
    query_text TEXT,
    k INTEGER,
    p_client_id UUID DEFAULT NULL,
    p_empresa TEXT DEFAULT NULL,
    p_chunking TEXT DEFAULT NULL
)
RETURNS TABLE (
    doc_path TEXT,
    chunk_ix INTEGER,
    content TEXT,
    score FLOAT,
    meta JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.doc_path,
        c.chunk_ix,
        c.content,
        similarity(c.content, query_text) AS score,
        c.meta
    FROM public.kb_chunks c
    WHERE
        (p_client_id IS NULL OR c.client_id = p_client_id)
        AND (p_empresa IS NULL OR lower(c.empresa) = lower(p_empresa))
        AND (p_chunking IS NULL OR c.meta->>'chunking' = p_chunking)
        AND c.content % query_text
    ORDER BY similarity(c.content, query_text) DESC
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Busca Híbrida (RRF - Reciprocal Rank Fusion)
CREATE OR REPLACE FUNCTION public.kb_hybrid_search(
    query_text TEXT,
    query_vec TEXT,
    k INTEGER,
    threshold FLOAT DEFAULT NULL,
    p_client_id UUID DEFAULT NULL,
    p_empresa TEXT DEFAULT NULL,
    p_chunking TEXT DEFAULT NULL
)
RETURNS TABLE (
    doc_path TEXT,
    chunk_ix INTEGER,
    content TEXT,
    score FLOAT,
    meta JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_vec::vector) AS vec_rank
        FROM public.kb_chunks c
        WHERE
            (p_client_id IS NULL OR c.client_id = p_client_id)
            AND (p_empresa IS NULL OR lower(c.empresa) = lower(p_empresa))
            AND (p_chunking IS NULL OR c.meta->>'chunking' = p_chunking)
            AND (threshold IS NULL OR 1 - (c.embedding <=> query_vec::vector) >= threshold)
        LIMIT k * 2
    ),
    text_results AS (
        SELECT
            c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            ROW_NUMBER() OVER (ORDER BY similarity(c.content, query_text) DESC) AS text_rank
        FROM public.kb_chunks c
        WHERE
            (p_client_id IS NULL OR c.client_id = p_client_id)
            AND (p_empresa IS NULL OR lower(c.empresa) = lower(p_empresa))
            AND (p_chunking IS NULL OR c.meta->>'chunking' = p_chunking)
            AND c.content % query_text
        LIMIT k * 2
    ),
    combined AS (
        SELECT
            COALESCE(v.doc_path, t.doc_path) AS doc_path,
            COALESCE(v.chunk_ix, t.chunk_ix) AS chunk_ix,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.meta, t.meta) AS meta,
            COALESCE(1.0 / (60 + v.vec_rank), 0) + COALESCE(1.0 / (60 + t.text_rank), 0) AS rrf_score
        FROM vector_results v
        FULL OUTER JOIN text_results t
            ON v.doc_path = t.doc_path AND v.chunk_ix = t.chunk_ix
    )
    SELECT
        combined.doc_path,
        combined.chunk_ix,
        combined.content,
        combined.rrf_score AS score,
        combined.meta
    FROM combined
    ORDER BY rrf_score DESC
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Busca Híbrida Union (alternativa)
CREATE OR REPLACE FUNCTION public.kb_hybrid_union(
    query_text TEXT,
    query_vec TEXT,
    k INTEGER,
    threshold FLOAT DEFAULT NULL,
    p_client_id UUID DEFAULT NULL,
    p_empresa TEXT DEFAULT NULL,
    p_chunking TEXT DEFAULT NULL
)
RETURNS TABLE (
    doc_path TEXT,
    chunk_ix INTEGER,
    content TEXT,
    score FLOAT,
    meta JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH all_results AS (
        -- Vector results
        SELECT
            c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            1 - (c.embedding <=> query_vec::vector) AS score,
            'vector' AS source
        FROM public.kb_chunks c
        WHERE
            (p_client_id IS NULL OR c.client_id = p_client_id)
            AND (p_empresa IS NULL OR lower(c.empresa) = lower(p_empresa))
            AND (p_chunking IS NULL OR c.meta->>'chunking' = p_chunking)

        UNION ALL

        -- Text results
        SELECT
            c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            similarity(c.content, query_text) AS score,
            'text' AS source
        FROM public.kb_chunks c
        WHERE
            (p_client_id IS NULL OR c.client_id = p_client_id)
            AND (p_empresa IS NULL OR lower(c.empresa) = lower(p_empresa))
            AND (p_chunking IS NULL OR c.meta->>'chunking' = p_chunking)
            AND c.content % query_text
    ),
    aggregated AS (
        SELECT
            ar.doc_path,
            ar.chunk_ix,
            ar.content,
            ar.meta,
            MAX(ar.score) AS max_score
        FROM all_results ar
        GROUP BY ar.doc_path, ar.chunk_ix, ar.content, ar.meta
    )
    SELECT
        aggregated.doc_path,
        aggregated.chunk_ix,
        aggregated.content,
        aggregated.max_score AS score,
        aggregated.meta
    FROM aggregated
    WHERE threshold IS NULL OR aggregated.max_score >= threshold
    ORDER BY max_score DESC
    LIMIT k;
END;
$$ LANGUAGE plpgsql;
```

---

## 4. BACKEND API

### 4.1 Main Application (api/main.py)

```python
"""FastAPI main application."""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, rag, agents

# LangSmith tracing
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "ai-agent-template")

app = FastAPI(
    title="AI Agent + RAG API",
    description="API for AI agents with RAG capabilities",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


@app.get("/")
async def root():
    return {"message": "AI Agent + RAG API", "version": "1.0.0"}


@app.get("/health")
async def health():
    checks = {
        "openrouter_api_key": bool(os.getenv("OPENROUTER_API_KEY")),
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
    }
    try:
        from core.database import get_conn
        conn = get_conn()
        conn.close()
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    return {"status": "healthy", "checks": checks}
```

### 4.2 Request Models (api/models/requests.py)

```python
"""Pydantic request models."""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = None
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    use_tavily: Optional[bool] = None


class RAGSearchRequest(BaseModel):
    query: str
    k: int = 5
    search_type: str = "hybrid"  # vector, text, hybrid, hybrid_rrf, hybrid_union
    reranker: str = "none"       # none, cohere
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    chunking: Optional[str] = None
    use_hyde: bool = False
    match_threshold: Optional[float] = None


class RAGIngestRequest(BaseModel):
    base_dir: str = "kb"
    strategy: str = "semantic"   # fixed, markdown, semantic
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    chunk_size: int = 800
    chunk_overlap: int = 200


class AgentInvokeRequest(BaseModel):
    agent_id: str
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
```

### 4.3 Response Models (api/models/responses.py)

```python
"""Pydantic response models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    model: Optional[str] = None


class RAGSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total: int


class RAGIngestResponse(BaseModel):
    staged: int
    chunked: int
    message: str


class AgentResponse(BaseModel):
    output: Dict[str, Any]
    agent_id: str
```

### 4.4 Chat Routes (api/routes/chat.py)

```python
"""Chat endpoints with streaming support."""
import os
import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.models.requests import ChatRequest
from api.models.responses import ChatResponse
from core.agents.simple import create_simple_agent
from core.tools.search import tavily_search

router = APIRouter()
logger = logging.getLogger(__name__)

DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").lower() in {"1", "true", "yes"}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Synchronous chat endpoint."""
    try:
        model_name = request.model or "google/gemini-2.5-flash"
        tools = []
        if request.use_tavily:
            tools.append(tavily_search)

        agent = create_simple_agent(
            model_name=model_name,
            tools=tools,
        )

        thread_id = request.thread_id or f"thread-{uuid.uuid4().hex[:8]}"

        config = {
            "configurable": {
                "thread_id": thread_id,
                "empresa": request.empresa,
                "client_id": request.client_id,
            }
        }

        from langchain_core.messages import HumanMessage
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )

        messages = result.get("messages", [])
        response_text = ""
        if messages:
            last = messages[-1]
            if hasattr(last, "content"):
                response_text = last.content if isinstance(last.content, str) else str(last.content)

        return ChatResponse(
            response=response_text,
            thread_id=thread_id,
            model=model_name
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """SSE streaming chat endpoint."""

    async def generate() -> AsyncGenerator[str, None]:
        try:
            model_name = request.model or "google/gemini-2.5-flash"
            tools = []
            if request.use_tavily:
                tools.append(tavily_search)

            agent = create_simple_agent(
                model_name=model_name,
                tools=tools,
            )

            thread_id = request.thread_id or f"thread-{uuid.uuid4().hex[:8]}"

            config = {
                "configurable": {
                    "thread_id": thread_id,
                }
            }

            graph = agent.create_graph()

            from langchain_core.messages import HumanMessage, AIMessage
            accumulated_content = ""

            async for chunk in graph.astream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
                stream_mode="values"
            ):
                messages = chunk.get("messages", [])
                if not messages:
                    continue

                # Find last AI message
                last_ai = None
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        last_ai = msg
                        break

                if last_ai and hasattr(last_ai, "content"):
                    content = last_ai.content
                    if isinstance(content, list):
                        content = "".join(
                            c.get("text", "") if isinstance(c, dict) else str(c)
                            for c in content
                        )

                    if content and len(content) > len(accumulated_content):
                        new_content = content[len(accumulated_content):]
                        accumulated_content = content

                        yield f"data: {json.dumps({'type': 'content', 'content': new_content, 'thread_id': thread_id, 'final': False})}\n\n"

            # Final message
            yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id, 'total_length': len(accumulated_content)})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

### 4.5 RAG Routes (api/routes/rag.py)

```python
"""RAG endpoints for search and ingestion."""
import logging
from fastapi import APIRouter, HTTPException

from api.models.requests import RAGSearchRequest, RAGIngestRequest
from api.models.responses import RAGSearchResponse, RAGIngestResponse
from core.rag.tools import kb_search_client
from core.rag.ingestion import stage_docs_from_dir, materialize_chunks_from_staging
from core.database import get_conn

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", response_model=RAGSearchResponse)
async def search_kb(request: RAGSearchRequest) -> RAGSearchResponse:
    """Search knowledge base."""
    try:
        results = kb_search_client.invoke({
            "query": request.query,
            "k": request.k,
            "search_type": request.search_type,
            "reranker": request.reranker,
            "empresa": request.empresa,
            "client_id": request.client_id,
            "chunking": request.chunking,
            "use_hyde": request.use_hyde,
            "match_threshold": request.match_threshold,
        })

        return RAGSearchResponse(
            results=results,
            query=request.query,
            total=len(results)
        )
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=RAGIngestResponse)
async def ingest_documents(request: RAGIngestRequest) -> RAGIngestResponse:
    """Ingest documents into knowledge base."""
    try:
        staged = stage_docs_from_dir(
            request.base_dir,
            empresa=request.empresa,
            client_id=request.client_id
        )

        chunked = materialize_chunks_from_staging(
            strategy=request.strategy,
            empresa=request.empresa,
            client_id=request.client_id,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        return RAGIngestResponse(
            staged=staged,
            chunked=chunked,
            message=f"Staged {staged} docs, created {chunked} chunks"
        )
    except Exception as e:
        logger.error(f"Ingest error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{empresa}")
async def get_kb_stats(empresa: str, client_id: str = None):
    """Get knowledge base statistics."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM public.kb_docs WHERE lower(empresa) = lower(%s)",
                    (empresa,)
                )
                docs = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM public.kb_chunks WHERE lower(empresa) = lower(%s)",
                    (empresa,)
                )
                chunks = cur.fetchone()[0]

        return {
            "empresa": empresa,
            "documents": docs,
            "chunks": chunks
        }
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 5. CORE AGENTS

### 5.1 Base Agent (core/agents/base.py)

```python
"""Abstract base class for all agents."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Iterator, Optional, AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.graph import CompiledGraph


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        model: BaseChatModel,
        tools: Optional[Iterable[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.model = model
        self.tools = list(tools or [])
        self.system_prompt = system_prompt
        self.name = name or self.__class__.__name__

    @abstractmethod
    def create_graph(self) -> CompiledGraph:
        """Create and return the agent's LangGraph graph."""
        pass

    @abstractmethod
    def invoke(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke agent synchronously."""
        pass

    async def ainvoke(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke agent asynchronously (default: calls invoke)."""
        return self.invoke(input, config)

    def stream(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Iterator:
        """Stream agent responses synchronously."""
        graph = self.create_graph()
        return graph.stream(input, config)

    async def astream(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator:
        """Stream agent responses asynchronously."""
        graph = self.create_graph()
        async for chunk in graph.astream(input, config):
            yield chunk

    def add_tool(self, tool: BaseTool) -> None:
        """Add tool to agent."""
        self.tools.append(tool)

    def remove_tool(self, tool_name: str) -> None:
        """Remove tool by name."""
        self.tools = [t for t in self.tools if t.name != tool_name]
```

### 5.2 Simple Agent (core/agents/simple.py)

```python
"""Simple agent using LangChain create_agent with dynamic configuration."""
import os
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langgraph.prebuilt import create_react_agent
from langgraph.graph.graph import CompiledGraph

from core.agents.base import BaseAgent
from core.middleware.dynamic import DynamicSettingsMiddleware

# Timezone São Paulo
try:
    from zoneinfo import ZoneInfo
    SP_TZ = ZoneInfo("America/Sao_Paulo")
except ImportError:
    import pytz
    SP_TZ = pytz.timezone("America/Sao_Paulo")


class SimpleAgent(BaseAgent):
    """Agent using LangChain with dynamic middleware support."""

    def __init__(
        self,
        model_name: str,
        system_prompt: Optional[str] = None,
        tools: Optional[Iterable[BaseTool]] = None,
        openrouter_api_key: Optional[str] = None,
        openrouter_base_url: str = "https://openrouter.ai/api/v1",
        temperature: float = 0.2,
        use_dynamic_middleware: bool = True,
    ):
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Defina OPENROUTER_API_KEY ou passe openrouter_api_key")

        # Default system prompt with current date
        if not system_prompt:
            now = datetime.now(SP_TZ)
            date_str = now.strftime("%d/%m/%Y")
            system_prompt = (
                f"Você é um assistente útil. Hoje é {date_str} (fuso de São Paulo). "
                "Seja direto e preciso nas respostas."
            )

        model = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=openrouter_base_url,
            temperature=temperature,
        )

        super().__init__(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            name="SimpleAgent"
        )

        self.model_name = model_name
        self.use_dynamic_middleware = use_dynamic_middleware
        self._graph = None

    def create_graph(self, checkpointer=None) -> CompiledGraph:
        """Create agent graph with optional middleware."""
        if self._graph is not None:
            return self._graph

        # Create react agent using langgraph
        self._graph = create_react_agent(
            self.model,
            tools=self.tools,
            state_modifier=self.system_prompt,
            checkpointer=checkpointer,
        )

        return self._graph

    def invoke(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke agent synchronously."""
        graph = self.create_graph()
        return graph.invoke(input, config)

    async def ainvoke(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke agent asynchronously."""
        graph = self.create_graph()
        return await graph.ainvoke(input, config)


def create_simple_agent(
    model_name: str,
    system_prompt: Optional[str] = None,
    tools: Optional[Iterable[BaseTool]] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = "https://openrouter.ai/api/v1",
    temperature: float = 0.2,
    use_dynamic_middleware: bool = True,
) -> SimpleAgent:
    """Factory function to create SimpleAgent."""
    return SimpleAgent(
        model_name=model_name,
        system_prompt=system_prompt,
        tools=tools,
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=openrouter_base_url,
        temperature=temperature,
        use_dynamic_middleware=use_dynamic_middleware,
    )
```

### 5.3 Workflow Agent (core/agents/workflow.py)

```python
"""Multi-intent workflow agent with planning capabilities."""
from typing import Any, Dict, List, Literal, Optional, Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from core.agents.base import BaseAgent

# Intent types
IntentLiteral = Literal["conversa_geral", "rag_search", "web_search", "custom_action"]

REQUIRED_SLOTS: Dict[str, List[str]] = {
    "rag_search": ["query"],
    "web_search": ["query"],
    "conversa_geral": [],
    "custom_action": [],
}


class ParserResponse(BaseModel):
    """Structured parser response."""
    intent: IntentLiteral
    slots: List[str]  # Format: ["key=value", ...]


class AgentState(TypedDict, total=False):
    """Workflow agent state."""
    messages: Annotated[List[BaseMessage], add_messages]
    intent: IntentLiteral
    slots: Dict[str, Any]
    errors: List[str]
    context: Dict[str, Any]
    pending_actions: List[Dict[str, Any]]


PARSER_SYSTEM_PROMPT = """Você é um classificador de intenções. Analise a mensagem e retorne:
- intent: uma das opções (conversa_geral, rag_search, web_search, custom_action)
- slots: lista de parâmetros no formato ["key=value", ...]

Exemplos:
- "Busque informações sobre Python" → intent="rag_search", slots=["query=Python"]
- "Pesquise na internet sobre IA" → intent="web_search", slots=["query=IA"]
- "Olá, tudo bem?" → intent="conversa_geral", slots=[]
"""

PLAN_SYSTEM_PROMPT = """Extraia TODAS as ações da mensagem.
Retorne JSON: {"actions": [{"intent": "...", "slots": ["key=value"]}, ...]}
"""


class WorkflowAgent(BaseAgent):
    """Workflow agent with intent classification and planning."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        tools: Optional[List] = None,
        enable_planning: bool = True,
        **kwargs
    ):
        model = ChatOpenAI(model=model_name, temperature=0.2)
        super().__init__(model=model, tools=tools, **kwargs)

        self.enable_planning = enable_planning
        self.parser_llm = model.with_structured_output(ParserResponse)
        self.planner_model = ChatOpenAI(model=model_name, temperature=0.2)

    def create_graph(self):
        """Create LangGraph state graph."""
        builder = StateGraph(AgentState)

        builder.add_node("parse_intent", self._parse_intent)
        builder.add_node("router", self._router)
        builder.add_node("execute_action", self._execute_action)
        builder.add_node("respond", self._respond)

        if self.enable_planning:
            builder.add_node("plan_actions", self._plan_actions)
            builder.set_entry_point("parse_intent")
            builder.add_edge("parse_intent", "plan_actions")
            builder.add_edge("plan_actions", "router")
        else:
            builder.set_entry_point("parse_intent")
            builder.add_edge("parse_intent", "router")

        builder.add_conditional_edges(
            "router",
            self._should_continue,
            {"continue": "execute_action", "done": "respond"}
        )
        builder.add_edge("execute_action", "router")
        builder.add_edge("respond", END)

        return builder.compile()

    def _parse_intent(self, state: AgentState) -> AgentState:
        """Parse user intent."""
        messages = state.get("messages", [])
        if not messages:
            return {"intent": "conversa_geral", "slots": {}}

        last_msg = messages[-1]
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        try:
            result = self.parser_llm.invoke([
                {"role": "system", "content": PARSER_SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ])
            slots_dict = self._slots_to_dict(result.slots)
            return {"intent": result.intent, "slots": slots_dict}
        except Exception:
            return {"intent": "conversa_geral", "slots": {}}

    def _plan_actions(self, state: AgentState) -> AgentState:
        """Plan multiple actions from user message."""
        messages = state.get("messages", [])
        if not messages:
            return {"context": {"pending_actions": []}}

        last_msg = messages[-1]
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        try:
            result = self.planner_model.invoke([
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ])
            # Parse actions from response
            import json
            import re
            text = result.content
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                actions = data.get("actions", [])
                return {"context": {"pending_actions": actions}}
        except Exception:
            pass

        return {"context": {"pending_actions": []}}

    def _router(self, state: AgentState) -> AgentState:
        """Route to next action or finish."""
        context = state.get("context", {})
        pending = context.get("pending_actions", [])

        if pending:
            action = pending[0]
            remaining = pending[1:]
            context["pending_actions"] = remaining
            return {
                "intent": action.get("intent", "conversa_geral"),
                "slots": self._slots_to_dict(action.get("slots", [])),
                "context": context
            }

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Decide if should continue or finish."""
        context = state.get("context", {})
        pending = context.get("pending_actions", [])
        return "continue" if pending else "done"

    def _execute_action(self, state: AgentState) -> AgentState:
        """Execute current action based on intent."""
        intent = state.get("intent", "conversa_geral")
        slots = state.get("slots", {})

        # Action handlers (implement as needed)
        if intent == "rag_search":
            # Call RAG search
            pass
        elif intent == "web_search":
            # Call web search
            pass

        return state

    def _respond(self, state: AgentState) -> AgentState:
        """Generate final response."""
        messages = state.get("messages", [])
        if messages:
            last = messages[-1]
            content = last.content if hasattr(last, "content") else str(last)
            return {"messages": [AIMessage(content=f"Processado: {content}")]}
        return {"messages": [AIMessage(content="Sem mensagem para processar.")]}

    def _slots_to_dict(self, slots: List[str]) -> Dict[str, Any]:
        """Convert ["key=value", ...] to dict."""
        result = {}
        for s in slots:
            if "=" in s:
                k, v = s.split("=", 1)
                result[k.strip()] = v.strip()
        return result

    def invoke(self, input: Dict[str, Any], config: Optional[Dict] = None):
        graph = self.create_graph()
        return graph.invoke(input, config)

    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict] = None):
        graph = self.create_graph()
        return await graph.ainvoke(input, config)
```

---

## 6. RAG PIPELINE

### 6.1 Loaders (core/rag/loaders.py)

```python
"""Text splitting utilities for RAG pipeline."""
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)


def split_text(
    text: str,
    strategy: str = "fixed",
    embedder: Optional[OpenAIEmbeddings] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
) -> Tuple[List[str], str]:
    """Split text using specified strategy.

    Args:
        text: Text to split
        strategy: fixed, markdown, or semantic
        embedder: Required for semantic strategy
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks

    Returns:
        Tuple of (chunks list, resolved strategy name)
    """
    resolved = strategy

    if strategy == "fixed":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_text(text)

    elif strategy == "markdown":
        headers = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
        docs = splitter.split_text(text)
        chunks = [doc.page_content for doc in docs]

    elif strategy == "semantic":
        try:
            from langchain_experimental.text_splitter import SemanticChunker
            if embedder is None:
                embedder = OpenAIEmbeddings(model="text-embedding-3-small")
            splitter = SemanticChunker(embedder)
            docs = splitter.create_documents([text])
            chunks = [doc.page_content for doc in docs]
        except ImportError:
            # Fallback to fixed
            resolved = "fixed"
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            chunks = splitter.split_text(text)

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return chunks, resolved


def load_and_split_dir(
    base_dir: str,
    strategy: str = "semantic",
    embedder: Optional[OpenAIEmbeddings] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """Load markdown files and split into chunks.

    Returns list of dicts with doc_path, chunk_ix, content, meta.
    """
    base = Path(base_dir)
    files = sorted([p for p in base.rglob("*.md") if p.is_file()])

    all_chunks = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        chunks, resolved = split_text(
            text,
            strategy=strategy,
            embedder=embedder,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "doc_path": str(path.as_posix()),
                "chunk_ix": i,
                "content": chunk,
                "meta": {"chunking": resolved}
            })

    return all_chunks
```

### 6.2 Ingestion (core/rag/ingestion.py)

```python
"""RAG ingestion pipeline: staging → chunks → embeddings → PostgreSQL."""
from typing import List, Dict, Any, Optional, TypedDict
from json import dumps as json_dumps
import hashlib
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, END

from core.database import get_conn
from core.rag.loaders import split_text


def vec_to_literal(v: List[float]) -> str:
    """Convert vector to pgvector literal."""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI."""
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return emb.embed_documents(texts)


def sha256_text(s: str) -> str:
    """Calculate SHA256 hash."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def stage_docs_from_dir(
    base_dir: str = "kb",
    *,
    empresa: Optional[str] = None,
    client_id: Optional[str] = None
) -> int:
    """Stage .md files into kb_docs table."""
    base = Path(base_dir)
    files = sorted([p for p in base.rglob("*.md") if p.is_file()])

    if not files:
        return 0

    with get_conn() as conn:
        with conn.cursor() as cur:
            count = 0
            for path in files:
                text = path.read_text(encoding="utf-8")
                h = sha256_text(text)
                cur.execute(
                    """
                    INSERT INTO public.kb_docs
                        (source_path, source_hash, mime_type, content, meta, client_id, empresa)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::uuid, %s)
                    ON CONFLICT (source_path, source_hash) DO NOTHING
                    """,
                    (str(path.as_posix()), h, "text/markdown", text,
                     json_dumps({}), client_id, empresa),
                    prepare=False,
                )
                count += 1
    return count


def upsert_chunks(
    rows: List[Dict[str, Any]],
    *,
    client_id: Optional[str] = None,
    empresa: Optional[str] = None
) -> int:
    """Upsert chunks into kb_chunks table."""
    if not rows:
        return 0

    with get_conn() as conn:
        with conn.cursor() as cur:
            count = 0
            for r in rows:
                vec_lit = vec_to_literal(r["embedding"])
                cur.execute(
                    """
                    INSERT INTO public.kb_chunks
                        (doc_path, chunk_ix, content, embedding, meta, client_id, empresa)
                    VALUES (%s, %s, %s, %s::vector(1536), %s::jsonb, %s::uuid, %s)
                    ON CONFLICT (doc_path, chunk_ix)
                    DO UPDATE SET
                        content=excluded.content,
                        embedding=excluded.embedding,
                        meta=excluded.meta,
                        client_id=excluded.client_id,
                        empresa=excluded.empresa,
                        updated_at=now()
                    """,
                    (r["doc_path"], r["chunk_ix"], r["content"], vec_lit,
                     json_dumps(r.get("meta") or {}), client_id, empresa),
                    prepare=False,
                )
                count += 1
    return count


def materialize_chunks_from_staging(
    *,
    strategy: str = "semantic",
    empresa: Optional[str] = None,
    client_id: Optional[str] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
    doc_path_prefix: Optional[str] = None,
) -> int:
    """Read kb_docs and create kb_chunks with embeddings."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            clauses = []
            vals: List[Any] = []
            if empresa:
                clauses.append("lower(empresa) = lower(%s)")
                vals.append(empresa)
            if client_id:
                clauses.append("client_id = %s::uuid")
                vals.append(client_id)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            cur.execute(
                f"SELECT id, source_path, content FROM public.kb_docs{where}",
                tuple(vals),
                prepare=False,
            )
            docs = cur.fetchall() or []

    if not docs:
        return 0

    embedder = OpenAIEmbeddings(model="text-embedding-3-small") if strategy == "semantic" else None

    rows: List[Dict[str, Any]] = []
    for _id, source_path, content in docs:
        chunks, resolved = split_text(
            content,
            strategy=strategy,
            embedder=embedder,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        for i, c in enumerate(chunks):
            new_doc_path = source_path
            if doc_path_prefix:
                new_doc_path = f"{doc_path_prefix.rstrip('/')}/{source_path}"
            rows.append({
                "doc_path": new_doc_path,
                "chunk_ix": i,
                "content": c,
                "meta": {"chunking": resolved},
            })

    # Generate embeddings
    vectors = embed_texts([r["content"] for r in rows])
    for r, vec in zip(rows, vectors):
        r["embedding"] = vec

    return upsert_chunks(rows, client_id=client_id, empresa=empresa)


def truncate_kb_tables() -> None:
    """Truncate KB tables for clean re-ingestion."""
    with get_conn() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE public.kb_chunks;")
            cur.execute("TRUNCATE TABLE public.kb_docs;")


# LangGraph ingestion graph
class IngestState(TypedDict, total=False):
    base_dir: str
    strategy: str
    strategies: List[str]
    client_id: Optional[str]
    empresa: Optional[str]
    staged: int
    chunked: int


def node_stage(state: IngestState) -> IngestState:
    n = stage_docs_from_dir(
        state.get("base_dir", "kb"),
        empresa=state.get("empresa"),
        client_id=state.get("client_id")
    )
    return {"staged": n}


def node_chunk(state: IngestState) -> IngestState:
    strategies = state.get("strategies") or [state.get("strategy", "semantic")]
    total = 0
    for s in strategies:
        n = materialize_chunks_from_staging(
            strategy=s,
            empresa=state.get("empresa"),
            client_id=state.get("client_id"),
            doc_path_prefix=s,
        )
        total += n
    return {"chunked": total}


def compile_ingest_graph():
    g = StateGraph(IngestState)
    g.add_node("stage_docs", node_stage)
    g.add_node("chunk_docs", node_chunk)
    g.set_entry_point("stage_docs")
    g.add_edge("stage_docs", "chunk_docs")
    g.set_finish_point("chunk_docs")
    return g.compile()


graph = compile_ingest_graph()
```

### 6.3 Search Tools (core/rag/tools.py)

```python
"""RAG search tools with filtering and reranking."""
from typing import Any, Dict, List, Optional
import os

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from core.database import get_conn


def vec_to_literal(v: List[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def query_candidates(
    query: str,
    k: int,
    search_type: str,
    client_id: Optional[str],
    empresa: Optional[str],
    chunking: Optional[str],
    query_embedding: Optional[List[float]],
    match_threshold: Optional[float]
) -> List[Dict[str, Any]]:
    """Get candidates from PostgreSQL."""
    params = {
        "k": k,
        "client_id": client_id,
        "empresa": empresa,
        "chunking": chunking,
        "query": query,
        "threshold": match_threshold,
    }

    with get_conn() as conn:
        with conn.cursor() as cur:
            results = []
            if search_type == "vector":
                if not query_embedding:
                    raise RuntimeError("vector search requires embedding")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "SELECT doc_path, chunk_ix, content, score, meta "
                    "FROM public.kb_vector_search(%(vec)s, %(k)s, %(threshold)s, "
                    "%(client_id)s, %(empresa)s, %(chunking)s)",
                    {**params, "vec": vec_lit},
                )
            elif search_type == "text":
                cur.execute(
                    "SELECT doc_path, chunk_ix, content, score, meta "
                    "FROM public.kb_text_search(%(query)s, %(k)s, %(client_id)s, "
                    "%(empresa)s, %(chunking)s)",
                    params,
                )
            elif search_type in ("hybrid", "hybrid_rrf"):
                if not query_embedding:
                    raise RuntimeError("hybrid search requires embedding")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "SELECT doc_path, chunk_ix, content, score, meta "
                    "FROM public.kb_hybrid_search(%(query)s, %(vec)s, %(k)s, "
                    "%(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s)",
                    {**params, "vec": vec_lit},
                )
            elif search_type == "hybrid_union":
                if not query_embedding:
                    raise RuntimeError("hybrid_union requires embedding")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "SELECT doc_path, chunk_ix, content, score, meta "
                    "FROM public.kb_hybrid_union(%(query)s, %(vec)s, %(k)s, "
                    "%(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s)",
                    {**params, "vec": vec_lit},
                )
            else:
                raise ValueError(f"Unknown search_type: {search_type}")

            for row in cur.fetchall() or []:
                results.append({
                    "doc_path": row[0],
                    "chunk_ix": row[1],
                    "content": row[2],
                    "score": float(row[3]) if row[3] else None,
                    "meta": row[4] or {},
                })
            return results


def apply_rerank(
    query: str,
    items: List[Dict[str, Any]],
    reranker: str,
    k: int
) -> List[Dict[str, Any]]:
    """Apply optional reranking."""
    if reranker == "none" or not items:
        return items[:k]

    if reranker == "cohere":
        if not os.getenv("COHERE_API_KEY"):
            raise RuntimeError("COHERE_API_KEY not set")
        from langchain_cohere import CohereRerank
        model = CohereRerank(model="rerank-english-v3.0")
        docs = [it["content"] for it in items]

        # Try different API versions
        if hasattr(model, "rank"):
            results = model.rank(query=query, documents=docs)
        elif hasattr(model, "rerank"):
            results = model.rerank(query=query, documents=docs)
        else:
            return items[:k]

        # Reconstruct order
        if isinstance(results, list):
            from collections import defaultdict, deque
            idx_map = defaultdict(deque)
            for i, d in enumerate(docs):
                idx_map[d].append(i)
            ordered = []
            for r in results:
                content = getattr(r, "document", {})
                txt = getattr(content, "page_content", None) or str(content)
                if txt in idx_map and idx_map[txt]:
                    i = idx_map[txt].popleft()
                    ordered.append(items[i])
            if ordered:
                return ordered[:k]

    return items[:k]


def hyde(query: str) -> str:
    """Generate hypothetical document for query expansion."""
    llm = ChatOpenAI(
        model=os.getenv("HYDE_LLM_MODEL", "gpt-4o-mini"),
        temperature=0.3
    )
    prompt = (
        "Escreva um parágrafo conciso que seria altamente relevante "
        "para a seguinte pergunta, simulando um documento técnico real.\n"
        f"Pergunta: {query}"
    )
    return (llm.invoke(prompt).content or "").strip()


@tool
def kb_search_client(
    query: str,
    k: int = 5,
    search_type: str = "hybrid",
    reranker: str = "none",
    rerank_candidates: int = 24,
    client_id: Optional[str] = None,
    empresa: Optional[str] = None,
    chunking: Optional[str] = None,
    use_hyde: bool = False,
    match_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search knowledge base with filters and optional reranking.

    Args:
        query: Search query
        k: Number of results
        search_type: vector, text, hybrid, hybrid_rrf, hybrid_union
        reranker: none or cohere
        rerank_candidates: Candidates for reranking
        client_id: Client UUID filter
        empresa: Company filter
        chunking: Chunking strategy filter
        use_hyde: Enable HyDE query expansion
        match_threshold: Similarity threshold

    Returns:
        List of results with doc_path, chunk_ix, content, score, meta
    """
    # Filter policy
    if not client_id and not empresa and not chunking:
        raise RuntimeError("Query requires filter: client_id, empresa, or chunking")

    # Generate embedding if needed
    query_emb = None
    if search_type != "text":
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        q_for_embed = hyde(query) if use_hyde else query
        query_emb = emb.embed_query(q_for_embed)

    # Get candidates
    candidates = query_candidates(
        query,
        rerank_candidates or k,
        search_type,
        client_id,
        empresa,
        chunking,
        query_emb,
        match_threshold,
    )

    # Apply reranking
    return apply_rerank(query, candidates, reranker, k)
```

---

## 7. MIDDLEWARE

### 7.1 Dynamic Settings (core/middleware/dynamic.py)

```python
"""Dynamic configuration middleware for runtime model/tool changes."""
import os
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI


def extract_settings_from_messages(
    messages: List[BaseMessage]
) -> Tuple[Optional[str], Optional[Dict]]:
    """Extract settings from SystemMessage with JSON {"type":"settings"}.

    Returns: (model_name, tool_settings_dict)
    """
    for msg in reversed(messages):
        if isinstance(msg, SystemMessage):
            try:
                data = json.loads(msg.content)
                if data.get("type") == "settings":
                    model = data.get("model")
                    # Extract tool settings (use_*, enable_*)
                    tool_settings = {
                        k: v for k, v in data.items()
                        if k.startswith("use_") or k.startswith("enable_")
                    }
                    return model, tool_settings
            except (json.JSONDecodeError, TypeError):
                continue
    return None, None


def strip_settings_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """Remove settings messages before passing to LLM."""
    result = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            try:
                data = json.loads(msg.content)
                if data.get("type") == "settings":
                    continue
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(msg)
    return result


class DynamicSettingsMiddleware:
    """Middleware for dynamic model and tool configuration.

    Usage:
        # In chat request, send:
        SystemMessage(content='{"type":"settings","model":"gpt-4o-mini","use_tavily":true}')

        # Middleware will:
        # 1. Switch model to gpt-4o-mini
        # 2. Enable tavily_search tool
        # 3. Strip settings message before LLM
    """

    def __init__(self, tool_filters: Optional[Dict[str, Callable]] = None):
        self.tool_filters = tool_filters or {}

    def filter_tools(self, tools: List, tool_settings: Dict) -> List:
        """Filter tools based on settings flags."""
        filtered = []
        for tool in tools:
            name = getattr(tool, "name", str(tool))

            # Check custom filter
            if name in self.tool_filters:
                if self.tool_filters[name](tools, tool_settings):
                    filtered.append(tool)
                continue

            # Check standard flags
            use_key = f"use_{name}"
            enable_key = f"enable_{name}"

            if use_key in tool_settings:
                if tool_settings[use_key]:
                    filtered.append(tool)
            elif enable_key in tool_settings:
                if tool_settings[enable_key]:
                    filtered.append(tool)
            else:
                # Keep by default if no flag
                filtered.append(tool)

        return filtered

    def apply_settings(
        self,
        messages: List[BaseMessage],
        tools: List,
        current_model: Any
    ) -> Tuple[List[BaseMessage], List, Any]:
        """Apply dynamic settings.

        Returns: (cleaned_messages, filtered_tools, new_model)
        """
        model_name, tool_settings = extract_settings_from_messages(messages)

        # Filter tools
        new_tools = tools
        if tool_settings:
            new_tools = self.filter_tools(tools, tool_settings)

        # Create new model if specified
        new_model = current_model
        if model_name:
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            new_model = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
            )

        # Strip settings messages
        cleaned = strip_settings_messages(messages)

        return cleaned, new_tools, new_model
```

---

## 8. FRONTEND (Next.js 15 + React 19)

### 8.1 Estrutura de Arquivos

```
frontend/src/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   ├── globals.css         # Global styles
│   └── api/                # API routes
│       ├── models/route.ts
│       └── threads/
│           ├── route.ts
│           └── [threadId]/
│               ├── route.ts
│               └── messages/
│                   ├── route.ts
│                   └── stream/route.ts
├── components/
│   ├── app/                # Application components
│   │   ├── ChatPane.tsx
│   │   ├── Sidebar.tsx
│   │   ├── MessageActions.tsx
│   │   ├── SettingsPanel.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── Logo.tsx
│   │   ├── AudioRecorderButton.tsx
│   │   └── DeleteConfirmDialog.tsx
│   └── ui/                 # Primitive components
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── select.tsx
│       ├── switch.tsx
│       ├── badge.tsx
│       └── toast.tsx
├── hooks/
│   ├── useAudioRecorder.ts
│   └── useToast.ts
├── state/                     # Split domain contexts (refactored)
│   ├── types.ts               # Shared types
│   ├── error-utils.ts         # API error translation
│   ├── use-local-storage-state.ts # localStorage hook
│   ├── config-context.tsx     # ConfigContext (models, toggles)
│   ├── session-context.tsx    # SessionContext (session CRUD)
│   ├── chat-context.tsx       # ChatContext (messages, streaming)
│   └── useGenesisUI.tsx       # Facade hook (~70 lines)
└── lib/
    ├── config.ts           # Configuration
    └── storage.ts          # LocalStorage utilities
```

### 8.2 State Management (Split Domain Contexts)

The frontend state was refactored from a 1239-line monolithic context into 3 focused domain contexts:

**Provider nesting order:**
```
GenesisUIProvider (facade)
  └─ ConfigProvider    (models, toggles — no deps)
       └─ SessionProvider  (sessions — no deps on Config)
             └─ ChatProvider   (messages, streaming — reads Config + Session)
                   └─ {children}
```

**Contexts:**
- `ConfigContext` (`config-context.tsx`): Models, selectedModelId, useTavily, enable* toggles
- `SessionContext` (`session-context.tsx`): Sessions CRUD, currentSessionId, fetchSession
- `ChatContext` (`chat-context.tsx`): Messages, streaming SSE, send/edit/resend/cancel

**Facade (backward-compatible):**
```typescript
// useGenesisUI.tsx (~70 lines)
export function useGenesisUI() {
  const config = useConfig();
  const session = useSession();
  const chat = useChat();
  return { ...config, ...session, ...chat };
}
```

**Types** are shared via `state/types.ts`:
```typescript
export type Role = "user" | "assistant"
export interface GenesisMessage { id: string; role: Role; content: string; ... }
export interface GenesisSession { id: string; title: string; createdAt: number; ... }
export interface ModelOption { id: string; label: string; inputCost: number; ... }
```

export function GenesisUIProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [models, setModels] = useState<ModelOption[]>([])
  const [selectedModelId, setSelectedModelId] = useState("google/gemini-2.5-flash")
  const [useTavily, setUseTavily] = useState(false)
  const [sessions, setSessions] = useState<GenesisSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState("")
  const [messagesBySession, setMessagesBySession] = useState<Record<string, GenesisMessage[]>>({})
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)

  // Load models from API
  const loadModels = useCallback(async () => {
    try {
      const res = await fetch("/api/models")
      if (res.ok) {
        const data = await res.json()
        setModels(data.map((m: any) => ({
          id: m.id,
          label: m.label,
          inputCost: m.input_cost || 0,
          outputCost: m.output_cost || 0,
        })))
      }
    } catch (error) {
      console.error("Failed to load models:", error)
    }
  }, [])

  // Load sessions from localStorage
  const loadSessions = useCallback(async () => {
    const stored = storage.sessions.getAll()
    if (stored.length > 0) {
      setSessions(stored.map(s => ({
        id: s.id,
        title: s.title,
        createdAt: s.createdAt,
      })))
      setCurrentSessionId(stored[0].id)

      // Load messages for current session
      const msgs = storage.messages.get(stored[0].id)
      if (msgs.length > 0) {
        setMessagesBySession(prev => ({
          ...prev,
          [stored[0].id]: msgs,
        }))
      }
    }
  }, [])

  // Bootstrap
  useEffect(() => {
    Promise.all([loadModels(), loadSessions()])
      .finally(() => setIsLoading(false))
  }, [loadModels, loadSessions])

  // Create new session
  const createSession = useCallback(async () => {
    try {
      const res = await fetch("/api/threads", { method: "POST" })
      if (res.ok) {
        const data = await res.json()
        const newSession: GenesisSession = {
          id: data.thread_id,
          title: `Nova Sessão ${new Date().toLocaleString("pt-BR")}`,
          createdAt: Date.now(),
        }

        storage.sessions.add({
          ...newSession,
          lastAccessed: Date.now(),
          messageCount: 0,
        })

        setSessions(prev => [newSession, ...prev])
        setCurrentSessionId(newSession.id)
        return newSession.id
      }
    } catch (error) {
      console.error("Failed to create session:", error)
    }
  }, [])

  // Select session
  const selectSession = useCallback(async (id: string) => {
    setCurrentSessionId(id)

    // Load messages from localStorage
    const msgs = storage.messages.get(id)
    setMessagesBySession(prev => ({
      ...prev,
      [id]: msgs,
    }))
  }, [])

  // Send message with streaming
  const sendMessage = useCallback(async (content: string, useStreaming = true) => {
    if (!currentSessionId || !content.trim()) return

    setIsSending(true)

    // Create user message
    const userMsg: GenesisMessage = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content: content.trim(),
      timestamp: Date.now(),
      modelId: selectedModelId,
      usedTavily,
    }

    // Add thinking message
    const thinkingMsg: GenesisMessage = {
      id: `msg-${Date.now()}-thinking`,
      role: "assistant",
      content: "Pensando...",
      timestamp: Date.now(),
    }

    setMessagesBySession(prev => ({
      ...prev,
      [currentSessionId]: [...(prev[currentSessionId] || []), userMsg, thinkingMsg],
    }))

    try {
      if (useStreaming) {
        // SSE streaming
        const res = await fetch(`/api/threads/${currentSessionId}/messages/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: content.trim(),
            model: selectedModelId,
            useTavily,
          }),
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const reader = res.body?.getReader()
        if (!reader) throw new Error("No reader")

        const decoder = new TextDecoder()
        let accumulated = ""
        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === "content") {
                  accumulated += data.content
                  setMessagesBySession(prev => {
                    const msgs = [...(prev[currentSessionId] || [])]
                    const idx = msgs.findIndex(m => m.id === thinkingMsg.id)
                    if (idx >= 0) {
                      msgs[idx] = { ...msgs[idx], content: accumulated }
                    }
                    return { ...prev, [currentSessionId]: msgs }
                  })
                } else if (data.type === "done") {
                  // Final update
                  const finalMsg: GenesisMessage = {
                    id: `msg-${Date.now()}-assistant`,
                    role: "assistant",
                    content: accumulated,
                    timestamp: Date.now(),
                    modelId: selectedModelId,
                  }
                  setMessagesBySession(prev => {
                    const msgs = (prev[currentSessionId] || []).filter(
                      m => m.id !== thinkingMsg.id
                    )
                    return { ...prev, [currentSessionId]: [...msgs, finalMsg] }
                  })
                } else if (data.type === "error") {
                  throw new Error(data.error)
                }
              } catch (e) {
                // Ignore parse errors
              }
            }
          }
        }
      } else {
        // Non-streaming
        const res = await fetch(`/api/threads/${currentSessionId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: content.trim(),
            model: selectedModelId,
            useTavily,
          }),
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data = await res.json()
        const assistantMsg: GenesisMessage = {
          id: `msg-${Date.now()}-assistant`,
          role: "assistant",
          content: data.assistant?.content || data.response || "",
          timestamp: Date.now(),
          modelId: selectedModelId,
        }

        setMessagesBySession(prev => {
          const msgs = (prev[currentSessionId] || []).filter(
            m => m.id !== thinkingMsg.id
          )
          return { ...prev, [currentSessionId]: [...msgs, assistantMsg] }
        })
      }

      // Save to localStorage
      const allMsgs = messagesBySession[currentSessionId] || []
      storage.messages.save(currentSessionId, allMsgs.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
        modelId: m.modelId,
        usedTavily: m.usedTavily,
      })))

    } catch (error) {
      console.error("Send message error:", error)
      // Show error message
      setMessagesBySession(prev => {
        const msgs = (prev[currentSessionId] || []).filter(
          m => m.id !== thinkingMsg.id
        )
        return {
          ...prev,
          [currentSessionId]: [
            ...msgs,
            {
              id: `msg-${Date.now()}-error`,
              role: "assistant",
              content: `Erro: ${error instanceof Error ? error.message : "Falha na comunicação"}`,
              timestamp: Date.now(),
            },
          ],
        }
      })
    } finally {
      setIsSending(false)
    }
  }, [currentSessionId, selectedModelId, useTavily, messagesBySession])

  // Edit message
  const editMessage = useCallback((messageId: string, newContent: string) => {
    setMessagesBySession(prev => {
      const msgs = [...(prev[currentSessionId] || [])]
      const idx = msgs.findIndex(m => m.id === messageId)
      if (idx >= 0) {
        msgs[idx] = { ...msgs[idx], content: newContent, editedAt: Date.now() }
      }
      storage.messages.save(currentSessionId, msgs)
      return { ...prev, [currentSessionId]: msgs }
    })
    setEditingMessageId(null)
  }, [currentSessionId])

  // Resend message
  const resendMessage = useCallback(async (messageId: string) => {
    const msgs = messagesBySession[currentSessionId] || []
    const idx = msgs.findIndex(m => m.id === messageId)
    if (idx >= 0) {
      const content = msgs[idx].content
      // Remove messages after this one
      setMessagesBySession(prev => ({
        ...prev,
        [currentSessionId]: msgs.slice(0, idx),
      }))
      await sendMessage(content)
    }
  }, [currentSessionId, messagesBySession, sendMessage])

  // Rename session
  const renameSession = useCallback((id: string, title: string) => {
    setSessions(prev => prev.map(s => s.id === id ? { ...s, title } : s))
    storage.sessions.update(id, { title })
  }, [])

  // Delete session
  const deleteSession = useCallback(async (id: string) => {
    storage.sessions.remove(id)
    storage.messages.clear(id)
    setSessions(prev => prev.filter(s => s.id !== id))

    if (currentSessionId === id) {
      const remaining = sessions.filter(s => s.id !== id)
      if (remaining.length > 0) {
        setCurrentSessionId(remaining[0].id)
      } else {
        await createSession()
      }
    }
  }, [currentSessionId, sessions, createSession])

  const value: GenesisUIState = {
    isLoading,
    isSending,
    models,
    selectedModelId,
    setSelectedModelId,
    useTavily,
    setUseTavily,
    sessions,
    currentSessionId,
    createSession,
    selectSession,
    renameSession,
    deleteSession,
    messagesBySession,
    sendMessage,
    editingMessageId,
    setEditingMessageId,
    editMessage,
    resendMessage,
  }

  return (
    <GenesisUIContext.Provider value={value}>
      {children}
    </GenesisUIContext.Provider>
  )
}
```

### 8.3 Storage Utilities (lib/storage.ts)

```typescript
const STORAGE_PREFIX = "ai_agent_rag_"

export interface StoredSession {
  id: string
  title: string
  createdAt: number
  lastAccessed: number
  messageCount: number
}

export interface StoredMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: number
  modelId?: string
  usedTavily?: boolean
  editedAt?: number
}

function getKey(key: string): string {
  return `${STORAGE_PREFIX}${key}`
}

export const storage = {
  sessions: {
    getAll(): StoredSession[] {
      if (typeof window === "undefined") return []
      try {
        const data = localStorage.getItem(getKey("sessions"))
        return data ? JSON.parse(data) : []
      } catch {
        return []
      }
    },

    save(sessions: StoredSession[]): void {
      if (typeof window === "undefined") return
      localStorage.setItem(getKey("sessions"), JSON.stringify(sessions))
    },

    add(session: StoredSession): void {
      const sessions = this.getAll()
      sessions.unshift(session)
      this.save(sessions)
    },

    update(id: string, updates: Partial<StoredSession>): void {
      const sessions = this.getAll()
      const idx = sessions.findIndex(s => s.id === id)
      if (idx >= 0) {
        sessions[idx] = { ...sessions[idx], ...updates }
        this.save(sessions)
      }
    },

    remove(id: string): void {
      const sessions = this.getAll().filter(s => s.id !== id)
      this.save(sessions)
    },
  },

  messages: {
    get(sessionId: string): StoredMessage[] {
      if (typeof window === "undefined") return []
      try {
        const data = localStorage.getItem(getKey(`messages_${sessionId}`))
        return data ? JSON.parse(data) : []
      } catch {
        return []
      }
    },

    save(sessionId: string, messages: StoredMessage[]): void {
      if (typeof window === "undefined") return
      localStorage.setItem(getKey(`messages_${sessionId}`), JSON.stringify(messages))
    },

    add(sessionId: string, message: StoredMessage): void {
      const messages = this.get(sessionId)
      messages.push(message)
      this.save(sessionId, messages)
    },

    clear(sessionId: string): void {
      if (typeof window === "undefined") return
      localStorage.removeItem(getKey(`messages_${sessionId}`))
    },
  },

  settings: {
    get<T>(key: string, defaultValue: T): T {
      if (typeof window === "undefined") return defaultValue
      try {
        const data = localStorage.getItem(getKey(`settings_${key}`))
        return data ? JSON.parse(data) : defaultValue
      } catch {
        return defaultValue
      }
    },

    set<T>(key: string, value: T): void {
      if (typeof window === "undefined") return
      localStorage.setItem(getKey(`settings_${key}`), JSON.stringify(value))
    },
  },

  clear(): void {
    if (typeof window === "undefined") return
    const keys = Object.keys(localStorage).filter(k => k.startsWith(STORAGE_PREFIX))
    keys.forEach(k => localStorage.removeItem(k))
  },
}
```

### 8.4 ChatPane Component (components/app/ChatPane.tsx)

```typescript
"use client"
import React, { useState, useRef, useEffect, useCallback } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useGenesisUI } from "@/state/useGenesisUI"
import { MessageActions } from "./MessageActions"
import { AudioRecorderButton } from "./AudioRecorderButton"
import { Button } from "@/components/ui/button"

interface ChatPaneProps {
  sidebarCollapsed?: boolean
  onToggleSidebar?: () => void
}

export function ChatPane({ sidebarCollapsed, onToggleSidebar }: ChatPaneProps) {
  const {
    isSending,
    currentSessionId,
    messagesBySession,
    sendMessage,
    editingMessageId,
    setEditingMessageId,
    editMessage,
    resendMessage,
    selectedModelId,
    useTavily,
  } = useGenesisUI()

  const [draft, setDraft] = useState("")
  const [useStreaming, setUseStreaming] = useState(true)
  const [editingContent, setEditingContent] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const messages = messagesBySession[currentSessionId] || []

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Handle send
  const handleSend = useCallback(async () => {
    if (!draft.trim() || isSending) return
    const content = draft
    setDraft("")
    await sendMessage(content, useStreaming)
  }, [draft, isSending, sendMessage, useStreaming])

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  // Start editing
  const handleStartEdit = useCallback((msgId: string, content: string) => {
    setEditingMessageId(msgId)
    setEditingContent(content)
  }, [setEditingMessageId])

  // Save edit
  const handleSaveEdit = useCallback(() => {
    if (editingMessageId) {
      editMessage(editingMessageId, editingContent)
    }
  }, [editingMessageId, editingContent, editMessage])

  // Audio transcript handler
  const handleTranscript = useCallback((transcript: string) => {
    setDraft(prev => prev + (prev ? " " : "") + transcript)
  }, [])

  return (
    <div className="flex flex-col h-full bg-[#0d1426]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div className="flex items-center gap-4">
          <button onClick={onToggleSidebar} className="p-2 hover:bg-white/10 rounded-lg">
            {sidebarCollapsed ? "→" : "←"}
          </button>
          <span className="text-sm text-white/60">
            Modelo: {selectedModelId}
          </span>
          {useTavily && (
            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
              Web Search
            </span>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm text-white/60">
          <input
            type="checkbox"
            checked={useStreaming}
            onChange={e => setUseStreaming(e.target.checked)}
            className="rounded"
          />
          Streaming
        </label>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`relative group max-w-3xl ${
              msg.role === "user" ? "ml-auto" : "mr-auto"
            }`}
          >
            <div
              className={`p-4 rounded-xl ${
                msg.role === "user"
                  ? "bg-orange-500/20 text-white"
                  : msg.content.startsWith("Erro:")
                  ? "bg-red-500/20 text-red-300"
                  : "bg-white/5 text-white/90"
              }`}
            >
              {editingMessageId === msg.id ? (
                <div className="space-y-2">
                  <textarea
                    value={editingContent}
                    onChange={e => setEditingContent(e.target.value)}
                    className="w-full bg-white/10 rounded p-2 text-white"
                    rows={4}
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveEdit}>Salvar</Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditingMessageId(null)}>
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : msg.content === "Pensando..." ? (
                <div className="flex items-center gap-2">
                  <span className="animate-pulse">●</span>
                  <span className="animate-pulse delay-100">●</span>
                  <span className="animate-pulse delay-200">●</span>
                </div>
              ) : msg.role === "assistant" ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => <p className="mb-2">{children}</p>,
                    a: ({ href, children }) => (
                      <a href={href} target="_blank" rel="noopener" className="text-blue-400 hover:underline">
                        {children}
                      </a>
                    ),
                    code: ({ className, children }) => {
                      const isBlock = className?.includes("language-")
                      return isBlock ? (
                        <pre className="bg-black/30 p-3 rounded-lg overflow-x-auto my-2">
                          <code className={className}>{children}</code>
                        </pre>
                      ) : (
                        <code className="bg-black/30 px-1 rounded">{children}</code>
                      )
                    },
                    ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>

            {msg.role === "user" && !editingMessageId && (
              <MessageActions
                message={msg}
                onEdit={() => handleStartEdit(msg.id, msg.content)}
                onResend={() => resendMessage(msg.id)}
              />
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      {/* Input */}
      <footer className="px-6 py-4 border-t border-white/10">
        <div className="flex items-end gap-2 max-w-3xl mx-auto">
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Digite sua mensagem... (Ctrl+Enter para enviar)"
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/40 resize-none"
            rows={2}
            disabled={isSending}
          />
          <AudioRecorderButton onTranscript={handleTranscript} />
          <Button
            onClick={handleSend}
            disabled={!draft.trim() || isSending}
            className="h-12"
          >
            {isSending ? "..." : "Enviar"}
          </Button>
        </div>
      </footer>
    </div>
  )
}
```

### 8.5 API Routes

#### GET/POST /api/threads (app/api/threads/route.ts)

```typescript
import { NextResponse } from "next/server"

export async function GET() {
  return NextResponse.json({ threads: [] })
}

export async function POST() {
  const threadId = `thread-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  return NextResponse.json({
    thread_id: threadId,
    thread: { thread_id: threadId, created_at: new Date().toISOString() }
  })
}
```

#### POST /api/threads/[threadId]/messages/stream

```typescript
import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.API_BASE_URL || "http://localhost:8000"

export async function POST(
  request: NextRequest,
  { params }: { params: { threadId: string } }
) {
  try {
    const body = await request.json()
    const { content, model, useTavily } = body

    const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: content,
        thread_id: params.threadId,
        model,
        use_tavily: useTavily,
      }),
    })

    if (!res.ok) {
      const error = await res.text()
      return NextResponse.json({ error }, { status: res.status })
    }

    // Proxy SSE stream
    return new NextResponse(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    )
  }
}
```

### 8.6 CSS Variables (globals.css)

```css
:root {
  --font-sans: ui-sans-serif, system-ui, sans-serif;
  --font-mono: ui-monospace, monospace;

  /* VSA Brand Colors */
  --vsa-orange-dark: #FF6B35;
  --vsa-orange: #FF8C42;
  --vsa-orange-light: #FFB347;

  --vsa-blue-dark: #1E3A8A;
  --vsa-blue: #3B82F6;
  --vsa-blue-light: #60A5FA;

  /* Gradients */
  --vsa-orange-gradient: linear-gradient(135deg, #FF6B35 0%, #FF8C42 50%, #FFB347 100%);
  --vsa-blue-gradient: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #60A5FA 100%);
}

body {
  background: #0d1426;
  color: #f0f0f0;
}
```

---

## 9. CONFIGURAÇÃO E DEPLOY

### 9.1 Variáveis de Ambiente (.env)

```env
# ===========================================
# DATABASE
# ===========================================
DB_HOST=postgres              # Docker: postgres | Local: localhost
DB_PORT=5432                  # Inside Docker network
DB_NAME=ai_agent_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_SSLMODE=disable           # Docker: disable | Production: require

# ===========================================
# API KEYS (Required)
# ===========================================
OPENAI_API_KEY=sk-proj-...              # For embeddings
OPENROUTER_API_KEY=sk-or-v1-...         # For LLM

# ===========================================
# API KEYS (Optional)
# ===========================================
TAVILY_API_KEY=tvly-...                 # Web search
COHERE_API_KEY=...                      # Reranking
LANGCHAIN_API_KEY=...                   # LangSmith tracing

# ===========================================
# SYSTEM CONFIG
# ===========================================
USE_POSTGRES_CHECKPOINT=true
DEFAULT_MODEL_NAME=google/gemini-2.5-flash
DEFAULT_USE_TAVILY=false
DEBUG_AGENT_LOGS=false
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
HYDE_LLM_MODEL=gpt-4o-mini

# ===========================================
# LANGSMITH (Optional)
# ===========================================
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai-agent-template

# ===========================================
# FRONTEND
# ===========================================
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_LANGGRAPH_BASE=http://127.0.0.1:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
```

### 9.2 Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: ai_agent_postgres
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-ai_agent_db}
    ports:
      - "${DB_PORT:-5433}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d/sql
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_agent_network

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: ai_agent_backend
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${DB_NAME:-ai_agent_db}
      DB_USER: ${DB_USER:-postgres}
      DB_PASSWORD: ${DB_PASSWORD:-postgres}
      DB_SSLMODE: disable
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      TAVILY_API_KEY: ${TAVILY_API_KEY:-}
      COHERE_API_KEY: ${COHERE_API_KEY:-}
      USE_POSTGRES_CHECKPOINT: ${USE_POSTGRES_CHECKPOINT:-true}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - ai_agent_network
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: ai_agent_frontend
    environment:
      API_BASE_URL: http://backend:8000
      NEXT_PUBLIC_API_BASE: ${NEXT_PUBLIC_API_BASE:-http://localhost:8000}
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - ./models.yaml:/app/models.yaml:ro
    depends_on:
      - backend
    networks:
      - ai_agent_network
    command: npm run dev

volumes:
  postgres_data:

networks:
  ai_agent_network:
    driver: bridge
```

### 9.3 Requirements (requirements.txt)

```
langchain>=1.0.0
langgraph>=1.0.0
langchain-openai>=1.0.1
langchain-tavily>=0.2.12
langchain-text-splitters>=0.3.0
langgraph-checkpoint>=3.0.1
langgraph-checkpoint-postgres>=3.0.1
python-dotenv>=1.2.1
psycopg[binary]>=3.1.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.12.4
```

### 9.4 Package.json (Frontend)

```json
{
  "name": "ai-agent-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  },
  "dependencies": {
    "next": "15.5.5",
    "react": "19.1.0",
    "react-dom": "19.1.0",
    "react-markdown": "10.1.0",
    "remark-gfm": "4.0.1",
    "clsx": "2.1.1",
    "js-yaml": "4.1.0"
  },
  "devDependencies": {
    "typescript": "5.6.3",
    "tailwindcss": "3.4.14",
    "@types/react": "19.1.0",
    "@types/node": "22.15.0",
    "jest": "29.7.0",
    "@testing-library/react": "14.1.2"
  }
}
```

---

## 10. SCRIPTS UTILITÁRIOS

### 10.1 RAG Ingest (scripts/rag_ingest.py)

```python
#!/usr/bin/env python3
"""RAG ingestion script."""
import argparse
from dotenv import load_dotenv

load_dotenv()

from core.rag.ingestion import (
    stage_docs_from_dir,
    materialize_chunks_from_staging,
    truncate_kb_tables,
)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into KB")
    parser.add_argument("--base", default="kb", help="Base directory with .md files")
    parser.add_argument("--empresa", help="Company name for tagging")
    parser.add_argument("--client-id", help="Client UUID")
    parser.add_argument("--strategy", default="semantic",
                        choices=["fixed", "markdown", "semantic"])
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    parser.add_argument("--truncate", action="store_true",
                        help="Truncate tables before ingestion")

    args = parser.parse_args()

    if args.truncate:
        print("Truncating KB tables...")
        truncate_kb_tables()

    print(f"Staging documents from {args.base}...")
    staged = stage_docs_from_dir(
        args.base,
        empresa=args.empresa,
        client_id=args.client_id
    )
    print(f"Staged {staged} documents.")

    print(f"Materializing chunks with strategy={args.strategy}...")
    chunked = materialize_chunks_from_staging(
        strategy=args.strategy,
        empresa=args.empresa,
        client_id=args.client_id,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    print(f"Created {chunked} chunks.")

    print("Ingestion complete!")


if __name__ == "__main__":
    main()
```

### 10.2 Database Connection (core/database.py)

```python
"""Database connection utilities."""
import os
from dotenv import load_dotenv

load_dotenv()

import psycopg


def get_db_url() -> str:
    """Build PostgreSQL connection URL."""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    sslmode = os.getenv("DB_SSLMODE", "require")

    if not all([user, password, host, name]):
        raise RuntimeError("Missing database configuration")

    return f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode={sslmode}"


def get_conn():
    """Get PostgreSQL connection."""
    return psycopg.connect(get_db_url())
```

### 10.3 Tavily Search Tool (core/tools/search.py)

```python
"""Web search tool using Tavily."""
import os
import json
from langchain_core.tools import tool


@tool
def tavily_search(
    query: str,
    max_results: int = 5,
    include_raw_content: bool = False,
) -> str:
    """Search the internet using Tavily.

    Args:
        query: Search query
        max_results: Maximum number of results
        include_raw_content: Include raw page content

    Returns:
        JSON string with search results
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not set")

    from langchain_tavily import TavilySearch

    client = TavilySearch(
        max_results=max_results,
        topic="general",
        include_raw_content=include_raw_content,
    )

    results = client.invoke(query)

    try:
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception:
        return str(results)
```

---

## CHECKLIST DE REPLICAÇÃO

### Fase 1: Infraestrutura
- [ ] Criar banco PostgreSQL 16 com pgvector
- [ ] Executar scripts SQL (seção 3)
- [ ] Configurar .env com todas variáveis

### Fase 2: Backend
- [ ] Criar estrutura de pastas (api/, core/)
- [ ] Implementar database.py e checkpointing.py
- [ ] Implementar agents (base.py, simple.py)
- [ ] Implementar RAG (loaders.py, ingestion.py, tools.py)
- [ ] Implementar middleware (dynamic.py)
- [ ] Implementar tools (search.py)
- [ ] Implementar API routes (chat.py, rag.py, agents.py)
- [ ] Testar: `make dev` e acessar /health

### Fase 3: Frontend
- [ ] Criar projeto Next.js 15
- [ ] Instalar dependências
- [ ] Implementar lib/ (config.ts, storage.ts)
- [ ] Implementar state/ (useGenesisUI.tsx)
- [ ] Implementar components/ (ChatPane, Sidebar, etc.)
- [ ] Implementar API routes
- [ ] Testar: `make frontend`

### Fase 4: Integração
- [ ] Configurar docker-compose.yml
- [ ] Criar models.yaml
- [ ] Testar: `docker-compose up -d`
- [ ] Testar chat streaming
- [ ] Testar RAG ingest e search

### Fase 5: Produção
- [ ] Configurar SSL/TLS
- [ ] Ajustar CORS para domínios específicos
- [ ] Configurar LangSmith tracing
- [ ] Documentar APIs (OpenAPI)

---

*Documento gerado automaticamente. Última atualização: Janeiro 2026*
