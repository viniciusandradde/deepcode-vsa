#!/bin/bash
# Script para corrigir problemas com Docker Compose

set -e

echo "🔧 Corrigindo problemas do Docker Compose..."

# Verificar se está em modo swarm
if docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo "⚠️  Docker está em modo Swarm. Saindo do modo swarm..."
    docker swarm leave --force 2>/dev/null || true
fi

# Remover containers corrompidos
echo "🧹 Removendo containers corrompidos..."
docker ps -a --filter "name=ai_agent" --format "{{.Names}}" | while read container; do
    if [ ! -z "$container" ]; then
        echo "  Removendo: $container"
        docker rm -f "$container" 2>/dev/null || true
    fi
done

# Remover volumes órfãos
echo "🧹 Removendo volumes órfãos..."
docker volume ls --filter "name=template" --format "{{.Name}}" | while read volume; do
    if [ ! -z "$volume" ]; then
        echo "  Removendo volume: $volume"
        docker volume rm "$volume" 2>/dev/null || true
    fi
done

# Limpar usando docker-compose
echo "🧹 Limpando com docker-compose..."
docker-compose down -v --remove-orphans 2>/dev/null || true

echo "✅ Limpeza concluída!"
echo ""
echo "Agora você pode executar:"
echo "  docker-compose up -d --build"

