#!/usr/bin/env python3
"""
Phase 3 — Runner do agente (E2E com LLM-judge)

Executa o grafo proposal_agent_v2 sobre o dataset tests/rag/rag_queries.yaml
e salva JSON/CSV em tests/rag/analysis/.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/rag_phase3_runner.py [--fast] [--max N] [--outfile NAME]

Exemplos:
  PYTHONPATH=. .venv/bin/python scripts/rag_phase3_runner.py --fast
  PYTHONPATH=. .venv/bin/python scripts/rag_phase3_runner.py --max 50 --outfile phase3_full

Saídas:
  tests/rag/analysis/<NAME>_results.json   (summary + details)
  tests/rag/analysis/<NAME>_results.csv    (summary + details em um único CSV)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

import yaml


def llm_judge_yesno_with_reason(question: str, expected: str, answer_text: str) -> tuple[bool, str]:
    """LLM como juiz binário (sim/não) com justificativa curta sobre a RESPOSTA fornecida."""
    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        return False, ""
    prompt = (
        "Você é um avaliador. Analise a RESPOSTA a seguir e responda 'sim' ou 'não' seguido de uma justificativa curta.\n"
        "A resposta deve estar em UMA LINHA no formato: <sim|não> — <justificativa curta>.\n"
        "A justificativa deve citar sucintamente os termos/trechos que sustentam a decisão e se a QUESTÃO foi respondida.\n\n"
        f"QUESTÃO: {question}\n"
        f"ESPERADO: {expected}\n\n"
        f"RESPOSTA:\n{answer_text}\n\n"
        "Saída: uma única linha no formato: sim — <justificativa> ou não — <justificativa>."
    )
    try:
        llm = ChatOpenAI(model=os.getenv("EVAL_LLM_MODEL", "gpt-4.1-2025-04-14"), temperature=0)
        raw = (llm.invoke(prompt).content or "").strip()
        low = raw.lower()
        ok = low.startswith("sim")
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


def extract_answer_text(last_content: Any) -> str:
    if isinstance(last_content, list):
        parts: list[str] = []
        for it in last_content:
            if isinstance(it, dict) and it.get("type") in ("text", "output_text"):
                t = it.get("text") or ""
                if t:
                    parts.append(t)
        return "\n".join(parts)
    return last_content if isinstance(last_content, str) else str(last_content or "")


def load_queries() -> list[dict[str, Any]]:
    base = Path(__file__).resolve().parents[1] / "tests" / "rag"
    q_file = base / "rag_queries.yaml"
    assert q_file.exists(), f"Arquivo de perguntas ausente: {q_file}"
    data = yaml.safe_load(q_file.read_text(encoding="utf-8")) or {}
    return data.get("queries") or []


def run(args: argparse.Namespace) -> int:
    from langchain_core.messages import HumanMessage
    from app.rag.proposal_agent_v2 import graph

    queries = load_queries()
    if args.fast:
        queries = queries[:10]
    if args.max and args.max > 0:
        queries = queries[: args.max]

    # Chunking informativo (o agente usa default interno 'semantic')
    chunking = os.getenv("PROPOSAL_CHUNKING", "semantic")

    base = Path(__file__).resolve().parents[1] / "tests" / "rag"
    out_dir = base / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    outname = args.outfile or "phase3"

    total = 0
    lyes = 0
    details: list[dict[str, Any]] = []
    for q in queries:
        pergunta = q.get("pergunta") or q.get("question")
        exp = q.get("answer") or q.get("expected") or ", ".join(q.get("expected_all") or [])
        if not (pergunta and exp):
            continue
        total += 1

        state = graph.invoke({"messages": [HumanMessage(content=pergunta)]})
        messages = state.get("messages") or []
        raw = messages[-1].content if messages and hasattr(messages[-1], "content") else ""
        answer = extract_answer_text(raw)

        ok = False
        reason = ""
        try:
            ok, reason = llm_judge_yesno_with_reason(pergunta, exp, answer)
        except Exception:
            ok, reason = False, ""
        lyes += 1 if ok else 0

        details.append({
            "question": pergunta,
            "expected": exp,
            "answer": answer[:4000],
            "judge_yes": bool(ok),
            "judge_justification": reason,
        })

    rate = round(lyes / max(total, 1), 2)
    row = {
        "chunking": chunking,
        "total": total,
        "llm_yes": rate,
    }

    # Escreve CSV/JSON
    # CSV único (summary + details)
    csv_path = out_dir / f"{outname}_results.csv"
    summary_fields = ["chunking", "total", "llm_yes"]
    detail_fields = ["question", "expected", "answer", "judge_yes", "judge_justification"]
    union_fields: list[str] = ["row_type"]
    for f in summary_fields + detail_fields:
        if f not in union_fields:
            union_fields.append(f)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=union_fields)
        w.writeheader()
        # Summary row
        rsum = {k: row.get(k) for k in summary_fields}
        rsum["row_type"] = "summary"
        w.writerow(rsum)
        # Details rows
        for d in details:
            dd = {k: d.get(k) for k in detail_fields}
            dd_row = {k: None for k in union_fields}
            dd_row.update(dd)
            dd_row["row_type"] = "detail"
            w.writerow(dd_row)

    json_path = out_dir / f"{outname}_results.json"
    json_path.write_text(json.dumps({"summary": [row], "details": details}, ensure_ascii=False, indent=2), encoding="utf-8")


    print("\n=== PHASE 3 — AGENT (LLM-JUDGE SOBRE DATASET) ===")
    print(f"chunking={chunking} | total={total} | llm_yes={rate:0.2f}")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phase 3 runner (agent E2E)")
    p.add_argument("--fast", action="store_true", help="Usa apenas ~10 perguntas (atalho; equivalente a RAG_FAST=1)")
    p.add_argument("--max", type=int, default=0, help="Limita a N perguntas (0 = todas)")
    p.add_argument("--outfile", default="phase3", help="Prefixo do arquivo de saída (default: phase3)")
    args = p.parse_args(argv)
    if args.fast:
        os.environ["RAG_FAST"] = "1"
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
