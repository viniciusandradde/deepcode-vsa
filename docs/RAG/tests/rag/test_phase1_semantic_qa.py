import uuid
from pathlib import Path
import pytest

# Fase 1 — avaliação simples usando apenas busca semântica (vetorial)
pytestmark = pytest.mark.phase1


def test_phase1_semantic_only_vector(tmp_path: Path, db_ready, require_openai):
    """Avalia recuperação vetorial (VECTOR only) sobre o dataset didático.

    Regras deste teste:
    - Ingesta todo o dataset de `tests/rag/data` usando chunking markdown (idempotente).
    - Consulta apenas com `search_type=vector` (sem híbridos, sem rerank).
    - Para cada documento de leads, definir 3 perguntas/termos esperados.
    - Para os demais documentos (products/services/policies), 1 pergunta/termo esperado por doc.
    - Métrica: hit@5 (se o termo esperado aparece em qualquer um dos top‑5 conteúdos).
    """
    from app.rag.tools import kb_search_client
    import psycopg

    # Requer KB pré‑carregado (use `make rag_phase0`). Valida presença de Empresas X e Y.
    empresa_x = "Empresa X"
    empresa_y = "Empresa Y"
    try:
        with psycopg.connect(db_ready) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select count(*) from public.kb_chunks where lower(empresa)=lower(%s)",
                    (empresa_x,),
                )
                cx = cur.fetchone()[0]
                cur.execute(
                    "select count(*) from public.kb_chunks where lower(empresa)=lower(%s)",
                    (empresa_y,),
                )
                cy = cur.fetchone()[0]
        if cx == 0 or cy == 0:
            pytest.skip("KB vazio para Empresa X/Y. Execute `make rag_phase0` antes da fase 1.")
    except Exception:
        pytest.skip("Não foi possível validar KB; verifique conexão/ingestão prévia.")

    # Conjunto de perguntas (empresa, pergunta, termo_esperado)
    # Carrega dataset externo (YAML). Sem fallback.
    import yaml
    ds_path = Path(__file__).resolve().parents[0] / "rag_queries.yaml"
    assert ds_path.exists(), "Arquivo de queries 'tests/rag/rag_queries.yaml' ausente"
    cases = []
    data = yaml.safe_load(ds_path.read_text(encoding="utf-8")) or {}
    for q in data.get("queries", []):
        grp = (q.get("group") or q.get("kind") or "empresa").strip().lower()
        emp = q.get("empresa") or empresa_x
        per = q.get("pergunta") or q.get("question")
        exp = q.get("expected_all") or q.get("expected")
        if per and exp:
            cases.append((grp, emp, per, exp))

    import unicodedata

    def _normalize(s: str) -> str:
        s = s or ""
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower()
        s = s.replace("‑", "").replace("-", "")  # hifens comuns e não‑quebrantes
        return s

    strategies = ["fixed", "markdown", "semantic"]

    # 1) Resumo por estratégia
    summary = []  # (strategy, hit@5, hit@1)
    per_question = []  # [(empresa, pergunta, esperado, {strategy: (ok1, doc:chunk)})]

    for kind, empresa, pergunta, esperado in cases:
        row = {"empresa": empresa, "kind": kind, "q": pergunta, "exp": esperado, "by": {}, "doc": {}}
        for strat in strategies:
            res = kb_search_client.invoke({
                "query": pergunta,
                "k": 5,
                "search_type": "vector",
                "reranker": "none",
                "empresa": empresa,
                "chunking": strat,
            })
            # Normalização de esperado (suporta string ou lista)
            if isinstance(esperado, (list, tuple)):
                exp_list = [_normalize(x) for x in esperado]
                def _has_all(s: str) -> bool:
                    ns = _normalize(s)
                    return all(x in ns for x in exp_list)
                def _has_any(s: str) -> bool:
                    ns = _normalize(s)
                    return any(x in ns for x in exp_list)
                blob5 = "\n".join([it.get("content") or "" for it in res])
                got5 = _has_all(blob5)
                top = res[0] if res else {"doc_path": "-", "chunk_ix": -1, "content": ""}
                got1 = _has_all(top.get("content", ""))
            else:
                exp_norm = _normalize(esperado)
                got5 = any(exp_norm in _normalize(it["content"] or "") for it in res)
                top = res[0] if res else {"doc_path": "-", "chunk_ix": -1, "content": ""}
                got1 = exp_norm in _normalize(top.get("content", ""))

            # Para casos de lead, preferimos top‑1 vindo de lead_reports
            if kind == "lead":
                top_doc = (top.get("doc_path") or "-")
                is_lead_doc = ("/lead_reports/" in top_doc) or (Path(top_doc).name.startswith("lead_"))
                if not is_lead_doc:
                    got1 = False
            # Guarda snippet do chunk top‑1 (não o doc)
            snippet = (top.get("content", "") or "").replace("\n", " ")[:80]
            row["by"][strat] = (got1, snippet, 1 if got5 else 0, 1 if got1 else 0)
            row["doc"][strat] = (Path(top.get("doc_path", "-")).name, top.get("chunk_ix", -1))
        per_question.append(row)

    # Agrega por estratégia
    # Agrupa por kind
    kinds = ["empresa", "lead"]
    grouped = {k: [r for r in per_question if r["kind"] == k] for k in kinds}
    for strat in strategies:
        # Geral
        hit5 = sum(r["by"][strat][2] for r in per_question)
        hit1 = sum(r["by"][strat][3] for r in per_question)
        total = len(per_question)
        summary.append(("geral", strat, hit5 / total if total else 0.0, hit1 / total if total else 0.0))
        # Por grupo
        for k in kinds:
            subset = grouped[k]
            if not subset:
                continue
            h5 = sum(r["by"][strat][2] for r in subset) / len(subset)
            h1 = sum(r["by"][strat][3] for r in subset) / len(subset)
            summary.append((k, strat, h5, h1))

    # 2) Impressões: Sumário e Tabela por pergunta x estratégia (top‑1)
    print("\n=== FASE 1 — SEMANTIC QA (VECTOR ONLY) ===")
    def print_block(title: str, rows):
        print(title)
        print("chunking  | hit@5 | hit@1")
        print("-" * 34)
        for _grp, strat, h5, h1 in rows:
            print(f"{strat:8s}| {h5:5.2f} | {h1:5.2f}")

    print_block("[GERAL]", [r for r in summary if r[0] == "geral"])
    print()
    if any(r[0] == "empresa" for r in summary):
        print_block("[EMPRESA]", [r for r in summary if r[0] == "empresa"])
        print()
    if any(r[0] == "lead" for r in summary):
        print_block("[LEAD]", [r for r in summary if r[0] == "lead"])

    print("\nPergunta x Estratégia (top‑1 — snippet do chunk)")
    print("ix | empresa        | pergunta                               | esperado    | fixed (snippet)                      | markdown (snippet)                   | semantic (snippet)                   ")
    print("-" * 166)
    for i, r in enumerate(per_question, start=1):
        qshort = (r["q"][:35] + "…") if len(r["q"]) > 35 else r["q"]
        # Formata esperado (string ou lista)
        if isinstance(r["exp"], (list, tuple)):
            exp_str = " + ".join([str(x) for x in r["exp"]])
        else:
            exp_str = str(r["exp"])
        exps = (exp_str[:10] + "…") if len(exp_str) > 10 else exp_str
        def cell(s):
            ok1, snip, _a, _b = r["by"][s]
            lab = "OK" if ok1 else " X"
            text = (snip[:32] + "…") if len(snip) > 33 else snip
            return f"{lab} {text:33s}"
        emp_tokens = r["empresa"].split()[:2]
        emp_short = " ".join(emp_tokens)
        print(f"{i:>2d} | {emp_short:14s}| {qshort:35s} | {exps:10s} | {cell('fixed')} | {cell('markdown')} | {cell('semantic')}")

    # 3) Critério: ao menos uma estratégia (no geral) com hit@5 >= 0.65
    assert any(h5 >= 0.65 for grp, strat, h5, h1 in summary if grp == "geral"), (
        "Desempenho insuficiente (nenhuma estratégia atingiu 0.65 em hit@5)"
    )
