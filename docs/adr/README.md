# Architecture Decision Records (ADR)

Este diretório contém os registros de decisões de arquitetura do DeepCode VSA.

## O que é um ADR?

Um Architecture Decision Record (ADR) é um documento que captura uma decisão de arquitetura importante junto com seu contexto e consequências.

## Índice de ADRs

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-001](./ADR-001-cli-local.md) | Tipo de Aplicação: CLI Local | Aprovado | Jan 2026 |
| [ADR-002](./ADR-002-python.md) | Linguagem: Python | Aprovado | Jan 2026 |
| [ADR-003](./ADR-003-agente-inteligente.md) | Arquitetura de Agente Inteligente | Aprovado | Jan 2026 |
| [ADR-004](./ADR-004-langgraph.md) | Orquestração: LangGraph | Aprovado | Jan 2026 |
| [ADR-005](./ADR-005-api-first.md) | Arquitetura API-First | Aprovado | Jan 2026 |
| [ADR-006](./ADR-006-api-registry.md) | API Tool Registry Dinâmico | Aprovado | Jan 2026 |
| [ADR-007](./ADR-007-governanca.md) | Execução Segura (Governança) | Aprovado | Jan 2026 |
| [ADR-008](./ADR-008-openrouter.md) | LLM via OpenRouter | Aprovado | Jan 2026 |
| [ADR-009](./ADR-009-foco-diagnostico.md) | Foco Inicial em Diagnóstico | Aprovado | Jan 2026 |

## Status Possíveis

- **Proposto**: Decisão em discussão
- **Aprovado**: Decisão aceita e em vigor
- **Deprecado**: Decisão substituída por outra
- **Rejeitado**: Decisão não aceita

## Template para Novos ADRs

```markdown
# ADR-XXX: Título

## Status
Proposto | Aprovado | Deprecado | Rejeitado

## Contexto
Qual é o problema ou situação que motivou esta decisão?

## Decisão
Qual é a decisão tomada?

## Justificativa
Por que esta decisão foi tomada?

## Consequências
### Positivas
- ...

### Negativas
- ...

## Alternativas Consideradas
- Alternativa 1: ...
- Alternativa 2: ...
```
