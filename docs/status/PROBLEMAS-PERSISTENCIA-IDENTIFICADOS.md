# Problemas de Persistência Identificados

**Data:** 27/01/2026  
**Status:** 🔴 **2 Problemas Críticos Identificados**

---

## Problema 1: Checkpointer Inicializado Tarde

### Descrição

O `get_checkpointer()` está sendo chamado no **nível do módulo** antes de `initialize_checkpointer()` executar.

**Arquivo:** `api/routes/chat.py:31`

```python
# ❌ PROBLEMA
checkpointer = get_checkpointer()  # ← Executa quando módulo é importado
```

**Resultado:**
- `checkpointer` = `MemorySaver` (não persiste)
- `_sync_checkpointer` global = `PostgresSaver` (não usado)

### Solução

Mover `get_checkpointer()` para dentro das funções:

```python
@router.post("")
async def chat(request: ChatRequest):
    checkpointer = get_checkpointer()  # ← Após initialize_checkpointer()
    agent = SimpleAgent(..., checkpointer=checkpointer)
```

---

## Problema 2: Erro com Async Checkpointer

### Descrição

Erro nos logs ao usar `get_async_checkpointer()`:

```
TypeError: Invalid checkpointer provided. Expected an instance of `BaseCheckpointSaver`, `True`, `False`, or `None`. 
Received _GeneratorContextManager.
```

**Causa:**
- `AsyncPostgresSaver` pode estar sendo retornado como context manager
- Ou há problema na inicialização do async pool

**Arquivo:** `core/checkpointing.py:69`

```python
_async_checkpointer = AsyncPostgresSaver(_async_pool)
```

### Solução Possível

Verificar se `AsyncPostgresSaver` precisa ser usado de forma diferente ou se o pool precisa estar aberto antes.

---

## Status Atual

| Item | Status | Detalhes |
|------|--------|----------|
| **PostgreSQL** | ✅ | Rodando e saudável |
| **Tabelas** | ✅ | Criadas corretamente |
| **Inicialização** | ✅ | Logs mostram "initialized" |
| **Checkpointer sync** | ❌ | Retorna MemorySaver (problema 1) |
| **Checkpointer async** | ❌ | Erro _GeneratorContextManager (problema 2) |
| **Checkpoints salvos** | ❌ | 0 checkpoints no banco |

---

## Correções Necessárias

### Correção 1: `api/routes/chat.py`

1. Remover linha 31: `checkpointer = get_checkpointer()`
2. Adicionar `checkpointer = get_checkpointer()` dentro de `chat()`
3. Adicionar `checkpointer = get_async_checkpointer()` dentro de `stream_chat()`
4. Atualizar import: `from core.checkpointing import get_checkpointer, get_async_checkpointer`

### Correção 2: `core/checkpointing.py`

Verificar inicialização do `AsyncPostgresSaver` e garantir que retorna o objeto correto, não um context manager.

---

## Testes Após Correções

1. Verificar tipo: `type(get_checkpointer())` deve ser `PostgresSaver`
2. Enviar mensagem: `curl -X POST /api/v1/chat ...`
3. Verificar banco: `SELECT COUNT(*) FROM checkpoints WHERE thread_id = 'test-xxx'`
4. Confirmar: Checkpoint salvo com sucesso

---

**Documento gerado:** 27/01/2026  
**Ação:** Implementar correções acima
