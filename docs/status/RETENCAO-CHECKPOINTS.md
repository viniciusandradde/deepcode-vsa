# Política de Retenção de Checkpoints do LangGraph

Este documento descreve como o DeepCode VSA gerencia o crescimento das tabelas
de checkpoint do LangGraph no PostgreSQL (`checkpoints` e `checkpoint_writes`).

## Objetivo

- Manter o histórico de conversas necessário para auditoria e explicabilidade.
- Evitar crescimento infinito das tabelas técnicas de checkpoint.
- Permitir limpeza controlada e segura de dados antigos.

## Estrutura Técnica

O LangGraph (`PostgresSaver` / `AsyncPostgresSaver`) utiliza duas tabelas:

- `checkpoints`
  - Um registro consolidado por checkpoint (estado do grafo).
  - Campo `checkpoint->>'ts'` armazena o timestamp ISO da última atualização.
- `checkpoint_writes`
  - Registros detalhados por canal (`messages`, `__error__`, etc.), em formato binário.

O carregamento de sessões e mensagens no chat usa o endpoint:

- `GET /api/v1/threads` → lista threads a partir de `checkpoints`.
- `GET /api/v1/threads/{thread_id}` → reconstrói as mensagens do último checkpoint.

## Retenção Padrão

- **Idade máxima**: 180 dias sem atividade.
- **Critério**: o último checkpoint de uma `thread_id` cujo
  `checkpoint->>'ts'` seja mais antigo que `NOW() - INTERVAL '180 days'`.
- **Escopo de remoção**:
  - Todas as linhas de `checkpoint_writes` para essas `thread_id`.
  - Todas as linhas de `checkpoints` para essas `thread_id`.

Esta política considera que:

- A auditoria de negócio (GLPI, Zabbix, etc.) é a fonte oficial.
- Os checkpoints são artefatos técnicos usados para estado do agente.

## Script de Limpeza

O script de manutenção fica em:

- `scripts/cleanup_checkpoints.py`

### Uso básico

Dry-run (não apaga, apenas mostra candidatos):

```bash
cd /home/projects/agentes-ai/deepcode-vsa
python scripts/cleanup_checkpoints.py --days 180 --dry-run
```

Execução real (apaga dados antigos):

```bash
cd /home/projects/agentes-ai/deepcode-vsa
python scripts/cleanup_checkpoints.py --days 180
```

Parâmetros:

- `--days` (opcional): número de dias de inatividade. Padrão: `180`.
- `--dry-run`: se presente, **não executa DELETE**, apenas mostra:
  - Quantidade de threads candidatas.
  - Amostra de até 10 `thread_id` antigos.

### O que o script faz

1. Conecta ao PostgreSQL usando `core.database.get_conn()`.
2. Identifica threads antigas:

   ```sql
   SELECT DISTINCT thread_id
   FROM checkpoints
   WHERE (checkpoint->>'ts')::timestamptz < (NOW() - INTERVAL '180 days');
   ```

3. Em modo não-dry-run, executa:

   ```sql
   WITH old_threads AS (
     SELECT DISTINCT thread_id
     FROM checkpoints
     WHERE (checkpoint->>'ts')::timestamptz < (NOW() - (%s || ' days')::interval)
   )
   DELETE FROM checkpoint_writes
   WHERE thread_id IN (SELECT thread_id FROM old_threads);

   WITH old_threads AS (
     SELECT DISTINCT thread_id
     FROM checkpoints
     WHERE (checkpoint->>'ts')::timestamptz < (NOW() - (%s || ' days')::interval)
   )
   DELETE FROM checkpoints
   WHERE thread_id IN (SELECT thread_id FROM old_threads);
   ```

4. Loga no stdout:
   - Quantidade de threads candidatas.
   - Linhas removidas em `checkpoint_writes`.
   - Linhas removidas em `checkpoints`.

## Recomendações Operacionais

- Executar o script **manual ou via cron**, por exemplo:

  ```bash
  # Cron mensal às 03h00
  0 3 1 * * cd /home/projects/agentes-ai/deepcode-vsa && python scripts/cleanup_checkpoints.py --days 180 >> /var/log/cleanup_checkpoints.log 2>&1
  ```

- Antes da primeira execução em produção:
  - Rodar com `--dry-run` e revisar os `thread_id` e contagens.
  - Garantir que não há dependência externa desses dados.

- O script **não é chamado automaticamente** pelo FastAPI:
  - Não há side-effects no startup.
  - Toda limpeza é explícita e controlada.

