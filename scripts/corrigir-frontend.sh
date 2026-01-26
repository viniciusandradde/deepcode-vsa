#!/bin/bash

echo "🔧 Corrigindo configuração do frontend..."
echo ""

echo "1. Parando container frontend..."
sudo docker-compose stop frontend

echo ""
echo "2. Removendo container frontend (para forçar recriação)..."
sudo docker-compose rm -f frontend

echo ""
echo "3. Recriando container frontend com novas variáveis..."
sudo docker-compose up -d frontend

echo ""
echo "4. Aguardando container iniciar..."
sleep 5

echo ""
echo "5. Verificando variáveis de ambiente..."
echo "----------------------------------------"
sudo docker-compose exec -T frontend env 2>/dev/null | grep -E "API_BASE|NEXT_PUBLIC" || echo "⚠️  Container ainda iniciando..."

echo ""
echo "6. Verificando logs iniciais..."
echo "--------------------------------"
sudo docker-compose logs --tail=30 frontend | grep -E "\[CONFIG\]|\[DEBUG\]|ready" || echo "Aguardando logs..."

echo ""
echo "✅ Correção aplicada!"
echo ""
echo "📋 Próximos passos:"
echo "   - Verifique os logs: sudo docker-compose logs -f frontend"
echo "   - Execute o diagnóstico: ./scripts/diagnostico-fetch.sh"
echo "   - Teste no navegador: http://10.10.1.105:3000"
