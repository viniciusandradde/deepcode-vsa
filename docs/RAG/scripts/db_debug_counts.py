#!/usr/bin/env python3
"""
Imprime contagens e amostras do KB (staging e chunks) para depuração rápida.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/db_debug_counts.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg


def db_url_from_env() -> str:
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    if not all([user, pwd, host, name]):
        raise SystemExit("Faltam variáveis do DB: DB_USER, DB_PASSWORD, DB_HOST, DB_NAME (opcionais: DB_PORT, DB_SSLMODE).")
    sslmode = os.getenv("DB_SSLMODE", "require")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{name}?sslmode={sslmode}"


def main() -> int:
    # Carrega .env do repositório
    load_dotenv()
    repo_root = Path(__file__).resolve().parents[1]
    env_alt = repo_root / ".env"
    if env_alt.exists():
        load_dotenv(env_alt, override=False)
    url = db_url_from_env()
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            print("KB_DOCS (staging)")
            cur.execute("select count(*) from public.kb_docs")
            print("  total:", cur.fetchone()[0])
            cur.execute("select coalesce(empresa,'<null>') as empresa, count(*) from public.kb_docs group by 1 order by 2 desc")
            for emp, c in cur.fetchall() or []:
                print(f"  empresa={emp} -> {c}")
            print()

            print("KB_CHUNKS (materializados)")
            cur.execute("select count(*) from public.kb_chunks")
            print("  total:", cur.fetchone()[0])
            cur.execute(
                "select coalesce(empresa,'<null>') as empresa, meta->>'chunking' as chunking, count(*)\n"
                "from public.kb_chunks group by 1,2 order by 1,2"
            )
            rows = cur.fetchall() or []
            for emp, strat, c in rows:
                print(f"  empresa={emp} chunking={strat} -> {c}")

            print()
            print("AMOSTRA POR ESTRATÉGIA (primeiros 5 doc_path por empresa/chunking)")
            cur.execute(
                "select coalesce(empresa,'<null>') as empresa, meta->>'chunking' as chunking, doc_path, count(*) as n\n"
                "from public.kb_chunks group by 1,2,3 order by 1,2,3 limit 15"
            )
            for emp, strat, doc, n in cur.fetchall() or []:
                print(f"  {emp} | {strat} | {doc} -> {n} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
