import os
from pathlib import Path
import yaml
import psycopg
import pytest
from langchain_core.messages import HumanMessage

# Fase 3 — avaliação E2E do agente usando o mesmo dataset (rag_queries.yaml)
pytestmark = pytest.mark.phase3


def _load_dataset() -> list[dict]:
    qdir = Path(__file__).resolve().parents[0]
    ds_file = qdir / "rag_queries.yaml"
    assert ds_file.exists(), "Arquivo 'tests/rag/rag_queries.yaml' ausente"
    ds = yaml.safe_load(ds_file.read_text(encoding="utf-8")) or {}
    return ds.get("queries") or []


def test_phase3_agent_dataset_llm_judge(db_ready, require_openai, llm_judge_yesno):
    """Executa o agente proposal_agent_v2 sobre o dataset e avalia apenas a resposta final (LLM-judge).

    - Usa KB já materializado (Fase 0). Sem ingestões ad-hoc aqui.
    - O agente é isolado (somente RAG) e deve chamar kb_search_client com 'chunking'.
    - Fast mode: RAG_FAST=1 (limita a ~10 perguntas) ou RAG_MAX_Q=<n>.
    """
    from app.rag.proposal_agent_v2 import graph

    # Garante que há KB materializado para o chunking esperado (default semantic)
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

    queries = _load_dataset()
    # Amostragem rápida
    max_q = None
    if (os.getenv("RAG_FAST", "").strip().lower() in ("1", "true", "yes", "on")):
        max_q = 10
    elif os.getenv("RAG_MAX_Q", "").strip().isdigit():
        try:
            max_q = int(os.getenv("RAG_MAX_Q"))
        except Exception:
            max_q = None
    if max_q:
        queries = queries[:max_q]

    total = 0
    lyes = 0
    for q in queries:
        pergunta = q.get("pergunta") or q.get("question")
        judge_expected = q.get("answer") or q.get("expected") or ", ".join(q.get("expected_all") or [])
        if not (pergunta and judge_expected):
            continue
        total += 1

        # O agente tem prompt orientando a usar chunking e ajustar threshold; aqui passamos apenas a pergunta
        state = graph.invoke({"messages": [HumanMessage(content=pergunta)]})
        messages = state.get("messages") or []
        raw = messages[-1].content if messages and hasattr(messages[-1], "content") else ""
        # Responses API pode devolver lista de partes; extrai o texto
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

        try:
            ok = llm_judge_yesno(pergunta, judge_expected, [answer])
        except Exception:
            ok = False
        lyes += 1 if ok else 0

    # Impressão do resultado agregado
    rate = round(lyes / max(total, 1), 2)
    print("\n=== PHASE 3 — AGENT (LLM-JUDGE SOBRE DATASET) ===")
    print(f"chunking={chunking} | total={total} | llm_yes={rate:0.2f}")

    # Critério mínimo: ao menos 0.5 de llm_yes na amostra
    assert rate >= 0.5, "Desempenho insuficiente do agente (llm_yes < 0.5)"
