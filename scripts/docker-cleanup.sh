#!/bin/bash
# Script para limpar containers e volumes corrompidos do Docker

echo "Limpando containers e volumes do projeto..."

# Parar e remover containers
docker-compose down -v 2>/dev/null || true

# Remover containers órfãos/corrompidos
docker ps -a --filter "name=ai_agent" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true

# Remover volumes órfãos
docker volume ls --filter "name=ai_agent" --format "{{.Name}}" | xargs -r docker volume rm 2>/dev/null || true

# Remover networks órfãs
docker network ls --filter "name=ai_agent" --format "{{.ID}}" | xargs -r docker network rm 2>/dev/null || true

echo "Limpeza concluída!"

