from pathlib import Path
import pytest

# Fase 2: estratégias de busca e filtros
pytestmark = pytest.mark.phase2

def test_retrieval_hybrid_filters_and_relevance(tmp_path: Path, db_ready, require_openai):
    from app.rag.ingest import ingest_dir
    from app.rag.tools import kb_search_client

    # Monta KB para duas empresas
    kb = tmp_path / "kb"
    (kb / "empresa_x").mkdir(parents=True)
    (kb / "empresa_y").mkdir(parents=True)

    fx = kb / "empresa_x" / "produto_a.md"
    fx.write_text("""
# Produto A — Políticas (Empresa X)
[KB_TEST_EMPRESA_X] O Produto A possui garantia de 12 meses e permite pagamento em 30/60 dias.
""".strip(), encoding="utf-8")

    fy = kb / "empresa_y" / "produto_a.md"
    fy.write_text("""
# Produto A — Políticas (Empresa Y)
[KB_TEST_EMPRESA_Y] Para Empresa Y, política diferente sem menção à garantia de 12 meses.
""".strip(), encoding="utf-8")

    # Ingestão com filtro de empresa (nome único p/ isolar do banco compartilhado)
    import uuid as _uuid
    empresa_x_name = f"Empresa X {str(_uuid.uuid4())[:8]}"
    empresa_y_name = f"Empresa Y {str(_uuid.uuid4())[:8]}"
    n1 = ingest_dir(str(kb / "empresa_x"), strategy="markdown", empresa=empresa_x_name)
    n2 = ingest_dir(str(kb / "empresa_y"), strategy="markdown", empresa=empresa_y_name)
    assert n1 >= 1 and n2 >= 1

    query = "garantia de 12 meses"

    # TEXT
    res_text = kb_search_client.invoke({
        "query": query,
        "k": 5,
        "search_type": "text",
        "reranker": "none",
        "empresa": empresa_x_name,
    })
    assert isinstance(res_text, list)
    assert res_text, "Nenhum resultado em TEXT"
    assert all("[kb_test_empresa_x]" in (it["content"] or "").lower() for it in res_text)
    assert all("[kb_test_empresa_y]" not in (it["content"] or "").lower() for it in res_text)

    # VECTOR
    res_vec = kb_search_client.invoke({
        "query": query,
        "k": 5,
        "search_type": "vector",
        "reranker": "none",
        "empresa": empresa_x_name,
    })
    assert isinstance(res_vec, list)
    assert res_vec, "Nenhum resultado em VECTOR"
    assert all("[kb_test_empresa_x]" in (it["content"] or "").lower() for it in res_vec)
    assert all("[kb_test_empresa_y]" not in (it["content"] or "").lower() for it in res_vec)

    # HYBRID
    res_hybrid = kb_search_client.invoke({
        "query": query,
        "k": 5,
        "search_type": "hybrid",
        "reranker": "none",
        "empresa": empresa_x_name,
    })
    assert isinstance(res_hybrid, list)
    assert res_hybrid, "Nenhum resultado em HYBRID"
    assert all("[kb_test_empresa_x]" in (it["content"] or "").lower() for it in res_hybrid)
    assert all("[kb_test_empresa_y]" not in (it["content"] or "").lower() for it in res_hybrid)
