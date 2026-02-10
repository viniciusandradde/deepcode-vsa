#!/bin/bash
set -e

if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
  echo "DB_HOST, DB_NAME e DB_USER precisam estar definidos."
  exit 1
fi

SQL_FILE="$(dirname "$0")/../sql/kb/06_files_schema.sql"

if [ ! -f "$SQL_FILE" ]; then
  echo "Arquivo SQL nao encontrado: $SQL_FILE"
  exit 1
fi

export PGPASSWORD="$DB_PASSWORD"

echo "Aplicando schema de arquivos..."
psql -v ON_ERROR_STOP=1 \
  --host "$DB_HOST" \
  --port "${DB_PORT:-5432}" \
  --username "$DB_USER" \
  --dbname "$DB_NAME" \
  -f "$SQL_FILE"

echo "Schema de arquivos aplicado com sucesso."
