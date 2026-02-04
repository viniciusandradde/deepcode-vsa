import pytest

# Fase 1: política de filtros
pytestmark = pytest.mark.phase0
from unittest.mock import patch


def test_filter_priority_user_then_company(monkeypatch):
    """Exercita a prioridade de filtros: client_id -> empresa -> sem resultado.

    Nota: Este teste cria apenas o esqueleto de chamada; a inserção de dados no KB
    e a associação de client_id/empresa deve ser feita em testes de integração
    específicos quando o ambiente estiver provisionado.
    """
    from app.rag.tools import kb_search_client

    # (c) Sem filtros → erro lógico
    with pytest.raises(RuntimeError):
        kb_search_client.invoke({
            "query": "Termos do Produto A",
            "k": 3,
            "search_type": "hybrid",
            "reranker": "none",
            # sem client_id e sem empresa
        })

    # Para (b) e (a) evitamos dependências de DB/API usando monkeypatch dos candidatos
    with patch("app.rag.tools.query_candidates", return_value=[]):
        # (b) Com empresa apenas → permitido (não deve falhar por política)
        try:
            kb_search_client.invoke({
                "query": "Termos do Produto A",
                "k": 3,
                "search_type": "text",
                "reranker": "none",
                "empresa": "Empresa X",
            })
        except RuntimeError:
            pytest.fail("Consulta com filtro por empresa não deveria falhar por política")

        # (a) Com client_id → permitido (preferencial)
        try:
            kb_search_client.invoke({
                "query": "Termos do Produto A",
                "k": 3,
                "search_type": "vector",
                "reranker": "none",
                "client_id": "00000000-0000-0000-0000-000000000000",
            })
        except RuntimeError:
            pytest.fail("Consulta com filtro por client_id não deveria falhar por política")
