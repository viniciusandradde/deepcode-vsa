import yaml
from pathlib import Path
import psycopg
import pytest

# Fase 2: runner de combinações (SEMANTIC chunking) com juiz LLM
pytestmark = pytest.mark.phase2


def _has_semantic_chunks(conn_str: str, empresa: str = "Empresa X") -> bool:
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select count(*) from public.kb_chunks where lower(empresa)=lower(%s) and meta->>'chunking'='semantic'",
                (empresa,),
            )
            c = cur.fetchone()[0]
    return c > 0


def test_experiments_runner(capsys, db_ready, require_openai, llm_judge_yesno):
    """Compara combinações (search_type × HyDE × threshold × reranker) usando SEMANTIC como chunking.

    Pré‑requisito: KB materializado (Fase 0) com chunks semantic.
    """
    from app.rag.tools import kb_search_client

    empresa = "Empresa X"

    cfg = yaml.safe_load((Path(__file__).resolve().parents[0] / "experiments.yaml").read_text(encoding="utf-8"))
    experiments = cfg.get("experiments") or []
    assert experiments, "Arquivo experiments.yaml vazio"

    qpath = Path(__file__).resolve().parents[0]
    ds_file = qpath / "rag_queries.yaml"
    assert ds_file.exists(), "Arquivo 'tests/rag/rag_queries.yaml' ausente"
    ds = yaml.safe_load(ds_file.read_text(encoding="utf-8"))
    queries = ds.get("queries") or []

    # Limite rápido por env: RAG_FAST=1 (usa 10) ou RAG_MAX_Q
    import os
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

    results = []
    for exp in experiments:
        name = exp.get("name")
        search_type = exp.get("search_type")
        use_hyde = bool(exp.get("use_hyde"))
        match_threshold = exp.get("match_threshold")
        reranker = exp.get("reranker", "none")
        chunking = exp.get("chunking")
        assert chunking in ("fixed", "markdown", "semantic"), "Experimento sem 'chunking' válido"
        hits5 = 0
        hits1 = 0
        lyes = 0
        total = 0
        skipped_due_to_rerank = False
        for q in queries:
            pergunta = q.get("pergunta") or q.get("question")
            # Heurística (hit@5/hit@1): usa expected/expected_all
            exp_all = q.get("expected_all")
            exp_one = q.get("expected")
            # Judge: prioriza answer
            judge_expected = q.get("answer") or exp_one or (", ".join(exp_all) if exp_all else None)
            if not (pergunta and (exp_one or exp_all)):
                continue
            total += 1

            args = {
                "query": pergunta,
                "k": 5,
                "search_type": search_type,
                "reranker": reranker,
                "empresa": empresa,
                "chunking": chunking,
                "use_hyde": use_hyde,
            }
            if match_threshold is not None:
                args["match_threshold"] = float(match_threshold)

            # Tratamento específico para rate limit do reranker (evita falhar a suíte inteira)
            try:
                res = kb_search_client.invoke(args)
            except Exception as e:
                # Pula o experimento inteiro em caso de rate limit do reranker
                try:
                    from cohere.errors import TooManyRequestsError
                    if isinstance(e, TooManyRequestsError) or "TooManyRequests" in str(e):
                        print(f"[SKIP] {name}: reranker rate-limited (429). Pulando este experimento.")
                        skipped_due_to_rerank = True
                        break
                except Exception:
                    pass
                raise
            blob = "\n".join([it.get("content") or "" for it in res])
            def _norm(s: str) -> str:
                import unicodedata
                s = unicodedata.normalize("NFKD", s)
                s = "".join(ch for ch in s if not unicodedata.combining(ch))
                return s.lower()
            # Heurística hit@5/hit@1
            if exp_all:
                ok5 = all(_norm(x) in _norm(blob) for x in exp_all)
                top = (res[0].get("content") or "") if res else ""
                ok1 = all(_norm(x) in _norm(top) for x in exp_all)
            else:
                ok5 = any(_norm(exp_one) in _norm(it.get("content") or "") for it in res)
                top = (res[0].get("content") or "") if res else ""
                ok1 = _norm(exp_one) in _norm(top)
            hits5 += 1 if ok5 else 0
            hits1 += 1 if ok1 else 0
            # LLM judge
            ctxs = [it.get("content") or "" for it in res]
            try:
                ok = llm_judge_yesno(pergunta, judge_expected or "", ctxs)
            except Exception:
                ok = False
            lyes += 1 if ok else 0

        if skipped_due_to_rerank:
            continue
        results.append({
            "name": name,
            "chunking": chunking,
            "search_type": search_type,
            "use_hyde": use_hyde,
            "match_threshold": match_threshold,
            "reranker": reranker,
            "hit@5": round(hits5 / max(total, 1), 2),
            "hit@1": round(hits1 / max(total, 1), 2),
            "llm_yes": round(lyes / max(total, 1), 2),
        })

    print("\n=== EXPERIMENTS COMPARISON (ordenado por llm_yes) ===")
    print("name                 | chunking  | search       | hyde | thr  | rerank   | hit@5 | llm_yes")
    print("-" * 106)
    for r in sorted(results, key=lambda x: x["llm_yes"], reverse=True):
        thr = r.get('match_threshold')
        thr_s = f"{thr:.2f}" if isinstance(thr, (int, float)) else "-"
        print(f"{r['name'][:20]:20s} | {r['chunking']:9s} | {r['search_type']:11s} | {str(r['use_hyde'])[:4]:4s} | {thr_s:>4s} | {r.get('reranker','none')[:8]:8s} | {r['hit@5']:.2f} | {r['llm_yes']:.2f}")

    # Assert suave: ao menos um experimento processado
    assert results, "Nenhum experimento processado (todos podem ter sido pulados por rate limit)"
