#!/bin/bash
# Script para parar, reconstruir e iniciar os containers

set -e

echo "🛑 Parando containers..."
sudo docker-compose down

echo "🔨 Reconstruindo imagens (sem cache)..."
sudo docker-compose build --no-cache

echo "🚀 Iniciando containers..."
sudo docker-compose up -d

echo "📊 Verificando status..."
sudo docker-compose ps

echo ""
echo "✅ Containers reconstruídos e iniciados!"
echo ""
echo "Para ver os logs:"
echo "  sudo docker-compose logs -f backend"
echo "  sudo docker-compose logs -f frontend"

