from langchain_core.messages import HumanMessage
import pytest
import os
import psycopg

# Fase 3: avaliação E2E do agente (isolado, somente RAG)
pytestmark = pytest.mark.phase3


def test_proposal_agent_v2_llm_judge(monkeypatch, db_ready, require_openai):
    """E2E com LLM como juiz, usando KB já materializado (fase 0) e agente isolado (somente RAG)."""
    from app.rag.proposal_agent_v2 import graph
    from langchain_openai import ChatOpenAI

    # Verifica se há KB materializado para o chunking escolhido
    chunking = (os.environ.get("PROPOSAL_CHUNKING") or "semantic").strip()
    try:
        with psycopg.connect(db_ready) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select count(*) from public.kb_chunks where meta->>'chunking'=%s",
                    (chunking,),
                )
                if (cur.fetchone() or [0])[0] == 0:
                    pytest.skip("KB vazio para a estratégia escolhida. Rode `make rag_phase0`." )
    except Exception:
        pytest.skip("Não foi possível validar KB; verifique conexão/ingestão prévia.")

    # Modelo: usar gpt-5 (consistente com workflow)
    monkeypatch.setenv("PROPOSAL_LLM_MODEL", "gpt-5-nano")

    # Prompt do usuário: não inclui empresa/CRM; agente deve recuperar via chunking global
    prompt = (
        "Gerar uma proposta sucinta do Produto A, incluindo condições de pagamento e garantia. "
        "Use apenas informações recuperadas do KB da base (filtrada por chunking) e ajuste match_threshold se necessário."
    )
    state = graph.invoke({"messages": [HumanMessage(content=prompt)]})
    messages = state.get("messages") or []
    assert messages, "Sem mensagens de saída do grafo"
    raw = messages[-1].content if hasattr(messages[-1], "content") else ""
    # Responses API: extrai texto
    if isinstance(raw, list):
        parts = []
        for it in raw:
            if isinstance(it, dict) and it.get("type") in ("text", "output_text"):
                t = it.get("text") or ""
                if t:
                    parts.append(t)
        answer = "\n".join(parts)
    else:
        answer = raw if isinstance(raw, str) else str(raw)
    assert answer.strip(), "Resposta vazia do agente"

    # LLM-judge: deve reconhecer 30/60 e/ou 12 meses
    judge = ChatOpenAI(model="gpt-4.1-2025-04-14", temperature=0)
    judge_prompt = (
        "Você é um avaliador. Dado o texto da resposta abaixo, responda apenas com 'sim' ou 'não' "
        "se a resposta contempla políticas de pagamento parcelado (ex.: 30/60 dias) e/ou garantia de 12 meses.\n\n"
        f"RESPOSTA:\n{answer}\n"
        "\nSaída: apenas 'sim' ou 'não'."
    )
    verdict = (judge.invoke(judge_prompt).content or "").strip().lower()
    assert verdict in ("sim", "não"), f"Saída inesperada do juiz: {verdict}"
    assert verdict == "sim", "Resposta do agente não refletiu as políticas recuperadas do KB"
