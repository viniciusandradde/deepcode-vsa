"""RAG ingestion pipeline: staging → chunks → embeddings → PostgreSQL."""

import os
from typing import List, Dict, Any, Optional, TypedDict
from json import dumps as json_dumps
import hashlib
from pathlib import Path
import mimetypes

from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, END

from core.database import get_conn
from core.rag.loaders import load_and_split_dir, split_text
from typing import Dict, Any


def _get_embedding_client() -> OpenAIEmbeddings:
    """OpenAI embeddings client. Requires OPENAI_API_KEY (real OpenAI key, not OpenRouter)."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "RAG embeddings requer OPENAI_API_KEY (chave da OpenAI para api.openai.com). "
            "Chaves do OpenRouter (sk-or-...) não funcionam no endpoint de embeddings."
        )
    if api_key.startswith("sk-or-"):
        raise RuntimeError(
            "RAG embeddings requer uma chave da OpenAI (OPENAI_API_KEY), não do OpenRouter. "
            "Chaves sk-or-... são do OpenRouter e não funcionam em api.openai.com/embeddings. "
            "Defina OPENAI_API_KEY com uma chave de https://platform.openai.com/api-keys"
        )
    return OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)


def vec_to_literal(v: List[float]) -> str:
    """Convert float vector to pgvector literal: "[v1, v2, ...]"."""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for texts (OpenAI api.openai.com)."""
    emb = _get_embedding_client()
    return emb.embed_documents(texts)


def upsert_chunks(
    rows: List[Dict[str, Any]],
    *,
    client_id: Optional[str] = None,
    empresa: Optional[str] = None
) -> int:
    """Idempotent upsert by (doc_path, chunk_ix). Returns affected count."""
    if not rows:
        return 0
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            count = 0
            for r in rows:
                vec_lit = vec_to_literal(r["embedding"])
                cur.execute(
                    """
                    insert into public.kb_chunks (doc_path, chunk_ix, content, embedding, meta, client_id, empresa)
                    values (%s, %s, %s, %s::vector(1536), %s::jsonb, %s::uuid, %s)
                    on conflict (doc_path, chunk_ix)
                    do update set content=excluded.content, embedding=excluded.embedding, meta=excluded.meta,
                                  client_id=excluded.client_id, empresa=excluded.empresa, updated_at=now()
                    """,
                    (
                        r["doc_path"],
                        r["chunk_ix"],
                        r["content"],
                        vec_lit,
                        json_dumps(r.get("meta") or {}),
                        client_id,
                        empresa,
                    ),
                    prepare=False,
                )
                count += 1
    return count


def sha256_text(s: str) -> str:
    """Calculate SHA256 hash of text."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def stage_docs_from_dir(
    base_dir: str = "kb",
    *,
    empresa: Optional[str] = None,
    client_id: Optional[str] = None
) -> int:
    """Read .md files from directory and insert into kb_docs (staging), idempotent by (source_path, source_hash)."""
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
                mime = mimetypes.guess_type(str(path))[0] or "text/markdown"
                cur.execute(
                    """
                    insert into public.kb_docs (source_path, source_hash, mime_type, content, meta, client_id, empresa)
                    values (%s, %s, %s, %s, %s::jsonb, %s::uuid, %s)
                    on conflict (source_path, source_hash) do nothing
                    """,
                    (str(path.as_posix()), h, mime, text, json_dumps({}), client_id, empresa),
                    prepare=False,
                )
                count += 1
    return count


def truncate_kb_tables() -> None:
    """Truncate KB tables (staging and chunks) for clean execution.
    
    WARNING: Removes ALL content from public.kb_docs and public.kb_chunks.
    """
    with get_conn() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("truncate table public.kb_chunks;")
            cur.execute("truncate table public.kb_docs;")


def materialize_chunks_from_staging(
    *,
    strategy: str = "semantic",
    empresa: Optional[str] = None,
    client_id: Optional[str] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
    path_prefix: Optional[str] = None,
    target_empresa: Optional[str] = None,
    doc_path_prefix: Optional[str] = None,
) -> int:
    """Read kb_docs (filter by empresa/path_prefix) and materialize kb_chunks with indicated strategy.
    
    - Selection: filters rows in kb_docs by `empresa` and optionally by `path_prefix`.
    - Write: writes to kb_chunks using `target_empresa` if provided; otherwise uses `empresa`.
    - Idempotent by (doc_path, chunk_ix) — overwrites same pair on upsert.
    """
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
            if path_prefix:
                like = path_prefix
                if not like.endswith('%'):
                    if not like.endswith('/'):
                        like = like + '/'
                    like = like + '%'
                clauses.append("source_path like %s")
                vals.append(like)
            where = (" where " + " and ".join(clauses)) if clauses else ""
            cur.execute(
                f"select id, source_path, content from public.kb_docs{where}",
                tuple(vals),
                prepare=False,
            )
            docs = cur.fetchall() or []
    
    if not docs:
        return 0
    
    # Decide embedder for semantic
    embedder = OpenAIEmbeddings(model="text-embedding-3-small") if strategy == "semantic" else None
    
    total = 0
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
    
    vectors = embed_texts([r["content"] for r in rows])
    for r, vec in zip(rows, vectors):
        r["embedding"] = vec
    
    write_empresa = target_empresa or empresa
    total = upsert_chunks(rows, client_id=client_id, empresa=write_empresa)
    return total


# ---------- LangGraph ingestion graph ----------

class IngestState(TypedDict, total=False):
    base_dir: str
    strategy: str
    strategies: List[str]
    client_id: Optional[str]
    empresa: Optional[str]
    skip_stage: bool
    skip_chunks: bool
    staged: int
    chunked: int
    processed: int
    chunk_size: Optional[int]
    chunk_overlap: Optional[int]


def node_stage(state: IngestState) -> IngestState:
    """Stage documents node."""
    if state.get("skip_stage"):
        return {"staged": 0}
    
    base_dir = state.get("base_dir", "kb")
    client_id = state.get("client_id")
    empresa = state.get("empresa")
    n = stage_docs_from_dir(base_dir, empresa=empresa, client_id=client_id)
    return {"staged": n}


def node_chunk(state: IngestState) -> IngestState:
    """Chunk documents node."""
    if state.get("skip_chunks"):
        return {"chunked": 0, "processed": 0}
    
    strategies: List[str] = []
    if isinstance(state.get("strategies"), list) and state.get("strategies"):
        strategies = [str(s).strip().lower() for s in state.get("strategies") or []]
    else:
        strategies = [str(state.get("strategy") or "semantic").strip().lower()]
    
    client_id = state.get("client_id")
    empresa = state.get("empresa")
    chunk_size = state.get("chunk_size") if isinstance(state.get("chunk_size"), int) else None
    chunk_overlap = state.get("chunk_overlap") if isinstance(state.get("chunk_overlap"), int) else None
    
    total = 0
    for s in strategies:
        kwargs: Dict[str, Any] = {
            "strategy": s,
            "empresa": empresa,
            "client_id": client_id,
            "doc_path_prefix": s,
        }
        if chunk_size is not None:
            kwargs["chunk_size"] = int(chunk_size)
        if chunk_overlap is not None:
            kwargs["chunk_overlap"] = int(chunk_overlap)
        n = materialize_chunks_from_staging(**kwargs)
        total += int(n or 0)
    
    return {"chunked": total, "processed": total}


def compile_ingest_graph():
    """Compile ingestion graph."""
    g = StateGraph(IngestState)
    g.add_node("stage_docs", node_stage)
    g.add_node("chunk_docs", node_chunk)
    g.set_entry_point("stage_docs")
    g.add_edge("stage_docs", "chunk_docs")
    g.set_finish_point("chunk_docs")
    return g.compile()


# Export graph for LangGraph Studio
graph = compile_ingest_graph()

