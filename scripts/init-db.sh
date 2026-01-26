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
    
    # Executar scripts em ordem específica
    for script in "$SQL_DIR/01_init.sql" "$SQL_DIR/02_indexes.sql" "$SQL_DIR/03_functions.sql"; do
        if [ -f "$script" ]; then
            echo "Executando: $(basename $script)"
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$script"
        else
            echo "Aviso: Script não encontrado: $script"
        fi
    done
else
    echo "Aviso: Diretório SQL não encontrado: $SQL_DIR"
    echo "Os scripts SQL devem estar em: $SQL_DIR"
fi

echo "Banco de dados inicializado com sucesso!"

