"""RAG tools : kb_search_client with parameterizable search and optional reranking.

Filter policy:
- At least one of client_id, empresa, chunking, or project_id must be set.
"""

from typing import Any, Dict, List, Optional
import os

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from core.database import get_conn
from core.rag.embeddings import EmbeddingFactory


def vec_to_literal(v: List[float]) -> str:
    """Convert vector to pgvector literal."""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def query_candidates(
    query: str,
    k: int,
    search_type: str,
    client_id: Optional[str],
    empresa: Optional[str],
    chunking: Optional[str],
    query_embedding: Optional[List[float]],
    match_threshold: Optional[float],
    project_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get candidates from Postgres according to search type.

    Returns dicts with doc_path, chunk_ix, content, score, meta.
    """
    params: Dict[str, Any] = {
        "k": k,
        "client_id": client_id,
        "empresa": empresa,
        "chunking": chunking,
        "query": query,
        "threshold": match_threshold,
        "project_id": project_id,
    }

    with get_conn() as conn:
        with conn.cursor() as cur:
            results: List[Dict[str, Any]] = []
            if search_type in ("vector",):
                if not query_embedding:
                    raise RuntimeError("search_type=vector requires query embedding")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_vector_search(%(vec)s, %(k)s, %(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s, %(project_id)s)",
                    {**params, "vec": vec_lit},
                )
            elif search_type in ("text",):
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_text_search(%(query)s, %(k)s, %(client_id)s, %(empresa)s, %(chunking)s, %(project_id)s)",
                    params,
                )
            elif search_type in ("hybrid", "hybrid_rrf"):
                if query_embedding is None:
                    raise RuntimeError("search_type=hybrid requires query embedding")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_hybrid_search(%(query)s, %(vec)s, %(k)s, %(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s, %(project_id)s)",
                    {**params, "vec": vec_lit},
                )
            elif search_type in ("hybrid_union",):
                if query_embedding is None:
                    raise RuntimeError("search_type=hybrid_union requires query embedding")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_hybrid_union(%(query)s, %(vec)s, %(k)s, %(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s, %(project_id)s)",
                    {**params, "vec": vec_lit},
                )
            else:
                raise ValueError(f"Unknown search_type: {search_type}")

            for row in cur.fetchall() or []:
                results.append(
                    {
                        "doc_path": row[0],
                        "chunk_ix": row[1],
                        "content": row[2],
                        "score": float(row[3]) if row[3] is not None else None,
                        "meta": row[4] or {},
                    }
                )
            return results


def apply_rerank(
    query: str, items: List[Dict[str, Any]], reranker: str, k: int
) -> List[Dict[str, Any]]:
    """Apply reranking to search results."""
    if reranker == "none" or not items:
        return items[:k]

    if reranker == "cohere":
        try:
            from langchain_cohere import CohereRerank
        except Exception as e:
            raise RuntimeError(
                "Reranker 'cohere' requested but langchain-cohere package not available"
            ) from e

        if not os.getenv("COHERE_API_KEY"):
            raise RuntimeError("Reranker 'cohere' requested but COHERE_API_KEY not defined")

        reranker_model = CohereRerank(model="rerank-english-v3.0")
        docs = [it["content"] for it in items]

        # Try multiple APIs for version compatibility
        results = None
        if hasattr(reranker_model, "rank"):
            results = reranker_model.rank(query=query, documents=docs)
        elif hasattr(reranker_model, "rerank"):
            results = reranker_model.rerank(query=query, documents=docs)
        else:
            try:
                results = reranker_model.invoke({"query": query, "documents": docs})
            except Exception:
                results = None

        # Reconstruct order from reranked results
        if isinstance(results, list) and results:

            def _get_content_and_score(obj):
                c = getattr(obj, "document", None)
                if c is not None:
                    txt = getattr(c, "page_content", None) or getattr(c, "text", None) or str(c)
                else:
                    txt = getattr(obj, "page_content", None) or getattr(obj, "text", None)
                if txt is None and isinstance(obj, dict):
                    d = obj.get("document") or obj
                    txt = d.get("text") or d.get("page_content") or str(d)
                score = getattr(obj, "relevance_score", None)
                if score is None and isinstance(obj, dict):
                    score = obj.get("relevance_score")
                return (str(txt or ""), float(score or 0.0))

            res_pairs = [_get_content_and_score(r) for r in results]
            from collections import defaultdict, deque

            idx_map = defaultdict(deque)
            for i, d in enumerate(docs):
                idx_map[d].append(i)
            ordered = []
            for content, _score in res_pairs:
                if content in idx_map and idx_map[content]:
                    i = idx_map[content].popleft()
                    ordered.append(items[i])
            if ordered:
                return ordered[:k]

        # Fallback: return original top-k
        return items[:k]

    # Future rerankers can be added here
    return items[:k]


def _get_project_embedding_model(project_id: str) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT embedding_model FROM planning_projects WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Projeto não encontrado para busca RAG")
            model = row[0] if isinstance(row, tuple) else row.get("embedding_model")
            return (model or "openai").strip().lower()


def hyde(query: str) -> str:
    """Generate a hypothetical relevant document (HyDE) to expand the query.

    KISS: uses ChatOpenAI with light model; controls low temperature.
    """
    llm = ChatOpenAI(model=(os.getenv("HYDE_LLM_MODEL") or "gpt-4o-mini"), temperature=0.3)
    prompt = (
        "Escreva um parágrafo conciso que seria altamente relevante para a seguinte pergunta,"
        " simulando um documento técnico real.\nPergunta: " + query
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
    project_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    use_hyde: bool = False,
    match_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search KB with filters and optional reranking.

    Filter policy: at least one of client_id, empresa, chunking, or project_id must be set.
    """
    # Filter policy: allow query when any filter is set
    if not client_id and not empresa and not chunking and not project_id:
        raise RuntimeError(
            "KB query without filter (client_id/empresa/chunking/project_id) is not allowed"
        )

    # Embedding only when necessary (usa OPENAI_API_KEY, não OpenRouter)
    query_emb: Optional[List[float]] = None
    if search_type != "text":
        if project_id:
            model_id = _get_project_embedding_model(project_id)
            emb = EmbeddingFactory.get_model(model_id)
        else:
            emb = EmbeddingFactory.get_model("openai")
        q_for_embed = hyde(query) if use_hyde else query
        query_emb = emb.embed_query(q_for_embed)

    # Candidates from Postgres
    candidates = query_candidates(
        query,
        rerank_candidates or k,
        search_type,
        client_id,
        empresa,
        chunking,
        query_emb,
        match_threshold,
        project_id=project_id,
    )

    # Optional reranking
    final = apply_rerank(query, candidates, reranker, k)
    return final
