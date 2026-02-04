#!/usr/bin/env python3
"""
Trunca as tabelas do Mini‑CRM (ambiente de desenvolvimento).

Uso:
  python scripts/db_truncate.py           # modo seguro: NÃO executa (pede --yes)
  python scripts/db_truncate.py --yes     # executa TRUNCATE nas tabelas (cascade)

Requisitos:
  - Variáveis DB_* no .env (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
  - Psycopg, python-dotenv
"""

import argparse
import os
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


def truncate_all(conn_str: str) -> None:
    stmts = [
        "truncate table public.itens_proposta cascade;",
        "truncate table public.propostas cascade;",
        "truncate table public.tarefas_lead cascade;",
        "truncate table public.notas_lead cascade;",
        "truncate table public.leads cascade;",
    ]
    with psycopg.connect(conn_str) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for sql in stmts:
                cur.execute(sql)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TRUNCATE das tabelas do Mini‑CRM (desenvolvimento)")
    parser.add_argument("--yes", action="store_true", help="Confirma execução do TRUNCATE (modo destrutivo)")
    args = parser.parse_args(argv)

    # Carrega .env (cwd) e, se existir, o .env do módulo
    load_dotenv()
    try:
        conn_str = db_url_from_env()
    except SystemExit as e:
        print(str(e))
        return 2

    if not args.yes:
        print("ATENÇÃO: este comando vai TRUNCAR (apagar) os dados das tabelas do Mini‑CRM.")
        print("Para confirmar, rode: python scripts/db_truncate.py --yes")
        return 2

    truncate_all(conn_str)
    print("Tabelas truncadas com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

