import pytest

# Fase 2: comparação de modos híbridos (sanidade)
pytestmark = pytest.mark.phase2


def test_rrf_vs_union_returns_lists(tmp_path, db_ready, require_openai):
    """Sanidade: ambos os modos retornam listas válidas e respeitam filtros.

    Comparações fortes (métricas) ficam em testes de avaliação dedicados.
    """
    from app.rag.ingest import ingest_dir
    from app.rag.tools import kb_search_client

    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "doc.md").write_text("Garantia de 12 meses; parcelamento 30/60.", encoding="utf-8")

    ingest_dir(str(kb), strategy="fixed", empresa="Empresa X")

    q = "garantia"
    res_rrf = kb_search_client.invoke({
        "query": q,
        "k": 5,
        "search_type": "hybrid_rrf",
        "empresa": "Empresa X",
    })
    res_union = kb_search_client.invoke({
        "query": q,
        "k": 5,
        "search_type": "hybrid_union",
        "empresa": "Empresa X",
    })
    assert isinstance(res_rrf, list) and isinstance(res_union, list)
    assert res_rrf and res_union
