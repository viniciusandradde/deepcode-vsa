# Correção Necessária: Persistência de Checkpoints

**Data:** 27/01/2026  
**Prioridade:** ALTA  
**Status:** ⚠️ Problema Identificado - Requer Correção

---

## Problema

Os checkpoints **não estão sendo salvos** no PostgreSQL, mesmo com:
- ✅ Banco rodando e saudável
- ✅ Tabelas criadas
- ✅ Checkpointers inicializados corretamente

---

## Causa Raiz

### Problema 1: Checkpointer inicializado tarde

**Arquivo:** `api/routes/chat.py:31`

```python
# ❌ INCORRETO: Chamado no nível do módulo
checkpointer = get_checkpointer()  # ← Retorna MemorySaver (ainda não inicializado)
```

**Problema:**
- `get_checkpointer()` é chamado quando o módulo é importado
- Nesse momento, `initialize_checkpointer()` ainda não executou
- `_sync_checkpointer` global ainda é `None`
- `get_checkpointer()` retorna `MemorySaver` como fallback

**Solução:**
```python
# ✅ CORRETO: Chamar dentro das funções
@router.post("")
async def chat(request: ChatRequest):
    checkpointer = get_checkpointer()  # ← Após initialize_checkpointer()
    agent = SimpleAgent(..., checkpointer=checkpointer)
```

---

## Correções Necessárias

### Correção 1: `api/routes/chat.py`

**Remover linha 31:**
```python
# ❌ REMOVER ESTA LINHA
checkpointer = get_checkpointer()
```

**Adicionar dentro de `chat()`:**
```python
@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # ... código existente ...
    
    # ✅ ADICIONAR: Obter checkpointer em runtime
    checkpointer = get_checkpointer()
    
    # Select agent based on VSA mode
    if request.enable_vsa:
        agent = UnifiedAgent(..., checkpointer=checkpointer)
    else:
        agent = SimpleAgent(..., checkpointer=checkpointer)
```

**Adicionar dentro de `stream_chat()`:**
```python
@router.post("/stream")
async def stream_chat(request: ChatRequest):
    # ... código existente ...
    
    # ✅ ADICIONAR: Obter async checkpointer em runtime
    checkpointer = get_async_checkpointer()
    
    # Select agent based on VSA mode
    if request.enable_vsa:
        agent = UnifiedAgent(..., checkpointer=checkpointer)
    else:
        agent = SimpleAgent(..., checkpointer=checkpointer)
```

**Atualizar import:**
```python
from core.checkpointing import get_checkpointer, get_async_checkpointer
```

---

### Correção 2: Verificar suporte de `create_agent` a checkpointer

**Arquivo:** `core/agents/simple.py:113`

**Problema Potencial:**
O `create_agent` do LangChain pode não aceitar `checkpointer` diretamente.

**Verificar:**
1. Se `create_agent` suporta parâmetro `checkpointer`
2. Se necessário, usar `graph.compile(checkpointer=...)` após `create_agent`

**Alternativa (se necessário):**
```python
def create_graph(self):
    if self._graph is None:
        # Criar grafo sem checkpointer
        self._graph = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            state_schema=AgentState,
            middleware=middlewares,
        )
        
        # Compilar com checkpointer se fornecido
        if self.checkpointer:
            self._graph = self._graph.compile(checkpointer=self.checkpointer)
    
    return self._graph
```

---

## Testes Após Correção

### Teste 1: Verificar tipo do checkpointer

```python
from core.checkpointing import get_checkpointer
cp = get_checkpointer()
print(type(cp))  # Deve ser PostgresSaver, não MemorySaver
```

### Teste 2: Enviar mensagem e verificar checkpoint

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Teste", "thread_id": "test-after-fix"}'
```

```sql
SELECT COUNT(*) FROM checkpoints WHERE thread_id = 'test-after-fix';
-- Deve retornar > 0
```

### Teste 3: Verificar mensagens salvas

```sql
SELECT 
    thread_id,
    jsonb_pretty(checkpoint->'channel_values'->'messages')
FROM checkpoints 
WHERE thread_id = 'test-after-fix'
ORDER BY created_at DESC 
LIMIT 1;
```

---

## Checklist de Implementação

- [ ] Remover `checkpointer = get_checkpointer()` do nível do módulo
- [ ] Adicionar `checkpointer = get_checkpointer()` dentro de `chat()`
- [ ] Adicionar `checkpointer = get_async_checkpointer()` dentro de `stream_chat()`
- [ ] Atualizar import para incluir `get_async_checkpointer`
- [ ] Verificar se `create_agent` suporta checkpointer
- [ ] Testar envio de mensagem
- [ ] Verificar checkpoint no banco
- [ ] Documentar solução final

---

## Impacto

**Sem esta correção:**
- ❌ Checkpoints não são salvos
- ❌ Conversas não persistem entre reinicializações
- ❌ Threads não são mantidos

**Com esta correção:**
- ✅ Checkpoints salvos em PostgreSQL
- ✅ Conversas persistem
- ✅ Threads mantidos entre sessões

---

**Documento gerado:** 27/01/2026  
**Ação requerida:** Implementar correções acima
