#!/usr/bin/env python3
"""
Fase 0 — Utilitário de ingestão do KB (staging → chunks) para o curso.

O que faz:
- (Opcional) Aplica as migrações do KB (staging + schema + índices + funções).
- Limpa as tabelas do KB (TRUNCATE em kb_docs e kb_chunks) para garantir execução limpa.
- Lê arquivos .md de um diretório base e insere 1 linha por arquivo em kb_docs (staging).
- A partir do staging, materializa chunks em kb_chunks para uma ou mais estratégias
  (fixed, markdown, semantic), com prefixo de doc_path por estratégia para evitar colisão.

Como usar (por padrão lê .env do projeto):
  PYTHONPATH=. .venv/bin/python scripts/rag_phase0.py \
    --base kb \
    --empresa "Empresa Curso" \
    --strategies fixed markdown semantic

Também aceita variáveis de ambiente (fallback) se as flags não forem passadas:
  BASE_DIR, EMPRESA, CLIENT_ID, STRATEGIES (separadas por espaço),
  CHUNK_SIZE, CHUNK_OVERLAP, PATH_PREFIX, NO_MIGRATE=1 (para pular migrações)

Requisitos:
- DB_* configurados no .env (ou no ambiente).
- OPENAI_API_KEY configurada (para embeddings e semantic chunking).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


# --- Helpers para ler env com valores vazios de forma segura ---
def env_str(name: str, default: str | None) -> str | None:
    val = os.getenv(name)
    if val is None:
        return default
    val = val.strip()
    return default if val == "" else val


def env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except Exception:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _load_env() -> None:
    # Carrega .env na raiz do repositório e o .env atual, sem sobrescrever já carregado
    load_dotenv(override=False)
    repo_root = Path(__file__).resolve().parents[1]
    env_alt = repo_root / ".env"
    if env_alt.exists():
        load_dotenv(env_alt, override=False)


def _ensure_migrations() -> None:
    import scripts.migrate as mig
    sql_dir = (Path(__file__).resolve().parents[1] / "sql" / "kb").resolve()
    conn_str = mig.db_url_from_env()
    files = [
        sql_dir / "00_docs_staging.sql",
        sql_dir / "01_init.sql",
        sql_dir / "02_indexes.sql",
        sql_dir / "03_functions.sql",
    ]
    assert all(f.exists() for f in files), "Arquivos SQL do KB ausentes"
    mig.apply_sql_files(conn_str, files, continue_on_error=False)


def parse_args() -> argparse.Namespace:
    _load_env()
    p = argparse.ArgumentParser(description="Fase 0 — staging e materialização do KB")
    p.add_argument("--base", dest="base", default=env_str("BASE_DIR", "tests/rag/data"), help="Diretório base com .md (default: tests/rag/data)")
    p.add_argument("--empresa", dest="empresa", default=env_str("EMPRESA", None), help="Nome da empresa para taguear os registros")
    p.add_argument("--client-id", dest="client_id", default=env_str("CLIENT_ID", None), help="Client ID (UUID) opcional")
    p.add_argument(
        "--strategies",
        nargs="*",
        default=((env_str("STRATEGIES", "fixed markdown semantic") or "fixed markdown semantic").split()),
        help="Estratégias de chunking (fixed/markdown/semantic)",
    )
    p.add_argument("--chunk-size", dest="chunk_size", type=int, default=env_int("CHUNK_SIZE", 400))
    p.add_argument("--chunk-overlap", dest="chunk_overlap", type=int, default=env_int("CHUNK_OVERLAP", 80))
    # Override apenas para fixed; markdown/semantic usam o tamanho geral
    p.add_argument("--fixed-chunk-size", dest="fixed_chunk_size", type=int, default=env_int("FIXED_CHUNK_SIZE", 200))
    p.add_argument("--fixed-chunk-overlap", dest="fixed_chunk_overlap", type=int, default=env_int("FIXED_CHUNK_OVERLAP", 40))
    p.add_argument("--path-prefix", dest="path_prefix", default=env_str("PATH_PREFIX", None), help="Prefixo do source_path (staging) para filtrar materialização")
    p.add_argument("--no-migrate", dest="no_migrate", action="store_true", default=env_bool("NO_MIGRATE", False))
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Checagem de API key (necessária para embeddings; semantic chunking também usa embeddings para cortes)
    if not os.getenv("OPENAI_API_KEY"):
        print("Erro: OPENAI_API_KEY não configurada. Defina no .env ou no ambiente para gerar embeddings.")
        return 2

    # Migrações do KB (idempotentes)
    if not args.no_migrate:
        print("[phase0] Aplicando migrações do KB…")
        _ensure_migrations()

    # Importa funções de ingestão
    try:
        from app.rag.ingest import (
            stage_docs_from_dir,
            materialize_chunks_from_staging,
            truncate_kb_tables,
        )
    except Exception as e:
        print(f"Erro ao importar pipeline de ingestão: {e}")
        return 1

    base_dir = Path(args.base)
    if not base_dir.exists():
        print(f"Erro: diretório base não existe: {base_dir}")
        return 2

    # Limpa tabelas para executar em ambiente limpo
    try:
        print("[phase0] Limpando tabelas do KB (truncate)…")
        truncate_kb_tables()
        print("[phase0] OK: KB limpo.")
    except Exception as e:
        print(f"[phase0] Aviso: falha ao limpar KB (seguindo mesmo assim): {e}")

    # Defaults robustos para estratégias (caso venham vazias do ambiente)
    if not args.strategies:
        args.strategies = ["fixed", "markdown", "semantic"]

    # Defaults robustos para estratégias (caso venham vazias do ambiente)
    if not args.strategies:
        args.strategies = ["fixed", "markdown", "semantic"]

    def _title_case_company(name: str) -> str:
        x = name.replace("_", " ").replace("-", " ")
        x = " ".join(w.capitalize() for w in x.split())
        return x

    total_chunks = 0

    # Modo A: empresa única fornecida
    if args.empresa:
        print(f"[phase0] Staging: base={base_dir} empresa={args.empresa} client_id={args.client_id or '-'}")
        staged = stage_docs_from_dir(str(base_dir), empresa=args.empresa, client_id=args.client_id)
        print(f"[phase0] Staged {staged} arquivo(s) em kb_docs.")

        for strat in args.strategies:
            s = strat.strip().lower()
            if s not in ("fixed", "markdown", "semantic"):
                print(f"[phase0] Estratégia ignorada (inválida): {strat}")
                continue
            # chunk params: fixed usa override; demais usam o geral
            if s == "fixed":
                cs = args.fixed_chunk_size or args.chunk_size
                co = args.fixed_chunk_overlap or args.chunk_overlap
            else:
                cs = args.chunk_size
                co = args.chunk_overlap
            if s == "fixed":
                print(f"[phase0] Materializando chunks: strategy=fixed cs={cs} ov={co} path_prefix={args.path_prefix or '-'} doc_path_prefix=fixed")
            elif s == "markdown":
                print(f"[phase0] Materializando chunks: strategy=markdown (header-based) path_prefix={args.path_prefix or '-'} doc_path_prefix=markdown")
            else:
                print(f"[phase0] Materializando chunks: strategy=semantic (embedding-guided) path_prefix={args.path_prefix or '-'} doc_path_prefix=semantic")
            n = materialize_chunks_from_staging(
                strategy=s,
                empresa=args.empresa,
                client_id=args.client_id,
                chunk_size=cs,
                chunk_overlap=co,
                path_prefix=args.path_prefix,
                doc_path_prefix=s,
            )
            total_chunks += n
            print(f"[phase0] -> {n} chunk(s) [{s}] para empresa '{args.empresa}'")

        # Resumo (opcional)
        try:
            import psycopg
            from app.agent.tools import get_db_url
            with psycopg.connect(get_db_url()) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "select count(*) from public.kb_docs where lower(empresa)=lower(%s)",
                        (args.empresa,),
                    )
                    docs_count = cur.fetchone()[0]
                    cur.execute(
                        "select meta->>'chunking' as chunking, count(*) from public.kb_chunks where lower(empresa)=lower(%s) group by 1 order by 1",
                        (args.empresa,),
                    )
                    rows = cur.fetchall() or []
            print("[phase0] Resumo:")
            print(f"  kb_docs(empresa={args.empresa}): {docs_count}")
            for chunking, c in rows:
                print(f"  kb_chunks(chunking={chunking}): {c}")
        except Exception:
            pass

        print(f"[phase0] Concluído. Total chunks gravados: {total_chunks}")
        return 0

    # Modo B: AUTO — sem empresa → usa subpastas do base como empresas
    print(f"[phase0] AUTO: empresa não informada; varrendo subpastas de {base_dir}.")
    subdirs = [p for p in base_dir.iterdir() if p.is_dir()]
    if not subdirs:
        print("[phase0] Nenhuma subpasta encontrada para autodetectar empresas.")
        return 0

    company_summaries: list[tuple[str, int, list[tuple[str, int]]]] = []
    for d in subdirs:
        empresa_name = _title_case_company(d.name)
        print(f"[phase0] Empresa detectada: '{empresa_name}' em '{d}'")
        # Staging por empresa
        staged = stage_docs_from_dir(str(d), empresa=empresa_name)
        print(f"[phase0] -> staged {staged} arquivo(s) de '{d.name}'")

        # Materialização por estratégia restringindo ao prefixo da subpasta
        per_strat_counts: list[tuple[str, int]] = []
        for strat in args.strategies:
            s = strat.strip().lower()
            if s not in ("fixed", "markdown", "semantic"):
                print(f"[phase0] Estratégia ignorada (inválida): {strat}")
                continue
            if s == "fixed":
                cs = args.fixed_chunk_size or args.chunk_size
                co = args.fixed_chunk_overlap or args.chunk_overlap
            else:
                cs = args.chunk_size
                co = args.chunk_overlap
            if s == "fixed":
                print(f"[phase0] Materializando chunks: strategy=fixed cs={cs} ov={co} path_prefix={str(d.as_posix())} doc_path_prefix=fixed")
            elif s == "markdown":
                print(f"[phase0] Materializando chunks: strategy=markdown (header-based) path_prefix={str(d.as_posix())} doc_path_prefix=markdown")
            else:
                print(f"[phase0] Materializando chunks: strategy=semantic (embedding-guided) path_prefix={str(d.as_posix())} doc_path_prefix=semantic")
            n = materialize_chunks_from_staging(
                strategy=s,
                empresa=empresa_name,
                chunk_size=cs,
                chunk_overlap=co,
                path_prefix=str(d.as_posix()),
                doc_path_prefix=s,
            )
            total_chunks += n
            per_strat_counts.append((s, n))
            print(f"[phase0] -> {n} chunk(s) [{s}] para empresa '{empresa_name}'")
        company_summaries.append((empresa_name, staged, per_strat_counts))

    # Resumo geral
    print("[phase0] Resumo AUTO:")
    for emp, staged, arr in company_summaries:
        print(f"  {emp}: staged={staged}")
        for s, n in arr:
            print(f"    chunks({s})={n}")
    print(f"[phase0] Concluído. Total chunks gravados: {total_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
