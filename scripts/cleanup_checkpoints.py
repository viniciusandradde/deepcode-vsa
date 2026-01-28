#!/usr/bin/env python
"""
Script de limpeza de checkpoints antigos do LangGraph no PostgreSQL.

Objetivo:
- Remover registros de `checkpoints` e `checkpoint_writes` para threads
  sem atividade há mais de N dias (padrão: 180), usando o campo
  `checkpoint->>'ts'` como referência de última atividade.

Uso:
    python scripts/cleanup_checkpoints.py --days 180 --dry-run
    python scripts/cleanup_checkpoints.py --days 365
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

# Garantir que o diretório raiz do projeto esteja no PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from core.database import get_conn


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Limpar checkpoints antigos do LangGraph no PostgreSQL."
  )
  parser.add_argument(
    "--days",
    type=int,
    default=180,
    help="Idade mínima (em dias) para considerar uma thread inativa. Padrão: 180.",
  )
  parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Apenas exibe o que seria removido, sem executar DELETE.",
  )
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  days = args.days
  dry_run = args.dry_run

  print(f"🧹 Iniciando limpeza de checkpoints (limite: {days} dias, dry-run={dry_run})")
  now = datetime.now(timezone.utc).isoformat()
  print(f"⏱  Momento da execução: {now}")

  conn = get_conn()
  try:
    with conn:
      with conn.cursor() as cur:
        # Identificar threads antigas com base no timestamp do checkpoint
        cur.execute(
          """
          WITH old_threads AS (
            SELECT DISTINCT thread_id
            FROM checkpoints
            WHERE (checkpoint->>'ts')::timestamptz < (NOW() - (%s || ' days')::interval)
          )
          SELECT COUNT(*) FROM old_threads;
          """,
          (days,),
        )
        (thread_count,) = cur.fetchone()
        print(f"🔎 Threads candidatas à limpeza: {thread_count}")

        if thread_count == 0:
          print("✅ Nenhuma thread antiga encontrada. Nada a fazer.")
          return

        if dry_run:
          # Em modo dry-run, também mostramos uma amostra de thread_ids
          cur.execute(
            """
            WITH old_threads AS (
              SELECT DISTINCT thread_id
              FROM checkpoints
              WHERE (checkpoint->>'ts')::timestamptz < (NOW() - (%s || ' days')::interval)
            )
            SELECT thread_id
            FROM old_threads
            ORDER BY thread_id
            LIMIT 10;
            """,
            (days,),
          )
          rows = cur.fetchall()
          sample_ids = [r[0] for r in rows]
          print(f"📋 Exemplo de thread_ids antigas (até 10): {sample_ids}")
          print("💡 Rode novamente sem --dry-run para aplicar a limpeza.")
          return

        # DELETE real (não-dry-run)
        print("⚠️  Executando DELETE em checkpoint_writes e checkpoints...")

        # Apagar writes primeiro (FK lógica por thread_id)
        cur.execute(
          """
          WITH old_threads AS (
            SELECT DISTINCT thread_id
            FROM checkpoints
            WHERE (checkpoint->>'ts')::timestamptz < (NOW() - (%s || ' days')::interval)
          )
          DELETE FROM checkpoint_writes
          WHERE thread_id IN (SELECT thread_id FROM old_threads);
          """,
          (days,),
        )
        writes_deleted = cur.rowcount

        # Apagar checkpoints
        cur.execute(
          """
          WITH old_threads AS (
            SELECT DISTINCT thread_id
            FROM checkpoints
            WHERE (checkpoint->>'ts')::timestamptz < (NOW() - (%s || ' days')::interval)
          )
          DELETE FROM checkpoints
          WHERE thread_id IN (SELECT thread_id FROM old_threads);
          """,
          (days,),
        )
        checkpoints_deleted = cur.rowcount

        print(f"✅ Linhas removidas em checkpoint_writes: {writes_deleted}")
        print(f"✅ Linhas removidas em checkpoints: {checkpoints_deleted}")

  finally:
    conn.close()
    print("ℹ️  Conexão com o banco encerrada.")


if __name__ == "__main__":
  main()

