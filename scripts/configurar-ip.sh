#!/bin/bash

echo "🔧 Configuração para Acesso via IP"
echo ""

# Detectar IP atual
CURRENT_IP=$(hostname -I | awk '{print $1}')
echo "IP detectado: $CURRENT_IP"
echo ""

read -p "Digite o IP do servidor (ou pressione Enter para usar $CURRENT_IP): " SERVER_IP
SERVER_IP=${SERVER_IP:-$CURRENT_IP}

echo ""
echo "📝 Configurando NEXT_PUBLIC_API_BASE=http://${SERVER_IP}:8000"
echo ""

# Adicionar ou atualizar no .env
if grep -q "NEXT_PUBLIC_API_BASE" .env 2>/dev/null; then
    # Atualizar linha existente
    sed -i "s|NEXT_PUBLIC_API_BASE=.*|NEXT_PUBLIC_API_BASE=http://${SERVER_IP}:8000|" .env
    echo "✅ Variável NEXT_PUBLIC_API_BASE atualizada no .env"
else
    # Adicionar nova linha
    echo "" >> .env
    echo "# URL do backend para acesso via IP" >> .env
    echo "NEXT_PUBLIC_API_BASE=http://${SERVER_IP}:8000" >> .env
    echo "✅ Variável NEXT_PUBLIC_API_BASE adicionada ao .env"
fi

echo ""
echo "🔄 Reiniciando frontend para aplicar mudanças..."
docker-compose restart frontend

echo ""
echo "⏳ Aguardando frontend iniciar..."
sleep 5

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "📋 Próximos passos:"
echo "   - Acesse: http://${SERVER_IP}:3000"
echo "   - Backend: http://${SERVER_IP}:8000"
echo "   - Verifique logs: docker-compose logs -f frontend"
