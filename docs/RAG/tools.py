"""
Ferramentas RAG: `kb_search_client` com busca parametrizável e reranking opcional.

Política de filtros:
- Prioridade: client_id > empresa; sem filtro → não consulta (erro lógico no proposal_agent_v2).
"""

from typing import Any, Dict, List, Optional
import os

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from app.agent.tools import get_conn


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
    """Obtém candidatos do Postgres conforme o tipo de busca.

    Retorna dicts com doc_path, chunk_ix, content, score, meta.
    """
    params: Dict[str, Any] = {
        "k": k,
        "client_id": client_id,
        "empresa": empresa,
        "chunking": chunking,
        "query": query,
        "threshold": match_threshold,
    }
    with get_conn() as conn:
        with conn.cursor() as cur:
            results: List[Dict[str, Any]] = []
            if search_type in ("vector",):
                if not query_embedding:
                    raise RuntimeError("search_type=vector requer embedding da query")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_vector_search(%(vec)s, %(k)s, %(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s)",
                    {**params, "vec": vec_lit},
                )
            elif search_type in ("text",):
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_text_search(%(query)s, %(k)s, %(client_id)s, %(empresa)s, %(chunking)s)",
                    params,
                )
            elif search_type in ("hybrid", "hybrid_rrf"):
                if query_embedding is None:
                    raise RuntimeError("search_type=hybrid requer embedding da query")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_hybrid_search(%(query)s, %(vec)s, %(k)s, %(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s)",
                    {**params, "vec": vec_lit},
                )
            elif search_type in ("hybrid_union",):
                if query_embedding is None:
                    raise RuntimeError("search_type=hybrid_union requer embedding da query")
                vec_lit = vec_to_literal(query_embedding)
                cur.execute(
                    "select doc_path, chunk_ix, content, score, meta from public.kb_hybrid_union(%(query)s, %(vec)s, %(k)s, %(threshold)s, %(client_id)s, %(empresa)s, %(chunking)s)",
                    {**params, "vec": vec_lit},
                )
            for row in cur.fetchall() or []:
                results.append({
                    "doc_path": row[0],
                    "chunk_ix": row[1],
                    "content": row[2],
                    "score": float(row[3]) if row[3] is not None else None,
                    "meta": row[4] or {},
                })
            return results


def apply_rerank(query: str, items: List[Dict[str, Any]], reranker: str, k: int) -> List[Dict[str, Any]]:
    if reranker == "none" or not items:
        return items[:k]
    if reranker == "cohere":
        # Tenta usar LangChain Cohere rerank; se indisponível, sinaliza claramente
        try:
            from langchain_cohere import CohereRerank
        except Exception as e:
            raise RuntimeError("Reranker 'cohere' solicitado, mas pacote langchain-cohere não está disponível") from e
        if not os.getenv("COHERE_API_KEY"):
            raise RuntimeError("Reranker 'cohere' solicitado, mas COHERE_API_KEY não está definido")
        reranker_model = CohereRerank(model="rerank-english-v3.0")
        docs = [it["content"] for it in items]
        # Tenta múltiplas APIs para compatibilidade de versões
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

        # Se retornou lista ordenada, tentamos reconstruir a ordem original por conteúdo
        if isinstance(results, list) and results:
            # Extrai conteúdo e score de cada entrada
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
            # Mapa doc->fila de índices (suporta possíveis duplicidades)
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

        # Fallback: não conseguiu reordenar, retorna top-k original
        return items[:k]
    # Futuros rerankers podem ser adicionados aqui
    return items[:k]


def hyde(query: str) -> str:
    """Gera um documento hipotético relevante (HyDE) para expandir a consulta.

    KISS: usa ChatOpenAI com modelo leve; controla temperatura baixa.
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
    tags: Optional[List[str]] = None,
    use_hyde: bool = False,
    match_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Busca em KB com filtros e reranking opcional.

    Política de filtros:
    - Preferir client_id quando disponível; caso contrário, empresa.
    - Para cenários de teste/benchmark, permitimos consulta global quando houver filtro por 'chunking'.
    """
    # Política de filtros
    if not client_id and not empresa and not chunking:
        raise RuntimeError("Consulta ao KB sem filtro (client_id/empresa) ou sem 'chunking' não é permitida")

    # Embedding apenas quando necessário
    query_emb: Optional[List[float]] = None
    if search_type != "text":
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        q_for_embed = hyde(query) if use_hyde else query
        query_emb = emb.embed_query(q_for_embed)

    # Candidatos do Postgres
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

    # Reranking opcional
    final = apply_rerank(query, candidates, reranker, k)
    return final
