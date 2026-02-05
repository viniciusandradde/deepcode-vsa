#!/bin/bash
set -e

# Este script é executado após a inicialização do PostgreSQL
# O banco de dados já está criado e pronto

echo "Inicializando extensões e schemas do banco de dados..."

# Criar extensão pgvector se não existir
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

# Executar scripts SQL se existirem (em ordem específica)
SQL_DIR="/docker-entrypoint-initdb.d/sql/kb"
if [ -d "$SQL_DIR" ]; then
    echo "Executando scripts SQL de inicialização..."
    
    # Executar scripts em ordem numerada (01, 02, 03, ...)
    for script in $(ls "$SQL_DIR"/*.sql 2>/dev/null | sort -V); do
        if [ -f "$script" ]; then
            echo "Executando: $(basename $script)"
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$script"
        fi
    done
else
    echo "Aviso: Diretório SQL não encontrado: $SQL_DIR"
    echo "Os scripts SQL devem estar em: $SQL_DIR"
fi

echo "Banco de dados inicializado com sucesso!"

