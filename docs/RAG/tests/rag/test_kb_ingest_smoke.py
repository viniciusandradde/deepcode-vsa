from pathlib import Path
import pytest

# Fase 1: ingestão mínima e verificação no banco
pytestmark = pytest.mark.phase0

def test_kb_ingest_smoke(tmp_path: Path, db_ready, require_openai):
    from app.rag.ingest import ingest_dir
    import psycopg

    # Cria um KB mínimo com 1 arquivo
    kb = tmp_path / "kb"
    kb.mkdir()
    f = kb / "produto_a.md"
    f.write_text("""
# Produto A — Políticas
Oferece pagamento em 30/60 dias. Garantia padrão de 12 meses.
""".strip(), encoding="utf-8")

    # Ingestão 1
    n1 = ingest_dir(str(kb), strategy="markdown")
    assert n1 >= 1

    # Verifica no banco quantos registros desse doc existem
    with psycopg.connect(db_ready) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from public.kb_chunks where doc_path like %s", (str(f.as_posix()),))
            c1 = cur.fetchone()[0]
            assert c1 >= 1

    # Ingestão 2 (idempotente)
    n2 = ingest_dir(str(kb), strategy="markdown")
    assert n2 >= 1
    with psycopg.connect(db_ready) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from public.kb_chunks where doc_path like %s", (str(f.as_posix()),))
            c2 = cur.fetchone()[0]
            assert c2 == c1
