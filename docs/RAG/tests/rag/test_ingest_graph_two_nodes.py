 
import pytest

# Fase 0: grafo de ingestão em dois passos
pytestmark = pytest.mark.phase0


def test_ingest_graph_two_nodes(tmp_path, db_ready, require_openai):
    from app.rag.ingest import graph
    import psycopg
    

    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "doc.md").write_text("Política Empresa Z: 30/60 e 12 meses.", encoding="utf-8")

    # 1) Apenas staging
    res1 = graph.invoke({
        "base_dir": str(kb),
        "empresa": "Empresa Z",
        "skip_chunks": True,
    })
    assert res1.get("staged") is not None

    # 2) Apenas chunking (pula staging)
    res2 = graph.invoke({
        "empresa": "Empresa Z",
        "strategy": "markdown",
        "skip_stage": True,
    })
    assert res2.get("chunked") is not None
    assert res2.get("processed") == res2.get("chunked")

    # Confirma no banco
    with psycopg.connect(db_ready) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from public.kb_docs where lower(empresa)=lower('Empresa Z')")
            c_docs = cur.fetchone()[0]
            cur.execute("select count(*) from public.kb_chunks where lower(empresa)=lower('Empresa Z')")
            c_chunks = cur.fetchone()[0]
            assert c_docs >= 1 and c_chunks >= 1
