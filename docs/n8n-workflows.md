# Workflows n8n para DeepCode VSA

Este documento descreve os workflows n8n que espelham a estrutura da API VSA (chat, agentes, threads, planning, RAG) e como invocá-los via MCP **user-n8n-mcp**.

## Pré-requisitos

1. **n8n** em execução com acesso à API VSA (FastAPI).
2. **Variável de ambiente no n8n:** `VSA_API_URL` (ex.: `http://localhost:8000` ou URL do deploy). Ver seção [Configuração n8n](#configuração-n8n-vsa_api_url) abaixo.
3. Workflows importados a partir dos JSON em **[docs/n8n/](n8n/)** (ou criados manualmente conforme esta doc):
   - `vsa-chat.json` – Chat síncrono
   - `vsa-agent-invoke.json` – Invocar agente
   - `vsa-threads-list.json` – Listar threads
   - `vsa-thread-get.json` – Obter thread por ID
   - `vsa-planning.json` – Planning (list/get/create/analyze/sync_linear)
   - `vsa-rag-search.json` – Busca RAG

## Acesso via MCP

1. **Buscar workflows:** `search_workflows(query="VSA", limit=20)`
2. **Detalhes de um workflow:** `get_workflow_details(workflowId)` (para ver descrição e schema de input)
3. **Executar:** `execute_workflow(workflowId, inputs)` com `type: "chat"` + `chatInput` ou `type: "form"` + `formData`

---

## 1. VSA Chat

**Descrição:** Chama `POST /api/v1/chat` da API VSA. Entrada: mensagem do usuário; opcionais: thread_id, model, flags de integração.

**Trigger MCP:** input tipo **chat**.

### Exemplo execute_workflow (chat)

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_CHAT>",
  "inputs": {
    "type": "chat",
    "chatInput": "Liste os últimos 5 tickets do GLPI"
  }
}
```

### Exemplo com formData (se o workflow aceitar form)

Se o workflow for configurado para receber **form** em vez de chat, use:

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_CHAT>",
  "inputs": {
    "type": "form",
    "formData": {
      "message": "Liste os últimos 5 tickets do GLPI",
      "thread_id": "thread_abc123",
      "model": null,
      "enable_vsa": true,
      "enable_glpi": true,
      "enable_zabbix": false,
      "enable_linear": false,
      "enable_planning": false,
      "use_tavily": false,
      "dry_run": true
    }
  }
}
```

**Campos do body da API VSA (referência):** `message` (obrigatório), `thread_id`, `model`, `empresa`, `client_id`, `use_tavily`, `enable_vsa`, `enable_glpi`, `enable_zabbix`, `enable_linear`, `enable_planning`, `dry_run`.

**Resposta esperada:** `{ "response": "...", "thread_id": "...", "model": "..." }`

---

## 2. VSA Agent Invoke

**Descrição:** Chama `POST /api/v1/agents/{agent_id}/invoke`. Agentes: `simple`, `unified`, `vsa`.

**Trigger MCP:** input tipo **form**.

### Exemplo execute_workflow

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_AGENT_INVOKE>",
  "inputs": {
    "type": "form",
    "formData": {
      "agent_id": "unified",
      "input": {
        "messages": [
          { "role": "user", "content": "Classifique: servidor de e-mail fora do ar" }
        ]
      },
      "config": {}
    }
  }
}
```

**Campos formData:** `agent_id` (obrigatório: simple | unified | vsa), `input` (obrigatório: objeto com estrutura do agente, ex. `messages`), `config` (opcional).

**Resposta esperada:** `{ "output": {...}, "agent_id": "unified" }`

---

## 3. VSA Threads List

**Descrição:** Chama `GET /api/v1/threads`. Lista threads disponíveis (checkpoints).

**Trigger MCP:** input tipo **form**. formData pode ser vazio ou com `limit`, `cursor` se a API suportar no futuro.

### Exemplo execute_workflow

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_THREADS_LIST>",
  "inputs": {
    "type": "form",
    "formData": {}
  }
}
```

**Resposta esperada:** `{ "threads": [ { "thread_id": "...", "last_ts": "..." } ], ... }`

---

## 4. VSA Thread Get

**Descrição:** Chama `GET /api/v1/threads/{thread_id}`. Retorna histórico de mensagens da thread.

**Trigger MCP:** input tipo **form**.

### Exemplo execute_workflow

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_THREAD_GET>",
  "inputs": {
    "type": "form",
    "formData": {
      "thread_id": "thread_abc123"
    }
  }
}
```

**Campos formData:** `thread_id` (obrigatório).

**Resposta esperada:** `{ "thread_id": "...", "messages": [ { "id", "role", "content" } ] }`

---

## 5. VSA Planning

**Descrição:** Orquestra chamadas à API de planning (`/api/v1/planning/...`). Ações: list_projects, get_project, create_project, analyze, sync_linear, etc.

**Trigger MCP:** input tipo **form**.

### Exemplo execute_workflow (listar projetos)

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_PLANNING>",
  "inputs": {
    "type": "form",
    "formData": {
      "action": "list_projects",
      "payload": {
        "status": null,
        "empresa": null,
        "limit": 50,
        "offset": 0
      }
    }
  }
}
```

### Exemplo (obter projeto)

```json
{
  "type": "form",
  "formData": {
    "action": "get_project",
    "payload": { "project_id": "uuid-do-projeto" }
  }
}
```

### Exemplo (criar projeto)

```json
{
  "type": "form",
  "formData": {
    "action": "create_project",
    "payload": {
      "title": "Projeto X",
      "description": "Descrição",
      "empresa": null,
      "client_id": null
    }
  }
}
```

### Exemplo (analisar documentos)

```json
{
  "type": "form",
  "formData": {
    "action": "analyze",
    "payload": { "project_id": "uuid-do-projeto" }
  }
}
```

### Exemplo (sync Linear)

```json
{
  "type": "form",
  "formData": {
    "action": "sync_linear",
    "payload": { "project_id": "uuid-do-projeto" }
  }
}
```

**formData:** `action` (obrigatório), `payload` (objeto conforme a ação). O workflow n8n deve fazer switch por `action` e chamar o endpoint correspondente (GET/POST/PUT) com o payload.

---

## 6. VSA RAG Search

**Descrição:** Chama `POST /api/v1/rag/search`. Busca na base de conhecimento.

**Trigger MCP:** input tipo **form**.

### Exemplo execute_workflow

```json
{
  "workflowId": "<ID_DO_WORKFLOW_VSA_RAG_SEARCH>",
  "inputs": {
    "type": "form",
    "formData": {
      "query": "Como configurar GLPI?",
      "k": 5,
      "search_type": "hybrid",
      "reranker": "none",
      "empresa": null,
      "client_id": null,
      "use_hyde": false
    }
  }
}
```

**Campos formData (referência API):** `query` (obrigatório), `k`, `search_type`, `reranker`, `empresa`, `client_id`, `chunking`, `use_hyde`, `match_threshold`.

**Resposta esperada:** `{ "results": [...], "query": "...", "total": N }`

---

## Resumo: IDs e nomes para search_workflows

| Nome do workflow (no n8n) | Descrição sugerida | Tipo de input MCP |
|---------------------------|--------------------|-------------------|
| VSA Chat | Chat síncrono com a API VSA (POST /api/v1/chat). Input: chatInput ou formData.message. | chat ou form |
| VSA Agent Invoke | Invoca agente (simple/unified/vsa) via POST /api/v1/agents/{id}/invoke. | form |
| VSA Threads List | Lista threads (GET /api/v1/threads). | form |
| VSA Thread Get | Obtém mensagens de uma thread (GET /api/v1/threads/{id}). formData: thread_id. | form |
| VSA Planning | CRUD e ações de planning (list/get/create/analyze/sync_linear). formData: action, payload. | form |
| VSA RAG Search | Busca na base de conhecimento (POST /api/v1/rag/search). formData: query, k, etc. | form |

Após criar os workflows no n8n, use `search_workflows(query="VSA", limit=20)` para obter os IDs e preencher os exemplos acima com os `workflowId` reais.

---

## Configuração n8n (VSA_API_URL)

Os workflows em `docs/n8n/` chamam a API VSA usando a variável `VSA_API_URL`. Configure-a no ambiente onde o n8n roda.

### No n8n

- **Settings > Variables** (ou variáveis de ambiente do container/processo do n8n).
- Defina `VSA_API_URL` com a URL base da API VSA, por exemplo:
  - API no mesmo host: `http://localhost:8000`
  - n8n em Docker e API no host: `http://host.docker.internal:8000` (Linux/Mac: use o IP do host ou `host.docker.internal` se disponível)
  - API em outro serviço Docker na mesma rede: `http://backend:8000` (nome do serviço do docker-compose)
- Nos nodes HTTP Request dos workflows, a URL usa `{{ $env.VSA_API_URL || 'http://localhost:8000' }}`; o fallback localhost serve para testes sem variável definida.

### No projeto (DeepCode VSA)

- A API VSA sobe por padrão na **porta 8000** (`make dev` ou `uvicorn api.main:app --port 8000`).
- Se você rodar o n8n em outro host ou container, garanta que ele consiga acessar essa URL (rede, firewall, CORS se for o caso).
- Não é necessário definir `VSA_API_URL` no `.env` do próprio projeto VSA; essa variável é usada **apenas pelo n8n** ao executar os workflows.

Se a API VSA exigir API key ou header de autenticação no futuro, configure no n8n em cada HTTP Request (Header) ou em Credentials.
