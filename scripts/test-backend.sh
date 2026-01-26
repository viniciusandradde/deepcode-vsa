#!/bin/bash
# Script para testar o backend manualmente

echo "🧪 Testando Backend API..."
echo ""

echo "1. Testando health endpoint..."
curl -s http://localhost:8000/health | jq . || echo "❌ Health check falhou"
echo ""

echo "2. Testando endpoint de chat (stream)..."
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá, teste",
    "model": "google/gemini-2.5-flash",
    "use_tavily": false,
    "thread_id": "test-123"
  }' \
  -N \
  --max-time 10 \
  || echo "❌ Stream falhou"
echo ""

echo "3. Verificando variáveis de ambiente no backend..."
docker-compose exec backend env | grep -E "(OPENAI|OPENROUTER|DB_)" || echo "⚠️  Não foi possível verificar (pode precisar de sudo)"
echo ""

echo "✅ Testes concluídos!"

