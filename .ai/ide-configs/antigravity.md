# Antigravity (Gemini) - DeepCode VSA

## Status: Cidadao Nativo

Antigravity ja usa `.agent/` como estrutura primaria.
Este arquivo existe apenas como referencia para o protocolo multi-IDE.

## Arquivos de Contexto Nativos

- `.agent/rules/GEMINI.md` - Master config (Tier 0/1/2, routing, checklist)
- `.agent/agents/*.md` - 21 agent definitions
- `.agent/skills/*/SKILL.md` - 40 skills
- `.agent/workflows/*.md` - 12 workflows

## Leitura Adicional (Multi-IDE)

1. `.ai/context.md` - Contexto compartilhado do projeto
2. `.ai/progress.md` - Sessoes de todas as IDEs
3. `.ai/handoff.md` - Pendencias cross-IDE

## Persistencia

- `brain/` - Contexto entre sessoes (protobuf)
- `code_tracker/` - Monitoramento de mudancas em arquivos
- `context_state/` - Estado implicito da conversa
- `mcp_config.json` - Acesso a DBs e APIs externas

## Protocolo de Sessao

### Inicio
1. `GEMINI.md` ja e lido automaticamente (trigger: always_on)
2. Ler `.ai/context.md` e `.ai/progress.md` para contexto multi-IDE
3. Agent routing conforme `.agent/rules/GEMINI.md` secao INTELLIGENT AGENT ROUTING

### Fim
1. Atualizar `.ai/progress.md`
2. Se incompleto -> `.ai/handoff.md`
3. Commit: `[workstream] tipo: descricao`

## Nao Fazer

- Nao modificar `.agent/rules/GEMINI.md` sem revisar impacto nos 21 agents
- Nao sobrescrever configs de outras IDEs em `.ai/ide-configs/`
