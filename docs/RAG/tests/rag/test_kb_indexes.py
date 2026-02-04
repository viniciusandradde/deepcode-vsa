import psycopg
import pytest

# Fase 1: verificação de índices
pytestmark = pytest.mark.phase0


def test_kb_indexes_exist(db_ready):
    """Verifica existência de índices criados para KB (HNSW, GIN e auxiliares)."""
    with psycopg.connect(db_ready) as conn:
        with conn.cursor() as cur:
            names = {
                "ix_kb_chunks_embedding_hnsw",
                "ix_kb_chunks_fts_gin",
                "ix_kb_chunks_doc",
                "ix_kb_chunks_empresa",
                "ix_kb_chunks_client",
            }
            cur.execute(
                """
                select indexname
                from pg_indexes
                where schemaname = 'public' and tablename = 'kb_chunks'
                """
            )
            present = {r[0] for r in (cur.fetchall() or [])}
            missing = sorted(names - present)
            assert not missing, f"Índices ausentes: {missing}"
