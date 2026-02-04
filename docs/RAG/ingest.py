"""
Ingestão simples de `.md` → chunks → embeddings → upsert no Postgres.

Exporta também um grafo `rag_ingest` (LangGraph) para acionar pipeline no Studio.
"""

from typing import List, Dict, Any, Optional, TypedDict

from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, END

from app.rag.loaders import load_and_split_dir, split_text
from app.agent.tools import get_conn  # reutiliza utilitário existente
from json import dumps as json_dumps
import hashlib
from pathlib import Path
import mimetypes
import os


def vec_to_literal(v: List[float]) -> str:
    """Converte vetor de floats em literal aceito pelo pgvector: "[v1, v2, ...]"."""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Gera embeddings para os textos (OpenAI)."""
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return emb.embed_documents(texts)


def upsert_chunks(rows: List[Dict[str, Any]], *, client_id: Optional[str] = None, empresa: Optional[str] = None) -> int:
    """Upsert idempotente por (doc_path, chunk_ix). Retorna quantidade afetada."""
    if not rows:
        return 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            count = 0
            for r in rows:
                vec_lit = vec_to_literal(r["embedding"])  # texto "[x,y,...]"
                # Evita erro de prepared statement duplicado no psycopg3 em execuções repetidas
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


def ingest_dir(base_dir: str = "kb", *, strategy: str = "semantic", client_id: Optional[str] = None, empresa: Optional[str] = None, chunk_size: int = 800, chunk_overlap: int = 200) -> int:
    """Pipeline: carrega .md, divide, embeda e upserta. Retorna total processado."""
    # Para semantic chunking usamos embeddings também; senão, None
    embedder = OpenAIEmbeddings(model="text-embedding-3-small") if strategy == "semantic" else None
    chunks = load_and_split_dir(base_dir, strategy=strategy, embedder=embedder, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = [it["content"] for it in chunks]
    vectors = embed_texts(texts)
    rows = []
    for it, vec in zip(chunks, vectors):
        it2 = dict(it)
        it2["embedding"] = vec
        rows.append(it2)
    return upsert_chunks(rows, client_id=client_id, empresa=empresa)


# ---------- Staging (kb_docs) ----------

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def stage_docs_from_dir(base_dir: str = "kb", *, empresa: Optional[str] = None, client_id: Optional[str] = None) -> int:
    """Lê arquivos .md do diretório e insere em kb_docs (staging), idempotente por (source_path, source_hash)."""
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
    """Trunca as tabelas do KB (staging e chunks) para uma execução limpa.

    Use com cuidado: remove TODO o conteúdo de public.kb_docs e public.kb_chunks.
    """
    with get_conn() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("truncate table public.kb_chunks;")
            cur.execute("truncate table public.kb_docs;")


def materialize_chunks_from_staging(*, strategy: str = "semantic", empresa: Optional[str] = None, client_id: Optional[str] = None, chunk_size: int = 800, chunk_overlap: int = 200, path_prefix: Optional[str] = None, target_empresa: Optional[str] = None, doc_path_prefix: Optional[str] = None) -> int:
    """Lê kb_docs (filtra por empresa/path_prefix) e materializa kb_chunks com a estratégia indicada.

    - Seleção: filtra linhas em kb_docs por `empresa` e opcionalmente por `path_prefix`.
    - Escrita: grava em kb_chunks usando `target_empresa` se fornecida; caso contrário, usa `empresa`.
    - Idempotente por (doc_path, chunk_ix) — sobrescreve o mesmo par no upsert.
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
                # Filtra por prefixo do caminho do arquivo (staging). Usa LIKE 'prefix%'
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
    # Decide embedder para semantic
    embedder = OpenAIEmbeddings(model="text-embedding-3-small") if strategy == "semantic" else None
    total = 0
    rows: List[Dict[str, Any]] = []
    for _id, source_path, content in docs:
        chunks, resolved = split_text(content, strategy=strategy, embedder=embedder, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for i, c in enumerate(chunks):
            # Para cenários comparativos (testes), opcionalmente prefixamos o doc_path para evitar colisão no upsert
            new_doc_path = source_path
            if doc_path_prefix:
                # Mantém o basename original no final para legibilidade
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
    # Grava em kb_chunks com a empresa alvo (permite comparar estratégias sem conflitar no filtro)
    write_empresa = target_empresa or empresa
    total = upsert_chunks(rows, client_id=client_id, empresa=write_empresa)
    return total


# ---------- Grafo de ingestão (opcional) ----------

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
    processed: int  # alias para chunked (compatibilidade)
    # parâmetros de chunking (opcionais)
    chunk_size: Optional[int]
    chunk_overlap: Optional[int]


def _resolve_base_dir(requested: Optional[str]) -> str:
    """Resolve o diretório base com fallback inteligente.

    Ordem de escolha:
    1. Valor explicitamente fornecido (se existir e conter .md)
    2. Variável de ambiente BASE_DIR (se existir e conter .md)
    3. Diretório "kb" no CWD (se existir e conter .md)
    4. Dataset didático em tests/rag/data (relativo à raiz do repo)
    """
    def has_md(p: Path) -> bool:
        try:
            return p.exists() and any(p.rglob("*.md"))
        except Exception:
            return False

    # 1) explícito
    if requested:
        p = Path(requested)
        if not p.is_absolute():
            p = (Path.cwd() / p)
        if has_md(p):
            return str(p)

    # 2) env
    env_dir = os.getenv("BASE_DIR")
    if env_dir:
        p = Path(env_dir)
        if not p.is_absolute():
            p = (Path.cwd() / p)
        if has_md(p):
            return str(p)

    # 3) kb no CWD
    p_kb = Path.cwd() / "kb"
    if has_md(p_kb):
        return str(p_kb)

    # 4) tests/rag/data relativo à raiz do repo (../.. a partir de app/rag/ingest.py)
    repo_root = Path(__file__).resolve().parents[2]
    p_ds = repo_root / "tests" / "rag" / "data"
    if has_md(p_ds):
        return str(p_ds)

    # Último recurso: devolve string original ou "kb" (não deve acontecer)
    return requested or "kb"


def node_stage(state: IngestState) -> IngestState:
    if state.get("skip_stage"):
        return {"staged": 0}
    # Resolve base_dir com fallback para evitar execuções "vazias"
    base_dir = _resolve_base_dir(state.get("base_dir"))
    client_id = state.get("client_id")
    empresa = state.get("empresa")
    n = stage_docs_from_dir(base_dir, empresa=empresa, client_id=client_id)
    return {"staged": n}


def node_chunk(state: IngestState) -> IngestState:
    if state.get("skip_chunks"):
        return {"chunked": 0, "processed": 0}
    # Suporta uma ou várias estratégias. Default: semantic
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
            # doc_path_prefix evita colisão quando materializamos múltiplas estratégias
            "doc_path_prefix": s,
        }
        if chunk_size is not None:
            kwargs["chunk_size"] = int(chunk_size)
        if chunk_overlap is not None:
            kwargs["chunk_overlap"] = int(chunk_overlap)
        n = materialize_chunks_from_staging(**kwargs)
        total += int(n or 0)

    return {"chunked": total, "processed": total}


def compile_graph():
    g = StateGraph(IngestState)
    g.add_node("stage_docs", node_stage)
    g.add_node("chunk_docs", node_chunk)
    g.set_entry_point("stage_docs")
    g.add_edge("stage_docs", "chunk_docs")
    g.set_finish_point("chunk_docs")
    return g.compile()

graph = compile_graph()
