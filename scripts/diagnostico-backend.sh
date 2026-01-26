#!/bin/bash
# Script de diagnóstico do backend

echo "🔍 Diagnóstico do Backend"
echo "========================"
echo ""

echo "1. Verificando se o backend está rodando..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend está acessível"
else
    echo "❌ Backend não está acessível na porta 8000"
    exit 1
fi

echo ""
echo "2. Verificando health check detalhado..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
echo ""

echo ""
echo "3. Verificando variáveis de ambiente no container..."
echo "   (Pode precisar de sudo)"
docker-compose exec backend env | grep -E "(OPENAI|OPENROUTER|DB_)" || echo "⚠️  Não foi possível verificar (pode precisar de sudo)"
echo ""

echo ""
echo "4. Testando endpoint de chat (stream)..."
echo "   Enviando requisição de teste..."
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Teste",
    "model": "google/gemini-2.5-flash",
    "use_tavily": false
  }' \
  -N \
  --max-time 5 \
  2>&1 | head -20 || echo "❌ Erro ao testar stream"
echo ""

echo ""
echo "✅ Diagnóstico concluído!"
echo ""
echo "💡 Dicas:"
echo "   - Se API keys não estiverem configuradas, adicione no arquivo .env"
echo "   - Verifique os logs: sudo docker-compose logs -f backend"
echo "   - Teste o health check: curl http://localhost:8000/health"

