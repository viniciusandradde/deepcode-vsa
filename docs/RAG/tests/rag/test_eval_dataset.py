import yaml
from pathlib import Path
import psycopg
import pytest
import os




def _choose_best_chunking(conn_str: str, empresa: str = "Empresa X") -> str:
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select meta->>'chunking' as c, count(*) from public.kb_chunks where lower(empresa)=lower(%s) group by 1",
                (empresa,),
            )
            counts = {r[0]: r[1] for r in (cur.fetchall() or [])}
    for c in ("semantic", "markdown", "fixed"):
        if counts.get(c):
            return c
    return "markdown"


def test_eval_dataset_llm_judge_comparison(capsys, db_ready, require_openai, llm_judge_yesno):
    if os.getenv("RAG_PHASE2_LEGACY", "").strip().lower() not in ("1", "true", "yes", "on"):
        pytest.skip("Teste legacy da Fase 2 desativado (defina RAG_PHASE2_LEGACY=1 para habilitar)")
    """Compara hybrid_rrf vs hybrid_union usando o dataset principal (rag_queries.yaml), fixando o melhor chunking presente.

    Pré‑requisito: KB materializado (Fase 0). Não faz ingestão aqui.
    """
    from app.rag.tools import kb_search_client

    empresa = "Empresa X"
    chosen_chunking = _choose_best_chunking(db_ready, empresa)

    # Carrega dataset (reutiliza o da Fase 1 para consistência)
    qdir = Path(__file__).resolve().parents[0]
    ds_file = qdir / "rag_queries.yaml"
    assert ds_file.exists(), "Arquivo 'tests/rag/rag_queries.yaml' ausente"
    ds = yaml.safe_load(ds_file.read_text(encoding="utf-8"))
    queries = ds.get("queries") or []
    # Fast mode
    max_q = None
    if os.getenv("RAG_FAST", "").strip().lower() in ("1", "true", "yes", "on"):
        max_q = 10
    elif os.getenv("RAG_MAX_Q", "").strip().isdigit():
        try:
            max_q = int(os.getenv("RAG_MAX_Q"))
        except Exception:
            max_q = None
    if max_q:
        queries = queries[:max_q]

    combos = [
        ("hybrid_rrf", chosen_chunking),
        ("hybrid_union", chosen_chunking),
    ]

    results = []
    for search_type, chunking in combos:
        hits = 0
        llm_yes = 0
        total = 0
        for q in queries:
            group = (q.get("group") or q.get("kind") or "empresa").strip().lower()
            pergunta = q.get("pergunta") or q.get("question")
            expected = q.get("answer") or q.get("expected_all") or q.get("expected")
            if not (pergunta and expected):
                continue
            total += 1

            args = {
                "query": pergunta,
                "k": 5,
                "search_type": search_type,
                "reranker": "none",
                "empresa": empresa,
                "chunking": chunking,
            }
            res = kb_search_client.invoke(args)
            blob = "\n".join([it.get("content") or "" for it in res])
            def _norm(s: str) -> str:
                import unicodedata
                s = unicodedata.normalize("NFKD", s)
                s = "".join(ch for ch in s if not unicodedata.combining(ch))
                return s.lower()
            if isinstance(expected, list):
                ok5 = all(_norm(x) in _norm(blob) for x in expected)
                ctxs = [it.get("content") or "" for it in res]
                try:
                    ok = llm_judge_yesno(pergunta, ", ".join(expected), ctxs)
                except Exception:
                    ok = False
            else:
                ok5 = any(_norm(expected) in _norm(it.get("content") or "") for it in res)
                ctxs = [it.get("content") or "" for it in res]
                try:
                    ok = llm_judge_yesno(pergunta, expected, ctxs)
                except Exception:
                    ok = False
            hits += 1 if ok5 else 0
            llm_yes += 1 if ok else 0

        results.append((search_type, chunking, round(hits / max(total, 1), 2), round(llm_yes / max(total, 1), 2)))

    print("\n=== COMPARAÇÃO (hybrid_rrf vs hybrid_union) — chunking fixo ===")
    print("search       | chunking  | hit@5 | llm_yes")
    print("-" * 48)
    for search_type, chunking, hitk, lyes in results:
        print(f"{search_type:11s}| {chunking:9s}| {hitk:5.2f} | {lyes:7.2f}")

    # Pelo menos uma combinação deve atingir >= 0.5
    assert any(hitk >= 0.5 for _, _, hitk, _ in results)
