# OpenCode Instructions - DeepCode VSA

## Contexto

DeepCode VSA: agente virtual inteligente para gestao de TI.
Leia `.ai/context.md` para visao completa.

## Leitura Obrigatoria

1. `.ai/context.md`
2. `.ai/progress.md`
3. `.ai/handoff.md`

## Foco

- Bug fixes pontuais
- Code review automatizado
- Refatoracao de seguranca
- Linting e padronizacao (ruff check, ruff format)
- Documentacao inline

## Regras

- Seguir padroes ja estabelecidos no projeto
- LGPD: verificar se dados sensiveis estao mascarados
- Nao alterar arquitetura sem documentar em progress.md
- `dry_run=True` por padrao em WRITE operations
- Manter backward compatibility

## Commit: `[workstream] tipo: descricao`

## Ao Finalizar

- Atualizar `.ai/progress.md`
- Se encontrou vulnerabilidade -> registrar em handoff.md
