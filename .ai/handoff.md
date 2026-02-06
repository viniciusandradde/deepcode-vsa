# Handoff - Passagem de Bastao entre IDEs

> Atualizado quando uma sessao termina com trabalho incompleto.
> A proxima IDE/sessao DEVE ler este arquivo antes de iniciar.

---

## Status Atual

**De:** Claude Code
**Data:** 2026-02-06
**Para:** Proxima IDE (qualquer)

### O que esta funcionando

- [x] Chat web (Next.js 15 + React 19) com streaming SSE
- [x] FastAPI backend com endpoints: chat, rag, agents, planning, automation, threads
- [x] UnifiedAgent (Router-Classifier-Planner-Executor) via LangGraph
- [x] Integracao Zabbix (JSON-RPC) - validada e funcional
- [x] Integracao Linear (GraphQL) - validada e funcional
- [x] Tools LangChain: GLPI, Zabbix, Linear, Planning, Search
- [x] RAG Pipeline: ingestion, hybrid search, HyDE, pgvector
- [x] Planning module: projetos, documentos, analise IA, sync Linear
- [x] Automation Scheduler: APScheduler + Celery, CRON, UI frontend
- [x] PostgreSQL 16 + pgvector com 9 schemas SQL
- [x] Multi-model LLM via OpenRouter (4 tiers)
- [x] Estrutura `.ai/` atualizada para projeto real (v2.0)
- [x] Estrutura `.agent/` com 40 skills, 21 agents, 12 workflows
- [x] Frontend state refatorado: monolito (1239 linhas) -> 3 domain contexts + facade

### O que esta pendente

### Proximos Passos (por prioridade)

### Arquivos Chave

- `.ai/context.md` - Contexto do projeto (ler primeiro!)
- `core/agents/unified.py` - Agente principal em uso
- `api/routes/chat.py` - Endpoints de chat
- `frontend/src/components/app/ChatPane.tsx` - Interface principal
- `CLAUDE.md` - Instrucoes completas do projeto

---

<!-- TEMPLATE DE HANDOFF (substituir conteudo acima ao atualizar)

## Status Atual

**De:** [IDE que esta finalizando]
**Data:** YYYY-MM-DD
**Para:** [IDE seguinte ou "Qualquer"]

### O que esta funcionando
- [x] Item 1

### O que esta pendente
- [ ] Item 1

### Proximos Passos
1. ...

### Contexto Importante
- ...

### Arquivos Chave
- ...
-->
