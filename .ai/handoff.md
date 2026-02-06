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

### O que esta pendente

- [ ] GLPI User Token - falta token valido para completar integracao
- [ ] VSAAgent nao integrado ao chat (existe em `core/agents/vsa.py`)
- [ ] Correlacao automatica GLPI <-> Zabbix (planejada, nao implementada)
- [ ] GUT score calculation no fluxo de chat
- [ ] CLI interface (adiada para v2.0)
- [ ] Feedback visual de tool calls no frontend
- [ ] Audit dashboard no frontend
- [ ] Testes de integracao com APIs reais (GLPI, Zabbix)

### Proximos Passos (por prioridade)

1. **Obter GLPI User Token**
   - Acessar: https://glpi.hospitalevangelico.com.br
   - Login -> Meu Perfil -> Configuracoes Remotas -> Tokens de API
   - Adicionar ao `.env` como `GLPI_USER_TOKEN`

2. **Integrar VSAAgent ao chat**
   - `core/agents/vsa.py` tem o pipeline completo (Classifier -> Planner -> Executor -> Reflector -> Integrator)
   - Precisa substituir ou ser opcao ao lado do UnifiedAgent
   - Ver `docs/INTEGRACAO-METODOLOGIAS-CHAT.md`

3. **Feedback visual de tool calls**
   - Frontend precisa mostrar quando o agente esta chamando GLPI/Zabbix/Linear
   - Componente ja parcial em `StructuredResponse.tsx` e `ITILBadge.tsx`

4. **Testes de integracao**
   - `tests/integration/` precisa de testes com APIs reais
   - Zabbix e Linear ja tem credenciais validas

### Contexto Importante

- O pivot de CLI-First para Chat-First aconteceu em Jan 2026 (ver `docs/PRD-REVISADO.md`)
- Frontend e backend rodam em portas separadas (3000 e 8000)
- Next.js proxy rewrite encaminha `/api/v1/*` para o FastAPI
- `dry_run=True` por padrao em TODAS as operacoes WRITE
- LangSmith tracing habilitado se `LANGCHAIN_API_KEY` estiver setada

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
