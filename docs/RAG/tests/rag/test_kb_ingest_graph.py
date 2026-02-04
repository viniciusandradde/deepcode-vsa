from pathlib import Path
import pytest

# Fase 1: grafo de ingestão
pytestmark = pytest.mark.phase0


def test_kb_ingest_graph_runs(tmp_path: Path, db_ready, require_openai):
    from app.rag.ingest import graph
    import psycopg

    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "doc.md").write_text("Politicas do Produto A com garantia.", encoding="utf-8")

    # Executa o grafo
    res = graph.invoke({"base_dir": str(kb), "strategy": "fixed", "empresa": "Empresa Teste"})
    processed = res.get("processed")
    assert isinstance(processed, int) and processed >= 1

    # Confere no banco
    with psycopg.connect(db_ready) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from public.kb_chunks where empresa=%s", ("Empresa Teste",))
            c = cur.fetchone()[0]
            assert c >= 1
