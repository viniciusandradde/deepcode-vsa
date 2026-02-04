from pathlib import Path
import pytest

# Fase 1: staging básico idempotente
pytestmark = pytest.mark.phase0

def test_kb_staging_idempotent(tmp_path: Path, db_ready):
    from app.rag.ingest import stage_docs_from_dir
    import psycopg

    kb = tmp_path / "kb"
    kb.mkdir()
    f = kb / "doc.md"
    f.write_text("Linha 1\n\nLinha 2", encoding="utf-8")

    n1 = stage_docs_from_dir(str(kb), empresa="Empresa Teste")
    assert n1 == 1
    n2 = stage_docs_from_dir(str(kb), empresa="Empresa Teste")
    assert n2 == 1  # inserções tentadas, mas segunda é no-op por hash/unique

    with psycopg.connect(db_ready) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from public.kb_docs where source_path=%s", (str(f.as_posix()),))
            c = cur.fetchone()[0]
            assert c == 1, "Staging deve manter apenas uma versão idêntica por (path,hash)"
