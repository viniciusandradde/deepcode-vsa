#!/usr/bin/env python3
"""
Runner de migrações SQL simples para o Módulo 1.

Lê arquivos .sql de um diretório (por padrão, ai-agent-sales/sql), em ordem lexicográfica,
e aplica no Postgres usando psycopg. Usa variáveis de ambiente do .env:
  DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

Exemplos:
  python scripts/migrate.py --dir sql --list
  python scripts/migrate.py --dir sql                   # aplica todos
  python scripts/migrate.py --dir sql --files 01_crm_schema.sql 02_seed_status_lead.sql

Requisitos: psycopg, python-dotenv. Já constam em requirements.txt deste módulo.
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg


def db_url_from_env() -> str:
    # Monta a partir de DB_* (didático). Não usa DB_URL.
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    if not all([user, pwd, host, name]):
        raise SystemExit("Faltam variáveis do DB: DB_USER, DB_PASSWORD, DB_HOST, DB_NAME (opcionais: DB_PORT, DB_SSLMODE).")
    sslmode = os.getenv("DB_SSLMODE", "require")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{name}?sslmode={sslmode}"


def discover_sql_files(sql_dir: Path, selection: list[str] | None) -> list[Path]:
    if selection:
        files = [sql_dir / f for f in selection]
    else:
        files = sorted(sql_dir.glob("*.sql"))
    return [f for f in files if f.exists()]


def apply_sql_files(conn_str: str, files: list[Path], continue_on_error: bool = False) -> int:
    # Modo silencioso para testes (controlado por env)
    quiet = os.getenv("MIGRATE_QUIET", "").strip().lower() in ("1", "true", "yes", "on")
    if not files:
        if not quiet:
            print("Nenhum arquivo .sql encontrado.")
        return 0
    applied = 0
    with psycopg.connect(conn_str) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                if not quiet:
                    print(f"\n=== Aplicando: {path.name} ===")
                try:
                    cur.execute(sql)
                    applied += 1
                    if not quiet:
                        print(f"OK: {path.name}")
                except Exception as e:
                    if not quiet:
                        print(f"ERRO em {path.name}: {e}")
                    if not continue_on_error:
                        break
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aplicador de migrações SQL (Postgres)")
    parser.add_argument("--dir", default="sql", help="Diretório com .sql (default: sql)")
    parser.add_argument("--files", nargs="*", help="Arquivos específicos a aplicar, em ordem.")
    parser.add_argument("--list", action="store_true", help="Apenas listar os arquivos detectados.")
    parser.add_argument("--continue-on-error", action="store_true", help="Não interromper no primeiro erro.")

    args = parser.parse_args(argv)

    # Carrega .env local (rodar a partir de ai-agent-sales)
    # Se executado de outra pasta, tente carregar .env relativo a este arquivo
    load_dotenv()  # cwd
    repo_root = Path(__file__).resolve().parents[1]
    env_alt = repo_root / ".env"
    if env_alt.exists():
        load_dotenv(env_alt, override=False)

    sql_dir = Path(args.dir)
    if not sql_dir.is_absolute():
        # relative to repo module dir
        sql_dir = (Path(__file__).resolve().parents[1] / sql_dir).resolve()

    files = discover_sql_files(sql_dir, args.files)
    if args.list:
        print("Arquivos .sql (ordem de execução):")
        for f in files:
            print(f"- {f.name}")
        return 0

    try:
        conn_str = db_url_from_env()
    except SystemExit as e:
        print(str(e))
        return 2

    count = apply_sql_files(conn_str, files, continue_on_error=args.continue_on_error)
    print(f"\nConcluído. Arquivos aplicados: {count}/{len(files)}")
    return 0 if count == len(files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
