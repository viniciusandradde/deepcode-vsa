#!/bin/bash
echo "🔄 Aplicando correções..."
echo ""
echo "1. Reiniciando frontend para carregar novas variáveis de ambiente..."
docker-compose restart frontend
echo ""
echo "2. Aguardando frontend iniciar..."
sleep 5
echo ""
echo "3. Verificando variáveis de ambiente..."
docker-compose exec frontend env | grep -E "API_BASE|NEXT_PUBLIC" || echo "⚠️  Container ainda não está pronto, aguarde alguns segundos"
echo ""
echo "✅ Correções aplicadas!"
echo ""
echo "📋 Próximos passos:"
echo "   - Verifique os logs: docker-compose logs -f frontend"
echo "   - Teste no navegador: http://localhost:3000"
