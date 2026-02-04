# Guia de Implementação: Workflows Fase 1

## 📋 Índice

1. [Visão Geral Fase 1](#visão-geral-fase-1)
2. [Sub-workflow: GLPI Integration](#sub-workflow-glpi-integration)
3. [Sub-workflow: Zabbix Integration](#sub-workflow-zabbix-integration)
4. [Sub-workflow: Linear Integration](#sub-workflow-linear-integration)
5. [Testes e Validação](#testes-e-validação)
6. [Troubleshooting](#troubleshooting)

---

## Visão Geral Fase 1

### Objetivo

Criar **3 sub-workflows** no n8n que substituem os clientes Python existentes:

| Python Client | n8n Workflow | Endpoint Webhook |
|---------------|--------------|------------------|
| `glpi_client.py` | `vsa-glpi-integration` | `/webhook/vsa/glpi` |
| `zabbix_client.py` | `vsa-zabbix-integration` | `/webhook/vsa/zabbix` |
| `linear_client.py` | `vsa-linear-integration` | `/webhook/vsa/linear` |

### Arquitetura

```
Frontend/API → Webhook n8n → Sub-workflow → API Externa → Resposta
```

**Exemplo (GLPI):**

```
POST /webhook/vsa/glpi
  {"action": "list_tickets", "limit": 5}
    ↓
n8n: vsa-glpi-integration
  1. GLPI Auth (initSession)
  2. Switch (action)
  3. GLPI List Tickets
  4. GLPI Logout (killSession)
    ↓
Response: {"tickets": [...], "count": 5}
```

---

## Sub-workflow: GLPI Integration

### Estrutura do Workflow

**Nome:** `vsa-glpi-integration`  
**Trigger:** Execute Workflow Trigger (chamado por workflows pai)  
**Webhook alternativo:** `/webhook/vsa/glpi` (para testes diretos)

### Nodes

#### 1. **Trigger Node**

**Tipo:** `n8n-nodes-base.executeWorkflowTrigger`

**Configuração:**

- Aceita input JSON com campos:
  - `action` (string): "list_tickets", "get_ticket", "create_ticket"
  - `limit` (number, opcional): Limite de resultados
  - `ticket_id` (number, opcional): ID do ticket (para get_ticket)
  - `title` (string, opcional): Título do ticket (para create_ticket)
  - `description` (string, opcional): Descrição do ticket
  - `urgency` (number, opcional): 1-5 (para create_ticket)

**Exemplo Input:**

```json
{
  "action": "list_tickets",
  "limit": 10
}
```

---

#### 2. **GLPI Auth Node**

**Objetivo:** Iniciar sessão GLPI

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | GET |
| **URL** | `{{ $env.GLPI_BASE_URL }}/initSession` |
| **Authentication** | None (usar headers) |
| **Send Headers** | ✅ Enabled |

**Headers:**

| Header | Value |
|--------|-------|
| `App-Token` | `{{ $env.GLPI_APP_TOKEN }}` |
| `Authorization` | `user_token {{ $env.GLPI_USER_TOKEN }}` |

**Expected Response:**

```json
{
  "session_token": "83af7e620c83a50a18d3eac2f6ed05a3ca0bea62"
}
```

**Armazenar:** Session token será usado nos próximos nodes via `{{ $('GLPI Auth').item.json.session_token }}`

---

#### 3. **Switch Action Node**

**Objetivo:** Rotear para ação correta

**Tipo:** `n8n-nodes-base.switch`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Mode** | Rules |
| **Value** | `={{ $json.action }}` |

**Rules:**

| Rule | Condition | Output Name |
|------|-----------|-------------|
| 1 | `action` equals `list_tickets` | List Tickets |
| 2 | `action` equals `get_ticket` | Get Ticket |
| 3 | `action` equals `create_ticket` | Create Ticket |
| Default | - | Error: Unknown Action |

---

#### 4. **GLPI List Tickets Node**

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | GET |
| **URL** | `={{ $env.GLPI_BASE_URL }}/Ticket?range=0-{{ $json.limit || 10 }}` |
| **Send Headers** | ✅ Enabled |

**Headers:**

| Header | Value |
|--------|-------|
| `Session-Token` | `={{ $('GLPI Auth').item.json.session_token }}` |
| `App-Token` | `={{ $env.GLPI_APP_TOKEN }}` |

**Expected Response:**

```json
[
  {
    "id": 1234,
    "name": "Servidor offline",
    "status": 2,
    "urgency": 5,
    "date_creation": "2026-02-04 10:00:00"
  }
]
```

---

#### 5. **GLPI Get Ticket Node**

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | GET |
| **URL** | `={{ $env.GLPI_BASE_URL }}/Ticket/{{ $json.ticket_id }}` |
| **Send Headers** | ✅ Enabled |

**Headers:** (iguais ao List Tickets)

**Expected Response:**

```json
{
  "id": 1234,
  "name": "Servidor offline",
  "content": "Servidor web01 não responde a ping",
  "status": 2,
  "urgency": 5,
  "priority": 5,
  "date_creation": "2026-02-04 10:00:00"
}
```

---

#### 6. **GLPI Create Ticket Node**

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | POST |
| **URL** | `={{ $env.GLPI_BASE_URL }}/Ticket` |
| **Send Headers** | ✅ Enabled |
| **Send Body** | ✅ Enabled |
| **Body Content Type** | JSON |

**Headers:**

| Header | Value |
|--------|-------|
| `Session-Token` | `={{ $('GLPI Auth').item.json.session_token }}` |
| `App-Token` | `={{ $env.GLPI_APP_TOKEN }}` |
| `Content-Type` | `application/json` |

**Body:**

```json
{
  "input": {
    "name": "={{ $json.title }}",
    "content": "={{ $json.description }}",
    "urgency": "={{ $json.urgency || 3 }}",
    "priority": "={{ $json.urgency || 3 }}"
  }
}
```

**Expected Response:**

```json
{
  "id": 1235,
  "message": "Ticket criado com sucesso"
}
```

---

#### 7. **GLPI Logout Node**

**Objetivo:** Finalizar sessão GLPI

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | GET |
| **URL** | `={{ $env.GLPI_BASE_URL }}/killSession` |
| **Send Headers** | ✅ Enabled |

**Headers:**

| Header | Value |
|--------|-------|
| `Session-Token` | `={{ $('GLPI Auth').item.json.session_token }}` |
| `App-Token` | `={{ $env.GLPI_APP_TOKEN }}` |

---

#### 8. **Error Handler Node** (Opcional)

**Tipo:** `n8n-nodes-base.set`

**Configuração:**

- Adicionar **Error Trigger** conectado a todos os nodes HTTP
- Formatar erro como JSON:

```json
{
  "status": "error",
  "message": "={{ $json.error.message }}",
  "action": "={{ $json.action }}",
  "timestamp": "={{ new Date().toISOString() }}"
}
```

---

### Conexões

```
Execute Workflow Trigger
  → GLPI Auth
    → Switch Action
      → [List Tickets]   → List Tickets Node   → GLPI Logout
      → [Get Ticket]     → Get Ticket Node     → GLPI Logout
      → [Create Ticket]  → Create Ticket Node  → GLPI Logout
      → [Default]        → Error Node
```

---

### Exportar JSON

**Após criar workflow no n8n UI:**

1. Clicar em **⋮** (menu) → **Download**
2. Salvar como: `docs/n8n/vsa-glpi-integration.json`
3. Commitar no repositório

---

## Sub-workflow: Zabbix Integration

### Estrutura do Workflow

**Nome:** `vsa-zabbix-integration`  
**Trigger:** Execute Workflow Trigger  
**Webhook:** `/webhook/vsa/zabbix`

### Nodes

#### 1. **Trigger Node**

**Input esperado:**

```json
{
  "action": "get_alerts",
  "limit": 10,
  "severity": 4
}
```

ou

```json
{
  "action": "get_host",
  "hostname": "web01"
}
```

---

#### 2. **Switch Action Node**

**Rules:**

| Action | Output |
|--------|--------|
| `get_alerts` | Get Alerts Branch |
| `get_host` | Get Host Branch |

---

#### 3. **Zabbix Get Alerts Node**

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | POST |
| **URL** | `={{ $env.ZABBIX_BASE_URL }}/api_jsonrpc.php` |
| **Send Headers** | ✅ Enabled |
| **Send Body** | ✅ Enabled |
| **Body Content Type** | JSON |

**Headers:**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

**Body (JSON-RPC):**

```json
{
  "jsonrpc": "2.0",
  "method": "problem.get",
  "params": {
    "output": "extend",
    "sortfield": "eventid",
    "sortorder": "DESC",
    "limit": "={{ $json.limit || 10 }}"
  },
  "auth": "={{ $env.ZABBIX_API_TOKEN }}",
  "id": 1
}
```

**Expected Response:**

```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "eventid": "12345",
      "name": "Server web01: High CPU usage",
      "severity": "4",
      "clock": "1707064800"
    }
  ],
  "id": 1
}
```

---

#### 4. **Zabbix Get Host Node**

**Body (JSON-RPC):**

```json
{
  "jsonrpc": "2.0",
  "method": "host.get",
  "params": {
    "output": "extend",
    "filter": {
      "host": ["={{ $json.hostname }}"]
    }
  },
  "auth": "={{ $env.ZABBIX_API_TOKEN }}",
  "id": 1
}
```

---

#### 5. **Format Response Node**

**Tipo:** `n8n-nodes-base.set`

**Objetivo:** Extrair apenas `result` do JSON-RPC

**Configuração:**

```javascript
// Code Node (JavaScript)
return {
  json: {
    data: $input.item.json.result,
    count: $input.item.json.result.length
  }
};
```

---

## Sub-workflow: Linear Integration

### Estrutura do Workflow

**Nome:** `vsa-linear-integration`  
**Trigger:** Execute Workflow Trigger  
**Webhook:** `/webhook/vsa/linear`

### Nodes

#### 1. **Trigger Node**

**Input esperado:**

```json
{
  "action": "list_issues",
  "team_key": "ENG",
  "limit": 10
}
```

---

#### 2. **Switch Action Node**

**Rules:**

| Action | Output |
|--------|--------|
| `list_issues` | List Issues |
| `get_issue` | Get Issue |
| `create_issue` | Create Issue |
| `get_teams` | Get Teams |

---

#### 3. **Linear List Issues Node**

**Tipo:** `n8n-nodes-base.httpRequest`

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Method** | POST |
| **URL** | `https://api.linear.app/graphql` |
| **Authentication** | Generic Credential |
| **Send Headers** | ✅ Enabled |
| **Send Body** | ✅ Enabled |
| **Body Content Type** | JSON |

**Headers:**

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer {{ $env.LINEAR_API_KEY }}` |
| `Content-Type` | `application/json` |

**Body (GraphQL):**

```json
{
  "query": "query { issues(first: {{ $json.limit || 10 }}, filter: { team: { key: { eq: \"{{ $json.team_key }}\" } } }) { nodes { id title state { name } priority createdAt } } }"
}
```

**Expected Response:**

```json
{
  "data": {
    "issues": {
      "nodes": [
        {
          "id": "abc-123",
          "title": "Fix login bug",
          "state": { "name": "In Progress" },
          "priority": 1
        }
      ]
    }
  }
}
```

---

#### 4. **Linear Create Issue Node**

**Body (GraphQL Mutation):**

```json
{
  "query": "mutation { issueCreate(input: { title: \"{{ $json.title }}\", description: \"{{ $json.description }}\", teamId: \"{{ $json.team_id }}\", priority: {{ $json.priority || 0 }} }) { success issue { id title } } }"
}
```

---

## Testes e Validação

### 1. Teste Manual no n8n UI

#### GLPI - List Tickets

1. Abrir workflow `vsa-glpi-integration`
2. Clicar em **Manual Trigger**
3. Clicar em **"Execute node"**
4. Inserir JSON de teste:

```json
{
  "action": "list_tickets",
  "limit": 3
}
```

5. Clicar em **"Execute Workflow"**
2. Verificar output em cada node

**Critérios de Sucesso:**

- ✅ GLPI Auth retorna `session_token`
- ✅ Switch router → "List Tickets"
- ✅ List Tickets retorna array de tickets
- ✅ Logout retorna sucesso

---

### 2. Teste via Webhook (curl)

#### GLPI - List Tickets

```bash
# Executar workflow via webhook
curl -X POST http://localhost:5678/webhook/vsa/glpi \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list_tickets",
    "limit": 5
  }'
```

**Expected Output:**

```json
{
  "tickets": [
    {
      "id": 1234,
      "name": "Servidor offline",
      "status": 2,
      "urgency": 5
    }
  ],
  "count": 5
}
```

---

#### GLPI - Create Ticket (Dry-Run)

```bash
curl -X POST http://localhost:5678/webhook/vsa/glpi \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_ticket",
    "title": "Teste n8n Workflow",
    "description": "Ticket criado via workflow n8n",
    "urgency": 3
  }'
```

**Expected Output:**

```json
{
  "id": 1245,
  "message": "Ticket criado com sucesso"
}
```

---

#### Zabbix - Get Alerts

```bash
curl -X POST http://localhost:5678/webhook/vsa/zabbix \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_alerts",
    "limit": 3
  }'
```

**Expected Output:**

```json
{
  "data": [
    {
      "eventid": "12345",
      "name": "Server web01: High CPU usage",
      "severity": "4"
    }
  ],
  "count": 3
}
```

---

#### Linear - List Issues

```bash
curl -X POST http://localhost:5678/webhook/vsa/linear \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list_issues",
    "team_key": "ENG",
    "limit": 5
  }'
```

---

### 3. Teste de Performance

**Objetivo:** Medir latência dos workflows

```bash
# Testar 10 requisições
for i in {1..10}; do
  time curl -X POST http://localhost:5678/webhook/vsa/glpi \
    -H "Content-Type: application/json" \
    -d '{"action":"list_tickets","limit":5}' \
    > /dev/null 2>&1
done
```

**Critério de Sucesso:**

- ✅ Latência média < 3s
- ✅ Todas as 10 requisições bem-sucedidas

---

## Troubleshooting

### 1. Erro: "401 Unauthorized" (GLPI)

**Causa:** Token inválido ou expirado

**Diagnóstico:**

```bash
# Testar token manualmente
curl -X GET https://glpi.hospitalevangelico.com.br/glpi/apirest.php/initSession \
  -H "App-Token: <APP_TOKEN>" \
  -H "Authorization: user_token <USER_TOKEN>"
```

**Solução:**

1. Regenerar User Token no GLPI
2. Atualizar `.env.n8n`
3. Reiniciar n8n: `docker compose -f docker-compose.n8n.yml restart`

---

### 2. Erro: "Session token not found" (GLPI)

**Causa:** Node GLPI Auth falhou antes do Switch

**Diagnóstico:**

- Ver execução no n8n UI
- Verificar se GLPI Auth node executou com sucesso

**Solução:**

- Verificar que Switch Action está conectado APÓS GLPI Auth (não diretamente ao Trigger)

---

### 3. Workflow muito lento (> 5s)

**Causa:** Overhead de múltiplas requisições HTTP

**Otimização:**

1. Habilitar cache:

   ```yaml
   # docker-compose.n8n.yml
   environment:
     - N8N_CACHE_ENABLED=true
   ```

2. Paralelizar requisições (se possível):
   - Usar **Split In Batches** node para processar múltiplos tickets

---

## Checklist de Conclusão

### GLPI Integration

- [ ] Workflow `vsa-glpi-integration` criado
- [ ] Ações implementadas: `list_tickets`, `get_ticket`, `create_ticket`
- [ ] Auth/Logout funcionando
- [ ] Teste manual no n8n UI: ✅
- [ ] Teste via webhook (curl): ✅
- [ ] Latência < 3s: ✅
- [ ] JSON exportado: `docs/n8n/vsa-glpi-integration.json`

### Zabbix Integration

- [ ] Workflow `vsa-zabbix-integration` criado
- [ ] Ações implementadas: `get_alerts`, `get_host`
- [ ] JSON-RPC funcionando
- [ ] Teste manual no n8n UI: ✅
- [ ] Teste via webhook (curl): ✅
- [ ] JSON exportado: `docs/n8n/vsa-zabbix-integration.json`

### Linear Integration

- [ ] Workflow `vsa-linear-integration` criado
- [ ] Ações implementadas: `list_issues`, `get_issue`, `create_issue`, `get_teams`
- [ ] GraphQL queries funcionando
- [ ] Teste manual no n8n UI: ✅
- [ ] Teste via webhook (curl): ✅
- [ ] JSON exportado: `docs/n8n/vsa-linear-integration.json`

---

**Próximo:** Fase 2 - RAG Pipeline (`n8n-workflows-fase2.md`)

---

**Data:** 04/02/2026  
**Versão:** 1.0  
**Autor:** DeepCode VSA Team
