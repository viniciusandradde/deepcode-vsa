# Guia de Testes: n8n Workflows

## 📋 Índice

1. [Estratégia de Testes](#estratégia-de-testes)
2. [Testes Unitários (Sub-workflows)](#testes-unitários-sub-workflows)
3. [Testes de Integração](#testes-de-integração)
4. [Testes de Performance](#testes-de-performance)
5. [Testes de Erro e Recuperação](#testes-de-erro-e-recuperação)
6. [Automação de Testes](#automação-de-testes)
7. [Checklist de Validação](#checklist-de-validação)

---

## Estratégia de Testes

### Pirâmide de Testes

```
          ┌─────────────────┐
          │   End-to-End    │  ← Testes completos (Frontend → n8n → Backend)
          │   (5% dos tests)│
          └─────────────────┘
         ┌───────────────────┐
         │   Integration      │   ← Testes de workflows completos
         │  (25% dos tests)   │
         └───────────────────┘
        ┌─────────────────────┐
        │   Unit Tests         │    ← Testes de sub-workflows individuais
        │  (70% dos tests)     │
        └─────────────────────┘
```

### Tipos de Testes

| Tipo | Objetivo | Ferramenta | Fase |
|------|----------|------------|------|
| **Unit** | Testar sub-workflows isoladamente | n8n UI + curl | Fase 1, 2, 3 |
| **Integration** | Testar fluxo completo (UnifiedAgent → Sub-workflows) | Postman/curl | Fase 3 |
| **Performance** | Validar latência < 3s | Apache Bench (ab) | Todas fases |
| **Error Handling** | Validar retry e fallback | Simulação de erros | Todas fases |
| **E2E** | Testar via Frontend Next.js | Manual/Playwright | Fase 4 |

---

## Testes Unitários (Sub-workflows)

### 1. Teste: GLPI List Tickets

#### Objetivo

Validar que o sub-workflow `vsa-glpi-integration` lista tickets corretamente.

#### Pré-requisitos

- ✅ GLPI está acessível
- ✅ Credenciais GLPI configuradas no n8n
- ✅ Workflow `vsa-glpi-integration` ativado

#### Passos (Manual - n8n UI)

1. Abrir n8n: `http://localhost:5678`
2. Navegar para workflow: `vsa-glpi-integration`
3. Clicar em **Manual Trigger** node
4. Clicar em **"Execute node"**
5. Inserir input JSON:

```json
{
  "action": "list_tickets",
  "limit": 5
}
```

6. Clicar em **"Execute Workflow"**
2. Verificar output em cada node

#### Validação

| Node | Verificação | Critério de Sucesso |
|------|-------------|---------------------|
| **GLPI Auth** | Response contém `session_token` | ✅ Token é string de 40 caracteres |
| **Switch Action** | Branch selecionado = "List Tickets" | ✅ Roteou corretamente |
| **GLPI List Tickets** | Response é array de tickets | ✅ Array com 5 itens |
| **GLPI Logout** | Response sem erro | ✅ Status 200 |

**Expected Final Output:**

```json
{
  "tickets": [
    { "id": 1234, "name": "Servidor offline", "status": 2, "urgency": 5 },
    { "id": 1235, "name": "Impressora não funciona", "status": 1, "urgency": 3 },
    { "id": 1236, "name": "VPN não conecta", "status": 2, "urgency": 4 },
    { "id": 1237, "name": "Email bouncing", "status": 3, "urgency": 2 },
    { "id": 1238, "name": "Lentidão no sistema", "status": 1, "urgency": 2 }
  ],
  "count": 5
}
```

---

#### Passos (Automatizado - curl)

```bash
# Testar via webhook
curl -X POST http://localhost:5678/webhook/vsa/glpi \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list_tickets",
    "limit": 5
  }' | jq '.'
```

**Validar output:**

```bash
# Verificar que retornou 5 tickets
curl -X POST http://localhost:5678/webhook/vsa/glpi \
  -H "Content-Type: application/json" \
  -d '{"action":"list_tickets","limit":5}' \
  | jq '.tickets | length'

# Output esperado: 5
```

---

### 2. Teste: GLPI Get Ticket

#### Input

```json
{
  "action": "get_ticket",
  "ticket_id": 1234
}
```

#### Expected Output

```json
{
  "id": 1234,
  "name": "Servidor offline",
  "content": "Servidor web01 não responde a ping desde 10:00",
  "status": 2,
  "urgency": 5,
  "priority": 5,
  "date_creation": "2026-02-04 10:00:00"
}
```

#### Validação

- ✅ Retorna ticket com ID correto
- ✅ Campo `content` contém descrição detalhada

---

### 3. Teste: GLPI Create Ticket

#### Input

```json
{
  "action": "create_ticket",
  "title": "[TESTE n8n] Validação de workflow",
  "description": "Ticket criado automaticamente para testar workflow n8n",
  "urgency": 3
}
```

#### Expected Output

```json
{
  "id": 1250,
  "message": "Ticket criado com sucesso"
}
```

#### Validação

- ✅ Response contém field `id` (número)
- ✅ Ticket aparece no GLPI UI com título "[TESTE n8n]..."

---

### 4. Teste: Zabbix Get Alerts

#### Input

```json
{
  "action": "get_alerts",
  "limit": 3
}
```

#### Expected Output

```json
{
  "data": [
    {
      "eventid": "12345",
      "name": "Server web01: High CPU usage",
      "severity": "4",
      "clock": "1707064800"
    },
    {
      "eventid": "12346",
      "name": "Server db01: Memory critical",
      "severity": "5",
      "clock": "1707064820"
    }
  ],
  "count": 2
}
```

#### Validação

- ✅ Array `data` contém até 3 alertas
- ✅ Cada alerta tem `eventid`, `name`, `severity`

---

### 5. Teste: Zabbix Get Host

#### Input

```json
{
  "action": "get_host",
  "hostname": "web01"
}
```

#### Expected Output

```json
{
  "data": [
    {
      "hostid": "10084",
      "host": "web01",
      "name": "Web Server 01",
      "status": "0"
    }
  ],
  "count": 1
}
```

---

### 6. Teste: Linear List Issues

#### Input

```json
{
  "action": "list_issues",
  "team_key": "ENG",
  "limit": 5
}
```

#### Expected Output

```json
{
  "data": {
    "issues": {
      "nodes": [
        {
          "id": "abc-123",
          "title": "Fix login bug",
          "state": { "name": "In Progress" },
          "priority": 1,
          "createdAt": "2026-02-01T10:00:00Z"
        }
      ]
    }
  },
  "count": 5
}
```

---

## Testes de Integração

### 1. Teste: UnifiedAgent → GLPI

**Objetivo:** Validar fluxo completo do UnifiedAgent chamando sub-workflow GLPI

#### Pré-requisitos

- ✅ Workflow `vsa-unified-agent` criado (Fase 3)
- ✅ Sub-workflow `vsa-glpi-integration` ativado

#### Input (Frontend simulado)

```json
{
  "message": "Liste os últimos 3 tickets críticos do GLPI",
  "thread_id": "test-thread-001",
  "enable_vsa": true,
  "enable_glpi": true
}
```

#### Fluxo Esperado

```
1. UnifiedAgent: Router Node
   ↓ Intent: "it_request"

2. UnifiedAgent: Classifier Node (ITIL)
   ↓ Category: "CONSULTA", Priority: "MEDIO"

3. UnifiedAgent: Planner Node
   ↓ Plan: [{"step":1,"action":"list_tickets","tool":"glpi","params":{"limit":3}}]

4. UnifiedAgent: Executor Node
   ↓ Call: Execute Workflow (vsa-glpi-integration)

5. GLPI Integration: Auth → List → Logout
   ↓ Response: {"tickets": [...], "count": 3}

6. UnifiedAgent: Responder Node
   ↓ LLM formata resposta markdown com tabela ITIL
```

#### Expected Final Output (Frontend)

```
🔍 Classificação: CONSULTA
📊 Prioridade: MÉDIA

Últimos 3 tickets críticos encontrados:

| ID   | Título              | Status      | Urgência | Criado em        |
|------|---------------------|-------------|----------|------------------|
| 1234 | Servidor offline    | Processando | Crítica  | 04/02/2026 10:00 |
| 1235 | Banco lento         | Novo        | Alta     | 04/02/2026 09:30 |
| 1236 | VPN não conecta     | Processando | Alta     | 04/02/2026 08:15 |
```

#### Validação

- ✅ Router detectou intent corretamente
- ✅ Classifier categorizou como "CONSULTA"
- ✅ Planner criou plano com tool="glpi"
- ✅ Executor chamou sub-workflow GLPI
- ✅ Resposta formatada como markdown

---

### 2. Teste: Correlação GLPI ↔ Zabbix

**Objetivo:** Validar workflow que correlaciona tickets GLPI com alertas Zabbix

#### Input

```json
{
  "message": "Correlacione alertas Zabbix com tickets GLPI para servidor web01",
  "enable_vsa": true,
  "enable_glpi": true,
  "enable_zabbix": true
}
```

#### Fluxo Esperado

```
1. UnifiedAgent: Planner
   ↓ Plan: [
       {"step":1,"action":"get_host","tool":"zabbix","params":{"hostname":"web01"}},
       {"step":2,"action":"get_alerts","tool":"zabbix"},
       {"step":3,"action":"list_tickets","tool":"glpi"},
       {"step":4,"action":"correlate","tool":"internal"}
     ]

2. Executor: Loop sobre plano
   ↓ Call Zabbix: get_host (web01)
   ↓ Call Zabbix: get_alerts
   ↓ Call GLPI: list_tickets
   ↓ Correlate: Match hostname/timestamp

3. Responder: Formatar timeline
```

#### Expected Output

```
📋 Correlação: Servidor web01

Timeline:
- 10:30 - ⚠️ Alerta Zabbix: CPU 100%
- 10:32 - ⚠️ Alerta Zabbix: Memory critical
- 10:35 - 🎫 Ticket GLPI #1234: "Servidor offline"

💡 Análise:
Ticket GLPI aberto 5 minutos após primeiro alerta Zabbix.
Possível causa raiz: Sobrecarga de CPU/Memory.
```

---

## Testes de Performance

### 1. Benchmark: Latência de Sub-workflows

**Tool:** Apache Bench

```bash
# Instalar Apache Bench
sudo apt install apache2-utils

# Testar GLPI (100 requisições, 10 concorrentes)
ab -n 100 -c 10 -p glpi-test.json -T application/json \
  http://localhost:5678/webhook/vsa/glpi
```

**Arquivo:** `glpi-test.json`

```json
{"action":"list_tickets","limit":5}
```

**Análise de Resultados:**

```
Concurrency Level:      10
Time taken for tests:   15.234 seconds
Complete requests:      100
Failed requests:        0
Requests per second:    6.56 [#/sec]
Time per request:       152.34 [ms] (mean)
Time per request:       15.23 [ms] (mean, across all concurrent requests)
```

**Critérios de Sucesso:**

- ✅ Time per request < 3000ms (3s)
- ✅ Failed requests = 0
- ✅ Requests per second > 5

---

### 2. Benchmark: RAG Search

```bash
# Testar RAG Search (50 requisições)
ab -n 50 -c 5 -p rag-test.json -T application/json \
  http://localhost:5678/webhook/vsa/rag/search
```

**Arquivo:** `rag-test.json`

```json
{"query":"como configurar GLPI?","k":5,"empresa":"vsa_tecnologia"}
```

**Critério de Sucesso:**

- ✅ Time per request < 2000ms (busca RAG deve ser rápida)

---

### 3. Teste de Carga: UnifiedAgent Completo

```bash
# Simular 20 usuários simultâneos
ab -n 20 -c 20 -p unified-test.json -T application/json \
  http://localhost:5678/webhook/vsa/chat
```

**Arquivo:** `unified-test.json`

```json
{"message":"Liste tickets GLPI","enable_vsa":true,"enable_glpi":true}
```

---

## Testes de Erro e Recuperação

### 1. Teste: GLPI Indisponível

**Objetivo:** Validar error handling quando GLPI está offline

#### Passos

1. Desligar GLPI (ou usar URL inválida):

```bash
# Alterar .env.n8n temporariamente
GLPI_BASE_URL=http://glpi-fake.local
```

1. Reiniciar n8n:

```bash
docker compose -f docker-compose.n8n.yml restart
```

1. Executar workflow:

```bash
curl -X POST http://localhost:5678/webhook/vsa/glpi \
  -d '{"action":"list_tickets"}'
```

#### Expected Behavior

**n8n UI:**

- ❌ Execução marcada como **"error"**
- Node "GLPI Auth" em vermelho
- Error message: "ECONNREFUSED" ou "timeout"

**Response (se error handling implementado):**

```json
{
  "status": "error",
  "message": "Erro ao conectar com GLPI. Verifique se o serviço está disponível.",
  "action": "list_tickets",
  "retry_after": 300
}
```

---

### 2. Teste: Credenciais Inválidas

**Input:**

```bash
# Usar token GLPI inválido
GLPI_USER_TOKEN=invalid-token-12345
```

**Expected Error:**

```json
{
  "status": "error",
  "message": "401 Unauthorized: Token GLPI inválido",
  "action": "list_tickets"
}
```

---

### 3. Teste: Retry Automático

**Configuração n8n:**

```yaml
# Em cada HTTP Request node
settings:
  retry:
    enabled: true
    maxRetries: 3
    retryInterval: 1000ms
```

**Validação:**

- ✅ n8n tenta 3 vezes antes de falhar
- ✅ Log mostra tentativas: "Retry 1/3", "Retry 2/3", "Retry 3/3"

---

## Automação de Testes

### 1. Script Bash: Teste Completo Fase 1

**Arquivo:** `scripts/test-n8n-fase1.sh`

```bash
#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🧪 Iniciando testes n8n Fase 1..."

# Função de teste
test_workflow() {
  local name=$1
  local url=$2
  local payload=$3
  local expected_field=$4
  
  echo -n "Testando $name... "
  
  response=$(curl -s -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$payload")
  
  if echo "$response" | jq -e ".$expected_field" > /dev/null; then
    echo -e "${GREEN}✅ PASSOU${NC}"
    return 0
  else
    echo -e "${RED}❌ FALHOU${NC}"
    echo "Response: $response"
    return 1
  fi
}

# Testes GLPI
test_workflow "GLPI List Tickets" \
  "http://localhost:5678/webhook/vsa/glpi" \
  '{"action":"list_tickets","limit":5}' \
  "tickets"

test_workflow "GLPI Get Ticket" \
  "http://localhost:5678/webhook/vsa/glpi" \
  '{"action":"get_ticket","ticket_id":1234}' \
  "id"

# Testes Zabbix
test_workflow "Zabbix Get Alerts" \
  "http://localhost:5678/webhook/vsa/zabbix" \
  '{"action":"get_alerts","limit":3}' \
  "data"

test_workflow "Zabbix Get Host" \
  "http://localhost:5678/webhook/vsa/zabbix" \
  '{"action":"get_host","hostname":"web01"}' \
  "data"

# Testes Linear
test_workflow "Linear List Issues" \
  "http://localhost:5678/webhook/vsa/linear" \
  '{"action":"list_issues","team_key":"ENG","limit":5}' \
  "data"

echo ""
echo "🏁 Testes finalizados!"
```

**Uso:**

```bash
chmod +x scripts/test-n8n-fase1.sh
./scripts/test-n8n-fase1.sh
```

---

### 2. Postman Collection

**Arquivo:** `docs/postman/DeepCode-VSA-n8n.postman_collection.json`

```json
{
  "info": {
    "name": "DeepCode VSA - n8n Workflows",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "GLPI",
      "item": [
        {
          "name": "List Tickets",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "url": "http://localhost:5678/webhook/vsa/glpi",
            "body": {
              "mode": "raw",
              "raw": "{\n  \"action\": \"list_tickets\",\n  \"limit\": 5\n}"
            }
          }
        },
        {
          "name": "Get Ticket",
          "request": {
            "method": "POST",
            "url": "http://localhost:5678/webhook/vsa/glpi",
            "body": {
              "mode": "raw",
              "raw": "{\n  \"action\": \"get_ticket\",\n  \"ticket_id\": 1234\n}"
            }
          }
        }
      ]
    }
  ]
}
```

**Importar no Postman:**

1. Abrir Postman
2. **Import** → **File** → Selecionar JSON
3. Executar testes

---

## Checklist de Validação

### Fase 1: Integrações

#### GLPI Integration

- [ ] ✅ Teste unitário: List Tickets
- [ ] ✅ Teste unitário: Get Ticket
- [ ] ✅ Teste unitário: Create Ticket
- [ ] ✅ Teste de erro: 401 Unauthorized
- [ ] ✅ Teste de performance: < 3s
- [ ] ✅ Webhook funcionando: `/webhook/vsa/glpi`

#### Zabbix Integration

- [ ] ✅ Teste unitário: Get Alerts
- [ ] ✅ Teste unitário: Get Host
- [ ] ✅ Teste de erro: API Token inválido
- [ ] ✅ Teste de performance: < 2s
- [ ] ✅ Webhook funcionando: `/webhook/vsa/zabbix`

#### Linear Integration

- [ ] ✅ Teste unitário: List Issues
- [ ] ✅ Teste unitário: Get Issue
- [ ] ✅ Teste unitário: Create Issue
- [ ] ✅ Teste de erro: GraphQL syntax error
- [ ] ✅ Teste de performance: < 2s
- [ ] ✅ Webhook funcionando: `/webhook/vsa/linear`

---

### Fase 2: RAG Pipeline

- [ ] ✅ Teste: RAG Search (vector)
- [ ] ✅ Teste: RAG Search (text)
- [ ] ✅ Teste: RAG Search (hybrid)
- [ ] ✅ Teste: RAG Ingestion (arquivo novo)
- [ ] ✅ Teste de performance: Search < 2s

---

### Fase 3: UnifiedAgent

- [ ] ✅ Teste: Router (intent detection)
- [ ] ✅ Teste: Classifier (ITIL categorization)
- [ ] ✅ Teste: Planner (action plan)
- [ ] ✅ Teste: Executor (tool calls)
- [ ] ✅ Teste integração: UnifiedAgent → GLPI
- [ ] ✅ Teste integração: UnifiedAgent → Zabbix
- [ ] ✅ Teste integração: Correlação GLPI ↔ Zabbix
- [ ] ✅ Teste de performance: End-to-end < 10s

---

## Template de Resultado de Teste

**Arquivo:** `test-results-YYYY-MM-DD.md`

```markdown
# Resultados de Teste - n8n Workflows

**Data:** 04/02/2026  
**Tester:** [Nome]  
**Fase:** Fase 1 - Integrações

---

## GLPI Integration

| Teste | Status | Latência | Observações |
|-------|--------|----------|-------------|
| List Tickets | ✅ PASSOU | 1.2s | - |
| Get Ticket | ✅ PASSOU | 0.8s | - |
| Create Ticket | ✅ PASSOU | 1.5s | Ticket #1250 criado |
| Error: 401 | ✅ PASSOU | - | Mensagem de erro correta |

---

## Zabbix Integration

| Teste | Status | Latência | Observações |
|-------|--------|----------|-------------|
| Get Alerts | ✅ PASSOU | 0.9s | 3 alertas retornados |
| Get Host | ✅ PASSOU | 0.7s | Host web01 encontrado |

---

## Resumo

**Total de testes:** 6  
**Passou:** 6  
**Falhou:** 0  
**Taxa de sucesso:** 100%

**Próximos passos:**
- Continuar para Fase 2 (RAG Pipeline)
```

---

**Data:** 04/02/2026  
**Versão:** 1.0  
**Autor:** DeepCode VSA Team
