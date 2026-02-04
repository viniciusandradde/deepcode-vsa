#!/usr/bin/env python3
"""
Phase 2 — Runner de experimentos (comparação de combinações)

Lê experiments em tests/rag/experiments.yaml e perguntas em tests/rag/rag_queries.yaml.
Executa cada configuração (chunking/search_type/HyDE/threshold/reranker) sobre o KB materializado (Phase 0)
e salva JSON/CSV em tests/rag/analysis/.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/rag_phase2_runner.py [--fast] [--max N] [--outfile NAME]

Exemplos:
  PYTHONPATH=. .venv/bin/python scripts/rag_phase2_runner.py --fast
  PYTHONPATH=. .venv/bin/python scripts/rag_phase2_runner.py --max 50 --outfile phase2_full

Saídas:
  tests/rag/analysis/<NAME>_results.json   (summary + details)
  tests/rag/analysis/<NAME>_results.csv    (summary + details em um único CSV)

Obs.: Se o reranker Cohere atingir 429 (Trial key), o experimento específico é pulado e registrado como skipped.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

import yaml


def llm_judge_yesno_with_reason(question: str, expected: str, contexts: list[str]) -> tuple[bool, str]:
    """LLM como juiz binário (sim/não) com justificativa curta.

    Retorna (ok, justificativa). Usa o modelo definido em EVAL_LLM_MODEL (default gpt-4.1-2025-04-14).

    Observação: os itens de `contexts` podem vir rotulados (ex.: "CTX1 [path#ix]: snippet");
    quando possível, a justificativa deve citar esses rótulos (CTX1/CTX2/...).
    """
    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        return False, ""
    prompt = (
        "Você é um avaliador. Analise os CONTEXTOS recuperados e responda 'sim' ou 'não' seguido de uma justificativa curta.\n"
        "A saída deve estar em UMA ÚNICA LINHA no formato: <sim|não> — <justificativa curta>.\n"
        "Na justificativa, cite sucintamente os termos/trechos que sustentam a decisão e, se útil, referencie os contextos pelos IDs (ex.: CTX1/CTX2).\n\n"
        f"QUESTÃO: {question}\n"
        f"ESPERADO: {expected}\n\n"
        f"CONTEXTOS:\n- " + "\n- ".join(contexts[:5]) + "\n\n"
        "Saída: uma única linha no formato: sim — <justificativa> ou não — <justificativa>."
    )
    try:
        llm = ChatOpenAI(model=os.getenv("EVAL_LLM_MODEL", "gpt-4.1-2025-04-14"), temperature=0)
        raw = (llm.invoke(prompt).content or "").strip()
        low = raw.lower()
        ok = low.startswith("sim")
        # Extrai justificativa após travessão/colchetes/dois-pontos; fallback: tudo após a primeira palavra
        just = raw
        for sep in ["—", "-", ":", "|", "–"]:
            if sep in raw:
                parts = raw.split(sep, 1)
                just = parts[1].strip() if len(parts) > 1 else raw
                break
        else:
            toks = raw.split(None, 1)
            just = toks[1].strip() if len(toks) > 1 else ""
        return ok, just
    except Exception:
        return False, ""


def _norm(s: str) -> str:
    import unicodedata
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()


def load_experiments_and_queries() -> tuple[list[dict[str, Any]], list[dict[str, Any]], Path]:
    base = Path(__file__).resolve().parents[1] / "tests" / "rag"
    exp_file = base / "experiments.yaml"
    q_file = base / "rag_queries.yaml"
    assert exp_file.exists(), f"Arquivo de experimentos ausente: {exp_file}"
    assert q_file.exists(), f"Arquivo de perguntas ausente: {q_file}"
    exp = yaml.safe_load(exp_file.read_text(encoding="utf-8")) or {}
    exps = exp.get("experiments") or []
    qs = (yaml.safe_load(q_file.read_text(encoding="utf-8")) or {}).get("queries") or []
    return exps, qs, base


def run(args: argparse.Namespace) -> int:
    from app.rag.tools import kb_search_client

    experiments, queries, base = load_experiments_and_queries()
    if args.fast:
        queries = queries[:10]
    if args.max and args.max > 0:
        queries = queries[: args.max]

    out_dir = base / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    outname = args.outfile or "phase2"

    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []

    for exp in experiments:
        name = exp.get("name") or "unnamed"
        chunking = exp.get("chunking")
        search_type = exp.get("search_type")
        use_hyde = bool(exp.get("use_hyde"))
        match_threshold = exp.get("match_threshold")
        reranker = exp.get("reranker", "none")
        assert chunking in ("fixed", "markdown", "semantic"), f"chunking inválido: {chunking}"
        hit5 = 0
        hit1 = 0
        lyes = 0
        total = 0
        skipped_reason = None

        for q in queries:
            pergunta = q.get("pergunta") or q.get("question")
            exp_all = q.get("expected_all")
            exp_one = q.get("expected")
            judge_expected = q.get("answer") or exp_one or (", ".join(exp_all) if exp_all else None)
            if not (pergunta and (exp_one or exp_all)):
                continue
            total += 1
            req = {
                "query": pergunta,
                "k": 5,
                "search_type": search_type,
                "reranker": reranker,
                "empresa": "Empresa X",
                "chunking": chunking,
                "use_hyde": use_hyde,
            }
            if match_threshold is not None:
                try:
                    req["match_threshold"] = float(match_threshold)
                except Exception:
                    pass
            try:
                res = kb_search_client.invoke(req)
            except Exception as e:
                # Reranker 429
                if "TooManyRequests" in str(e):
                    skipped_reason = "cohere_429"
                    break
                raise

            blob = "\n".join([it.get("content") or "" for it in res])
            if exp_all:
                ok5 = all(_norm(x) in _norm(blob) for x in exp_all)
                top = (res[0].get("content") or "") if res else ""
                ok1 = all(_norm(x) in _norm(top) for x in exp_all)
            else:
                ok5 = any(_norm(exp_one) in _norm(it.get("content") or "") for it in res)
                top = (res[0].get("content") or "") if res else ""
                ok1 = _norm(exp_one) in _norm(top)
            hit5 += 1 if ok5 else 0
            hit1 += 1 if ok1 else 0

            # Juiz LLM (sem fixtures de pytest)
            judge_ok = False
            judge_reason = ""
            # Prepara contextos rotulados e estruturados para auditoria
            def _snip(s: str, n: int = 300) -> str:
                s = (s or "").replace("\n", " ").strip()
                return s if len(s) <= n else s[:n] + "…"
            judge_ctx_struct: list[dict[str, Any]] = []
            judge_ctx_labeled: list[str] = []
            for i, it in enumerate(res[:5], start=1):
                doc = it.get("doc_path") or "-"
                ix = it.get("chunk_ix")
                sc = it.get("score")
                sn = _snip(it.get("content") or "")
                cid = f"CTX{i}"
                judge_ctx_struct.append({
                    "id": cid,
                    "doc_path": doc,
                    "chunk_ix": ix,
                    "score": sc,
                    "snippet": sn,
                })
                from pathlib import Path as _P
                base = _P(doc).name if doc else "-"
                scs = f"{sc:.2f}" if isinstance(sc, (int, float)) and sc is not None else "-"
                judge_ctx_labeled.append(f"{cid} [{base}#{ix} score={scs}]: {sn}")
            try:
                judge_ok, judge_reason = llm_judge_yesno_with_reason(
                    pergunta,
                    judge_expected or "",
                    judge_ctx_labeled,
                )
            except Exception:
                judge_ok, judge_reason = False, ""
            lyes += 1 if judge_ok else 0

            details.append({
                "experiment": name,
                "chunking": chunking,
                "search_type": search_type,
                "use_hyde": use_hyde,
                "match_threshold": match_threshold,
                "reranker": reranker,
                "question": pergunta,
                "expected": exp_one or exp_all,
                "answer": judge_expected,
                "hit@5": bool(ok5),
                "hit@1": bool(ok1),
                "judge_yes": bool(judge_ok),
                "judge_justification": judge_reason,
                # Auditoria do que o juiz viu
                "judge_contexts": judge_ctx_struct,
                # Atalhos do top‑1
                "top1_path": (res[0].get("doc_path") if res else None),
                "top1_chunk_ix": (res[0].get("chunk_ix") if res else None),
                "top1_score": (res[0].get("score") if res else None),
                "top1_snippet": (_snip(res[0].get("content") or "") if res else None),
            })

        if skipped_reason:
            rows.append({
                "name": name,
                "chunking": chunking,
                "search_type": search_type,
                "use_hyde": use_hyde,
                "match_threshold": match_threshold,
                "reranker": reranker,
                "skipped": skipped_reason,
                "hit@5": None,
                "hit@1": None,
                "llm_yes": None,
            })
        else:
            rows.append({
                "name": name,
                "chunking": chunking,
                "search_type": search_type,
                "use_hyde": use_hyde,
                "match_threshold": match_threshold,
                "reranker": reranker,
                "hit@5": round(hit5 / max(total, 1), 2),
                "hit@1": round(hit1 / max(total, 1), 2),
                "llm_yes": round(lyes / max(total, 1), 2),
            })

    # Salva CSV/JSON
    # CSV único (summary + details)
    csv_path = out_dir / f"{outname}_results.csv"
    # Campos: união de summary e details + marcador de tipo de linha
    summary_fields = [
        "name", "chunking", "search_type", "use_hyde", "match_threshold", "reranker", "hit@5", "hit@1", "llm_yes", "skipped"
    ]
    detail_fields = [
        "experiment", "chunking", "search_type", "use_hyde", "match_threshold", "reranker",
        "question", "expected", "answer",
        "hit@5", "hit@1", "judge_yes", "judge_justification",
        # Campos de auditoria leves
        "top1_path", "top1_chunk_ix", "top1_score",
        # Até 3 contextos formatados para leitura rápida
        "ctx1", "ctx2", "ctx3",
    ]
    # Garante ordem estável e inclusão de 'row_type'
    union_fields: list[str] = ["row_type"]
    for f in summary_fields + detail_fields:
        if f not in union_fields:
            union_fields.append(f)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=union_fields)
        w.writeheader()
        # Summary primeiro (ordenado por llm_yes)
        for r in sorted(rows, key=lambda x: (x.get("llm_yes") is None, -(x.get("llm_yes") or 0))):
            rr = {k: r.get(k) for k in summary_fields}
            rr["row_type"] = "summary"
            w.writerow(rr)
        # Depois detalhes por pergunta
        for d in details:
            dd = {k: d.get(k) for k in detail_fields}
            # Preenche ctx1..ctx3 a partir de judge_contexts
            ctxs = d.get("judge_contexts") or []
            def _fmt_ctx(obj: dict) -> str:
                if not isinstance(obj, dict):
                    return ""
                base = (obj.get("doc_path") or "-").split("/")[-1]
                ix = obj.get("chunk_ix")
                sc = obj.get("score")
                scs = f"{sc:.2f}" if isinstance(sc, (int, float)) and sc is not None else "-"
                sn = obj.get("snippet") or ""
                return f"{base}#{ix} ({scs}): {sn}"
            dd["ctx1"] = _fmt_ctx(ctxs[0]) if len(ctxs) > 0 else None
            dd["ctx2"] = _fmt_ctx(ctxs[1]) if len(ctxs) > 1 else None
            dd["ctx3"] = _fmt_ctx(ctxs[2]) if len(ctxs) > 2 else None
            # Repete o nome do experimento na coluna 'name' para facilitar filtros
            dd_name = d.get("experiment")
            dd_row = {k: None for k in union_fields}
            dd_row.update(dd)
            dd_row["name"] = dd_name
            dd_row["row_type"] = "detail"
            w.writerow(dd_row)

    json_path = out_dir / f"{outname}_results.json"
    json_path.write_text(json.dumps({"summary": rows, "details": details}, ensure_ascii=False, indent=2), encoding="utf-8")


    print("\n=== EXPERIMENTS RESULTS (ordenado por llm_yes) ===")
    print("name                 | chunking  | search       | hyde | thr  | rerank   | hit@5 | hit@1 | llm_yes")
    print("-" * 118)
    for r in sorted(rows, key=lambda x: (x.get("llm_yes") is None, -(x.get("llm_yes") or 0))):
        thr = r.get('match_threshold')
        thr_s = f"{thr:.2f}" if isinstance(thr, (int, float)) else "-"
        print(f"{str(r['name'])[:20]:20s} | {str(r['chunking']):9s} | {str(r['search_type']):11s} | {str(r['use_hyde'])[:4]:4s} | {thr_s:>4s} | {str(r.get('reranker','none'))[:8]:8s} | {str(r['hit@5']):>5s} | {str(r['hit@1']):>5s} | {str(r['llm_yes']):>6s}")

    print(f"\nCSV: {csv_path}")
    print(f"JSON: {json_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phase 2 runner (experiments)")
    p.add_argument("--fast", action="store_true", help="Usa apenas ~10 perguntas (atalho; equivalente a RAG_FAST=1)")
    p.add_argument("--max", type=int, default=0, help="Limita a N perguntas (0 = todas)")
    p.add_argument("--outfile", default="phase2", help="Prefixo do arquivo de saída (default: phase2)")
    args = p.parse_args(argv)
    if args.fast:
        os.environ["RAG_FAST"] = "1"
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
