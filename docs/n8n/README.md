# Workflows n8n – DeepCode VSA

JSONs para importação no n8n. Cada workflow chama a API VSA (FastAPI). Configure `VSA_API_URL` no n8n antes de executar.

| Arquivo | Nome do workflow | Descrição |
|--------|-------------------|-----------|
| vsa-chat.json | VSA Chat | POST /api/v1/chat. Input: chat (chatInput) ou form (message, thread_id, enable_*). |
| vsa-agent-invoke.json | VSA Agent Invoke | POST /api/v1/agents/{id}/invoke. formData: agent_id, input, config. |
| vsa-threads-list.json | VSA Threads List | GET /api/v1/threads. |
| vsa-thread-get.json | VSA Thread Get | GET /api/v1/threads/{id}. formData: thread_id. |
| vsa-planning.json | VSA Planning | Switch por action: list_projects, get_project, create_project, analyze, sync_linear. formData: action, payload. |
| vsa-rag-search.json | VSA RAG Search | POST /api/v1/rag/search. formData: query, k, search_type, etc. |

**Importar:** No n8n, menu (três pontos) > Import from File > selecione o JSON. Ajuste a URL base nos nodes HTTP se não usar variável `VSA_API_URL`.

Ver [docs/n8n-workflows.md](../n8n-workflows.md) para exemplos de `execute_workflow` via MCP e configuração.
