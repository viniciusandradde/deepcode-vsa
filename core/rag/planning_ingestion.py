"""RAG ingestion for planning documents: chunking, embedding, persistence by project_id."""

import logging
from json import dumps
from uuid import UUID

from core.database import get_conn
from core.rag.loaders import load_document_from_bytes, split_text
from core.rag.ingestion import embed_texts, vec_to_literal

logger = logging.getLogger(__name__)


async def ingest_project_document_task(
    project_id: UUID,
    document_id: UUID,
    content_bytes: bytes,
    filename: str,
) -> None:
    """
    Processa documento em background: Chunking (Markdown/Fixed) -> Embedding -> DB (com project_id).
    """
    try:
        logger.info("Iniciando ingestão RAG: %s (Proj: %s)", filename, project_id)

        # 1. Carregar texto
        text = load_document_from_bytes(content_bytes, filename)

        # 2. Chunking inteligente
        strategy = "markdown" if filename.lower().endswith(".md") else "fixed"
        chunks, _ = split_text(text, strategy=strategy, chunk_size=1000, chunk_overlap=200)

        if not chunks:
            logger.warning("Nenhum chunk gerado para %s", filename)
            return

        chunk_texts = [c["content"] for c in chunks]
        vectors = embed_texts(chunk_texts)

        # 3. Persistência isolada
        doc_path_prefix = f"planning/{project_id}/{filename}"
        rows = []
        for i, (c, vec) in enumerate(zip(chunks, vectors)):
            rows.append({
                "doc_path": doc_path_prefix,
                "chunk_ix": i,
                "content": c["content"],
                "embedding": vec,
                "meta": {
                    "source": "planning",
                    "doc_id": str(document_id),
                    "file": filename,
                },
            })

        _upsert_planning_chunks(rows, project_id)
        logger.info("Sucesso: %s chunks indexados para %s", len(rows), filename)

    except Exception as e:
        logger.error(
            "Falha na ingestão do documento %s: %s",
            document_id,
            e,
            exc_info=True,
        )


def _upsert_planning_chunks(rows: list, project_id: UUID) -> None:
    """Insere ou atualiza chunks em kb_chunks com project_id."""
    if not rows:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO kb_chunks
                    (doc_path, chunk_ix, content, embedding, meta, project_id)
                    VALUES (%s, %s, %s, %s::vector(1536), %s::jsonb, %s::uuid)
                    ON CONFLICT (doc_path, chunk_ix)
                    DO UPDATE SET
                        content = excluded.content,
                        embedding = excluded.embedding,
                        meta = excluded.meta,
                        project_id = excluded.project_id
                    """,
                    (
                        r["doc_path"],
                        r["chunk_ix"],
                        r["content"],
                        vec_to_literal(r["embedding"]),
                        dumps(r["meta"]),
                        str(project_id),
                    ),
                )
