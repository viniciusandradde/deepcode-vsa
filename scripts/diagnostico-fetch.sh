#!/bin/bash

echo "🔍 Diagnóstico de Conectividade - Fetch Failed"
echo "================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 está instalado"
        return 0
    else
        echo -e "${RED}✗${NC} $1 não está instalado"
        return 1
    fi
}

# Verificar se docker-compose está disponível
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Erro: docker-compose não encontrado${NC}"
    exit 1
fi

echo "1. Verificando status dos containers..."
echo "----------------------------------------"
docker-compose ps
echo ""

echo "2. Verificando se containers estão na mesma rede..."
echo "---------------------------------------------------"
NETWORK_NAME=$(docker-compose ps -q frontend | xargs docker inspect --format='{{range $net, $v := .NetworkSettings.Networks}}{{$net}}{{end}}' 2>/dev/null | head -1)
if [ -n "$NETWORK_NAME" ]; then
    echo -e "${GREEN}✓${NC} Frontend está na rede: $NETWORK_NAME"
    
    # Verificar se backend está na mesma rede
    BACKEND_NETWORK=$(docker-compose ps -q backend | xargs docker inspect --format='{{range $net, $v := .NetworkSettings.Networks}}{{$net}}{{end}}' 2>/dev/null | head -1)
    if [ "$NETWORK_NAME" = "$BACKEND_NETWORK" ]; then
        echo -e "${GREEN}✓${NC} Backend está na mesma rede: $BACKEND_NETWORK"
    else
        echo -e "${RED}✗${NC} Backend está em rede diferente: $BACKEND_NETWORK"
    fi
else
    echo -e "${RED}✗${NC} Não foi possível determinar a rede do frontend"
fi
echo ""

echo "3. Verificando variáveis de ambiente no container frontend..."
echo "-------------------------------------------------------------"
echo "API_BASE_URL:"
docker-compose exec -T frontend env 2>/dev/null | grep "API_BASE_URL" || echo -e "${YELLOW}⚠ Não encontrado${NC}"
echo "NEXT_PUBLIC_API_BASE:"
docker-compose exec -T frontend env 2>/dev/null | grep "NEXT_PUBLIC_API_BASE" || echo -e "${YELLOW}⚠ Não encontrado${NC}"
echo ""

echo "4. Testando resolução DNS do serviço 'backend'..."
echo "--------------------------------------------------"
if docker-compose exec -T frontend nslookup backend 2>/dev/null | grep -q "Name:"; then
    echo -e "${GREEN}✓${NC} DNS resolve 'backend' corretamente"
    docker-compose exec -T frontend nslookup backend 2>/dev/null | grep -A 2 "Name:"
else
    echo -e "${RED}✗${NC} DNS não resolve 'backend'"
    echo "Tentando com getent..."
    docker-compose exec -T frontend getent hosts backend 2>/dev/null || echo -e "${RED}✗${NC} getent também falhou"
fi
echo ""

echo "5. Testando conectividade de rede (ping)..."
echo "--------------------------------------------"
if docker-compose exec -T frontend ping -c 2 backend 2>/dev/null | grep -q "2 packets transmitted"; then
    echo -e "${GREEN}✓${NC} Ping para 'backend' funcionou"
    docker-compose exec -T frontend ping -c 2 backend 2>/dev/null | tail -2
else
    echo -e "${RED}✗${NC} Ping para 'backend' falhou"
fi
echo ""

echo "6. Testando conectividade HTTP (curl)..."
echo "----------------------------------------"
echo "Testando: http://backend:8000/health"
HTTP_TEST=$(docker-compose exec -T frontend curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://backend:8000/health 2>/dev/null)
if [ "$HTTP_TEST" = "200" ]; then
    echo -e "${GREEN}✓${NC} Backend respondeu com HTTP 200"
    echo "Resposta completa:"
    docker-compose exec -T frontend curl -s --max-time 5 http://backend:8000/health 2>/dev/null | head -5
elif [ -n "$HTTP_TEST" ]; then
    echo -e "${YELLOW}⚠${NC} Backend respondeu com HTTP $HTTP_TEST"
    docker-compose exec -T frontend curl -s --max-time 5 http://backend:8000/health 2>/dev/null | head -5
else
    echo -e "${RED}✗${NC} Não foi possível conectar ao backend"
    echo "Erro detalhado:"
    docker-compose exec -T frontend curl -v --max-time 5 http://backend:8000/health 2>&1 | head -10
fi
echo ""

echo "7. Verificando logs recentes do frontend..."
echo "-------------------------------------------"
echo "Últimas 20 linhas dos logs do frontend:"
docker-compose logs --tail=20 frontend 2>/dev/null | grep -E "\[DEBUG\]|\[ERROR\]|\[CONFIG\]" || echo "Nenhum log de debug encontrado"
echo ""

echo "8. Verificando logs recentes do backend..."
echo "-------------------------------------------"
echo "Últimas 20 linhas dos logs do backend:"
docker-compose logs --tail=20 backend 2>/dev/null | tail -20
echo ""

echo "9. Testando URL completa do endpoint de stream..."
echo "--------------------------------------------------"
TEST_URL="http://backend:8000/api/v1/chat/stream"
echo "Testando: $TEST_URL"
echo "Enviando requisição de teste..."
RESPONSE=$(docker-compose exec -T frontend curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"test","model":"google/gemini-2.5-flash","use_tavily":false}' \
  --max-time 10 \
  "$TEST_URL" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "500" ]; then
    echo -e "${GREEN}✓${NC} Endpoint respondeu (HTTP $HTTP_CODE)"
    echo "Primeiras linhas da resposta:"
    echo "$RESPONSE" | head -5
else
    echo -e "${RED}✗${NC} Endpoint não respondeu corretamente"
    echo "Resposta completa:"
    echo "$RESPONSE"
fi
echo ""

echo "10. Resumo e Recomendações..."
echo "------------------------------"
echo ""
echo "Se o diagnóstico mostrar problemas:"
echo "  1. Verifique se ambos os containers estão rodando: docker-compose ps"
echo "  2. Verifique se estão na mesma rede Docker"
echo "  3. Reinicie os containers: docker-compose restart frontend backend"
echo "  4. Verifique as variáveis de ambiente no docker-compose.yml"
echo "  5. Verifique os logs completos: docker-compose logs -f frontend"
echo ""
echo "✅ Diagnóstico concluído!"

