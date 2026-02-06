# Codex Instructions - DeepCode VSA

## Contexto

DeepCode VSA: agente virtual inteligente para gestao de TI.
Interface Chat-First (Next.js 15 + FastAPI). Integracoes: GLPI, Zabbix, Linear.
Leia `.ai/context.md` para detalhes completos.

## Leitura Obrigatoria

1. `.ai/context.md` - Contexto do projeto
2. `.ai/progress.md` - Ultimas sessoes
3. `.ai/handoff.md` - Pendencias
4. `.agent/skills/<skill>/SKILL.md` - Skill relevante

## Foco

- Algoritmos de ML e classificacao
- Otimizacao de queries SQL (pgvector, hybrid search)
- Logica de priorizacao GUT (Gravidade, Urgencia, Tendencia)
- Classificacao ITIL automatica
- Processamento de dados para RAG pipeline

## Regras

- Python 3.11+, type hints obrigatorios
- Queries parametrizadas (nunca concatenar SQL)
- LGPD: mascarar dados sensiveis em outputs
- Testes unitarios para algoritmos
- Documentar metricas de acuracia

## Commit: `[workstream] tipo: descricao`

## Ao Finalizar

- Atualizar `.ai/progress.md`
- Se mudou algoritmo -> documentar metricas em progress.md
