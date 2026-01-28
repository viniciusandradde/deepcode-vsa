# Guia de Teste - Persistência PostgreSQL

**Status:** ✅ Checkpointer corrigido e pronto para uso
**Pendência:** Atualizar chave da API OpenRouter válida

---

## 🎯 Pré-requisito

### Atualizar Chave da API OpenRouter

1. **Obter chave válida:**
   - Acesse: https://openrouter.ai/keys
   - Crie ou copie uma chave API válida
   - Verifique se há créditos disponíveis

2. **Atualizar .env:**
   ```bash
   # Editar arquivo
   nano .env

   # Substituir linha:
   OPENROUTER_API_KEY=sk-or-v1-your-valid-key-here
   ```

3. **Reiniciar backend:**
   ```bash
   docker compose restart backend
   ```

---

## 🧪 Teste 1: Verificar Inicialização

**Objetivo:** Confirmar que checkpointer foi inicializado com `dict_row factory`

```bash
docker compose logs backend --tail 20 | grep -E "PostgresSaver|dict_row|initialized"
```

**Saída Esperada:**
```
✅ Sync PostgresSaver initialized with dict_row factory
✅ Async PostgresSaver initialized with dict_row factory
✅ PostgreSQL Checkpointers (Sync & Async) initialized
```

---

## 🧪 Teste 2: Enviar Primeira Mensagem

**Objetivo:** Criar um novo checkpoint no banco de dados

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá! Este é um teste de persistência PostgreSQL.",
    "thread_id": "test-persistence-001"
  }'
```

**Saída Esperada:**
```json
{
  "response": "Olá! Como posso ajudá-lo hoje?",
  "thread_id": "test-persistence-001",
  "model": "google/gemini-2.5-flash"
}
```

---

## 🧪 Teste 3: Verificar Checkpoint no Banco

**Objetivo:** Confirmar que checkpoint foi salvo no PostgreSQL

```bash
docker exec ai_agent_postgres psql -U postgres -d deepcode_vsa -c "
SELECT
    thread_id,
    checkpoint_id,
    created_at,
    (checkpoint->'channel_values'->'messages')::jsonb AS messages
FROM checkpoints
WHERE thread_id = 'test-persistence-001'
ORDER BY created_at DESC
LIMIT 1;
"
```

**Saída Esperada:**
```
 thread_id             | checkpoint_id | created_at           | messages
-----------------------|---------------|----------------------|---------
 test-persistence-001  | xxx-xxx-xxx   | 2026-01-28 12:45:00  | [...]
(1 row)
```

Se retornar **0 rows**, significa que o checkpoint NÃO foi salvo (verificar logs de erro).

---

## 🧪 Teste 4: Continuar Conversa (Recuperação de Contexto)

**Objetivo:** Verificar se o agente recupera o contexto da conversa anterior

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Você consegue lembrar da minha mensagem anterior?",
    "thread_id": "test-persistence-001"
  }'
```

**Saída Esperada:**
A resposta deve mencionar a mensagem anterior ("teste de persistência PostgreSQL") ou demonstrar continuidade contextual.

---

## 🧪 Teste 5: Reiniciar Backend e Verificar Persistência

**Objetivo:** Confirmar que checkpoints sobrevivem a reinicializações

```bash
# 1. Reiniciar backend
docker compose restart backend

# 2. Aguardar inicialização (3-5 segundos)
sleep 5

# 3. Continuar conversa
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Após reiniciar, você ainda lembra do contexto?",
    "thread_id": "test-persistence-001"
  }'
```

**Saída Esperada:**
Agente demonstra continuidade do contexto anterior mesmo após reinicialização.

---

## 🧪 Teste 6: Verificar Quantidade de Checkpoints

**Objetivo:** Confirmar que múltiplos checkpoints são salvos

```bash
docker exec ai_agent_postgres psql -U postgres -d deepcode_vsa -c "
SELECT
    thread_id,
    COUNT(*) as total_checkpoints,
    MIN(created_at) as first_checkpoint,
    MAX(created_at) as last_checkpoint
FROM checkpoints
WHERE thread_id = 'test-persistence-001'
GROUP BY thread_id;
"
```

**Saída Esperada:**
```
 thread_id             | total_checkpoints | first_checkpoint     | last_checkpoint
-----------------------|-------------------|----------------------|--------------------
 test-persistence-001  | 6                 | 2026-01-28 12:45:00  | 2026-01-28 12:50:00
(1 row)
```

---

## 🧪 Teste 7: Streaming Endpoint

**Objetivo:** Verificar se checkpointer funciona com endpoint `/stream`

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Teste de streaming com persistência",
    "thread_id": "test-stream-001"
  }'
```

**Saída Esperada:**
Respostas em streaming (SSE) com checkpoints salvos no banco.

---

## 🧪 Teste 8: Modo VSA com ITIL

**Objetivo:** Verificar persistência com UnifiedAgent (VSA mode)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Liste os últimos tickets do GLPI",
    "thread_id": "test-vsa-001",
    "enable_vsa": true,
    "enable_glpi": true
  }'
```

**Saída Esperada:**
- Classificação ITIL em tabela markdown
- Checkpoints salvos no banco

---

## 🔍 Comandos de Diagnóstico

### Ver Todos os Checkpoints

```sql
docker exec ai_agent_postgres psql -U postgres -d deepcode_vsa -c "
SELECT
    thread_id,
    COUNT(*) as total,
    MIN(created_at) as first_msg,
    MAX(created_at) as last_msg
FROM checkpoints
GROUP BY thread_id
ORDER BY last_msg DESC;
"
```

### Ver Conteúdo de Checkpoint

```sql
docker exec ai_agent_postgres psql -U postgres -d deepcode_vsa -c "
SELECT
    checkpoint_id,
    jsonb_pretty(checkpoint->'channel_values'->'messages') as messages
FROM checkpoints
WHERE thread_id = 'test-persistence-001'
ORDER BY created_at DESC
LIMIT 1;
"
```

### Limpar Checkpoints de Teste

```sql
docker exec ai_agent_postgres psql -U postgres -d deepcode_vsa -c "
DELETE FROM checkpoints WHERE thread_id LIKE 'test-%';
"
```

---

## ⚠️ Troubleshooting

### Problema: Checkpoints não são salvos

**Verificar:**

1. Logs do backend:
   ```bash
   docker compose logs backend --tail 50 | grep -i error
   ```

2. Tabelas existem:
   ```bash
   docker exec ai_agent_postgres psql -U postgres -d deepcode_vsa -c "\dt"
   ```

3. Checkpointer foi inicializado:
   ```bash
   docker compose logs backend | grep "PostgresSaver initialized"
   ```

### Problema: `NotImplementedError`

**Causa:** Usando checkpointer sync em contexto async

**Solução:** Já foi corrigido. Verificar se está usando `get_async_checkpointer()`:
```bash
grep -n "get_checkpointer\|get_async_checkpointer" api/routes/chat.py
```

Deve mostrar apenas `get_async_checkpointer()`.

### Problema: `TypeError: tuple indices must be integers`

**Causa:** Falta `row_factory=dict_row`

**Solução:** Já foi corrigido. Verificar:
```bash
grep -n "row_factory=dict_row" core/checkpointing.py
```

Deve mostrar linhas 59 e 69.

---

## ✅ Checklist de Validação

Após executar todos os testes, você deve ter:

- [ ] Logs confirmam "✅ Sync/Async PostgresSaver initialized with dict_row factory"
- [ ] Primeira mensagem retorna resposta válida (não erro 401 ou 500)
- [ ] Checkpoints aparecem no banco de dados após enviar mensagens
- [ ] Agente recupera contexto ao continuar conversa (mesmo thread_id)
- [ ] Checkpoints persistem após reiniciar backend
- [ ] Múltiplos checkpoints são salvos por thread
- [ ] Endpoint `/stream` funciona e salva checkpoints
- [ ] Modo VSA funciona e salva checkpoints

---

## 📊 Resultados Esperados

### ✅ Sucesso Total

```
✅ Todas as mensagens retornam respostas válidas
✅ Checkpoints são salvos no PostgreSQL
✅ Contexto é recuperado entre mensagens
✅ Persistência sobrevive a reinicializações
✅ Sync e Async checkpointers funcionam
✅ VSA mode funciona com persistência
```

### ⚠️ Sucesso Parcial (Requer Investigação)

- Mensagens funcionam, mas checkpoints não aparecem no banco
- Checkpoints são salvos, mas contexto não é recuperado
- Funciona em `/chat` mas não em `/stream`

### ❌ Falha (Reportar)

- Erro 500 em todas as requisições
- `NotImplementedError` ainda aparece
- `TypeError: tuple indices must be integers`

---

## 📞 Suporte

**Documentação Completa:**
- `.agent/CORRECAO-PERSISTENCIA-POSTGRESQL.md` - Relatório técnico detalhado
- `.agent/RESUMO-EXECUTIVO-PERSISTENCIA.md` - Resumo executivo

**Logs Úteis:**
```bash
# Backend
docker compose logs backend --tail 100

# PostgreSQL
docker compose logs postgres --tail 50

# Verificar erros
docker compose logs backend | grep -i -E "error|exception|traceback" | tail -50
```

**Commit de Referência:** c7996db
**Data da Correção:** 2026-01-28
