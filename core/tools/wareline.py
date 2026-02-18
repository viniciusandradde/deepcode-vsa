"""Wareline hospital catalog search tool.

Queries the wareline_rag.wareline_embeddings table for hospital system
table/column documentation using semantic (vector) search.
"""

import logging
import os
from typing import Optional

from langchain_core.tools import tool

from core.database import get_conn

logger = logging.getLogger(__name__)

# Embedding model used for the wareline catalog (BGE-M3, 1024 dims)
_EMBEDDING_MODEL_ID = "openrouter-bge-m3"


def _get_embedding_model():
    """Lazy-load the embedding model for query vectorization."""
    from core.rag.embeddings import EmbeddingFactory

    return EmbeddingFactory.get_model(_EMBEDDING_MODEL_ID)


def get_wareline_domains() -> list[dict]:
    """Return distinct domains from wareline_embeddings with table counts."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT domain,
                           COUNT(DISTINCT table_name) AS table_count
                    FROM wareline_rag.wareline_embeddings
                    WHERE domain IS NOT NULL AND domain != ''
                    GROUP BY domain
                    ORDER BY domain
                """)
                rows = cur.fetchall()
                return [
                    {"domain": row[0], "table_count": row[1]}
                    for row in rows
                ]
    except Exception as e:
        logger.warning("Failed to fetch wareline domains: %s", e)
        return []


def search_wareline_catalog(
    query: str,
    domain: Optional[str] = None,
    limit: int = 10,
    threshold: float = 0.3,
) -> str:
    """Search the Wareline hospital catalog using semantic similarity.

    Args:
        query: Natural language search query.
        domain: Optional domain filter (e.g. "FATURAMENTO").
        limit: Max results to return.
        threshold: Minimum similarity threshold.

    Returns:
        Formatted context string with matching tables/columns.
    """
    try:
        model = _get_embedding_model()
        query_embedding = model.embed_query(query)

        with get_conn() as conn:
            with conn.cursor() as cur:
                if domain:
                    cur.execute("""
                        SELECT table_name, column_name, description, domain,
                               1 - (embedding <=> %s::vector) AS similarity
                        FROM wareline_rag.wareline_embeddings
                        WHERE domain = %s
                          AND 1 - (embedding <=> %s::vector) > %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, domain.upper(), query_embedding, threshold, query_embedding, limit))
                else:
                    cur.execute("""
                        SELECT table_name, column_name, description, domain,
                               1 - (embedding <=> %s::vector) AS similarity
                        FROM wareline_rag.wareline_embeddings
                        WHERE 1 - (embedding <=> %s::vector) > %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, query_embedding, threshold, query_embedding, limit))

                rows = cur.fetchall()

        if not rows:
            domain_msg = f" no domínio {domain}" if domain else ""
            return f"Nenhuma tabela encontrada{domain_msg} para: {query}"

        # Format results grouped by table
        tables: dict[str, list[str]] = {}
        for table_name, column_name, description, dom, similarity in rows:
            key = f"{table_name} ({dom})"
            if key not in tables:
                tables[key] = []
            col_desc = f"  - `{column_name}`: {description}" if description else f"  - `{column_name}`"
            tables[key].append(f"{col_desc} (sim: {similarity:.2f})")

        parts = []
        for table_key, columns in tables.items():
            parts.append(f"### {table_key}")
            parts.extend(columns)

        return "\n".join(parts)

    except Exception as e:
        logger.exception("Wareline catalog search failed: %s", e)
        return f"Erro na busca do catálogo Wareline: {e}"


@tool
def wareline_search_tables(query: str, domain: str = "") -> str:
    """Busca tabelas e colunas no catálogo do sistema hospitalar Wareline/MV.

    Use para encontrar tabelas, colunas e suas descrições no banco de dados
    hospitalar. Útil para consultas sobre faturamento, prontuário, estoque,
    farmácia, internação, etc.

    Args:
        query: Pergunta ou termos de busca (ex: "tabelas de convênio").
        domain: Domínio opcional para filtrar (ex: "FATURAMENTO", "FARMACIA").
    """
    return search_wareline_catalog(
        query=query,
        domain=domain if domain else None,
        limit=10,
        threshold=0.25,
    )
