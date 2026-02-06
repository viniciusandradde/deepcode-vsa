# CLAUDE.md - DeepCode VSA

## Leitura Obrigatoria (antes de qualquer codigo)

1. `.ai/context.md` - Visao geral do projeto DeepCode VSA
2. `.ai/progress.md` - Ultimas sessoes de desenvolvimento
3. `.ai/handoff.md` - Trabalho pendente e proximos passos
4. `.agent/skills/<skill>/SKILL.md` - Skill de desenvolvimento relevante
5. `.ai/skills/<skill>/SKILL.md` - Skill hospital-especifica (se aplicavel)

## Ao Finalizar a Sessao

1. Atualizar `.ai/progress.md` com template (no topo)
2. Se trabalho incompleto -> atualizar `.ai/handoff.md`
3. Se mudou arquitetura -> atualizar `.ai/context.md`
4. Commit: `[workstream] tipo: descricao`
   - Co-Authored-By: Claude <noreply@anthropic.com>

## Stack do Projeto

- **Backend:** FastAPI + Python 3.11+ (porta 8000)
- **Frontend:** Next.js 15 + React 19 (porta 3000)
- **Agente:** UnifiedAgent via LangGraph (`core/agents/unified.py`)
- **Integracoes:** GLPI (REST), Zabbix (JSON-RPC), Linear (GraphQL)
- **LLM:** Multi-model via OpenRouter (4 tiers)
- **DB:** PostgreSQL 16 + pgvector
- **RAG:** Hybrid search + HyDE + RRF

## Regras de Codigo

- Python 3.11+, async/await quando I/O
- Type hints obrigatorios em funcoes publicas
- `dry_run=True` por padrao em WRITE operations
- Import config via `core.config.get_settings()`
- LangGraph state deve ser TypedDict
- LGPD: mascarar dados sensiveis em logs

## Entry Points

- `api/main.py` - FastAPI app
- `core/agents/unified.py` - Agente principal
- `frontend/src/components/app/ChatPane.tsx` - Chat interface
- `Makefile` - Comandos de desenvolvimento

## Comandos

```bash
make dev          # FastAPI porta 8000
make frontend     # Next.js porta 3000
make test         # pytest
make studio       # LangGraph Studio
```

## Nao Fazer

- Nao instalar deps sem justificativa
- Nao modificar configs de outras IDEs em `.ai/ide-configs/`
- Nao fazer push sem confirmacao do usuario
- Nao expor credenciais em codigo
