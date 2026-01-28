# Testes de Persistência PostgreSQL - Resultados Completos

**Data:** 27/01/2026  
**Status:** ⚠️ Problema Identificado - Requer Correção

---

## Problema Identificado

### Causa Raiz

O `get_checkpointer()` está sendo chamado no **nível do módulo** (`api/routes/chat.py:31`) **ANTES** do `lifespan` do FastAPI executar `initialize_checkpointer()`.

**Fluxo Atual (INCORRETO):**
```
1. Import do módulo api/routes/chat.py
2. Linha 31: checkpointer = get_checkpointer()  ← Retorna MemorySaver (ainda não inicializado)
3. FastAPI inicia
4. lifespan executa initialize_checkpointer()  ← Muito tarde!
5. _sync_checkpointer é definido, mas checkpointer já foi atribuído
```

**Resultado:**
- `checkpointer` no módulo = `MemorySaver` (não persiste)
- `_sync_checkpointer` global = `PostgresSaver` (não usado)

---

## Evidências

### 1. Verificação de Tipo

```bash
docker exec backend python3 -c "
from core.checkpointing import get_checkpointer, _sync_checkpointer
print('_sync_checkpointer:', type(_sync_checkpointer))  # NoneType
print('get_checkpointer():', type(get_checkpointer()))  # InMemorySaver
"
```

**Resultado:**
- `_sync_checkpointer`: `NoneType` (não inicializado quando módulo carrega)
- `get_checkpointer()`: `InMemorySaver` (fallback porque `_sync_checkpointer` é None)

### 2. Logs de Inicialização

```
✅ PostgreSQL Checkpointers (Sync & Async) initialized
```

**Conclusão:** Checkpointers são inicializados corretamente, mas muito tarde.

### 3. Testes de Persistência

**Teste 1:** Mensagem enviada via `/api/v1/chat`
- ✅ Mensagem processada
- ❌ Checkpoint não encontrado no banco (0 checkpoints)

**Teste 2:** Script direto `test_persistence.py`
- ✅ Checkpointer inicializado corretamente
- ✅ PostgresSaver confirmado
- ⏳ Aguardando resultado do teste

---

## Solução Necessária

### Correção 1: Mover `get_checkpointer()` para dentro das funções

**Arquivo:** `api/routes/chat.py`

**ANTES (INCORRETO):**
```python
router = APIRouter()
checkpointer = get_checkpointer()  # ← Chamado no nível do módulo

@router.post("")
async def chat(request: ChatRequest):
    agent = SimpleAgent(..., checkpointer=checkpointer)  # ← Usa MemorySaver
```

**DEPOIS (CORRETO):**
```python
router = APIRouter()
# Checkpointer será obtido em runtime após inicialização

@router.post("")
async def chat(request: ChatRequest):
    checkpointer = get_checkpointer()  # ← Chamado após initialize_checkpointer()
    agent = SimpleAgent(..., checkpointer=checkpointer)  # ← Usa PostgresSaver
```

### Correção 2: Usar async checkpointer no endpoint de streaming

**Arquivo:** `api/routes/chat.py`

```python
@router.post("/stream")
async def stream_chat(request: ChatRequest):
    checkpointer = get_async_checkpointer()  # ← Async para streaming
    agent = SimpleAgent(..., checkpointer=checkpointer)
```

---

## Testes Realizados

### Teste 1: Verificação de Configuração

```bash
# Verificar variáveis de ambiente
USE_POSTGRES_CHECKPOINT=true ✅
DB_NAME=ai_agent_db ✅
```

### Teste 2: Verificação de Banco

```bash
# Verificar tabelas
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE '%checkpoint%';
```

**Resultado:**
- ✅ `checkpoints` existe
- ✅ `checkpoint_writes` existe
- ✅ `checkpoint_blobs` existe
- ✅ `checkpoint_migrations` existe

### Teste 3: Envio de Mensagem

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Teste", "thread_id": "test-001"}'
```

**Resultado:**
- ✅ Mensagem processada
- ❌ Checkpoint não salvo (0 checkpoints no banco)

### Teste 4: Script Direto

```bash
python3 scripts/test_persistence.py
```

**Resultado:** Aguardando execução

---

## Comparação: Template vs Projeto Atual

### Template (`template-vsa-tech/core/agents/simple.py`)

```python
def create_graph(self, checkpointer=None):
    # create_agent NÃO aceita checkpointer diretamente
    self._graph = create_agent(...)
    # Checkpointer deve ser passado no config ao invocar
    if checkpointer:
        self._graph._checkpointer = checkpointer
```

**Observação:** Template também não passa checkpointer para `create_agent`!

### Projeto Atual (`core/agents/simple.py`)

```python
def create_graph(self):
    self._graph = create_agent(
        ...,
        checkpointer=self.checkpointer,  # ← Passa diretamente
    )
```

**Observação:** Projeto atual tenta passar checkpointer, mas pode não funcionar com `create_agent`.

---

## Verificação: create_agent e Checkpointer

### Documentação LangChain

O `create_agent` do LangChain **pode não suportar checkpointer diretamente**. Verificar:

1. Se `create_agent` aceita parâmetro `checkpointer`
2. Se checkpointer precisa ser passado via `config` ao invocar
3. Se é necessário usar `graph.compile(checkpointer=...)` após `create_agent`

### Alternativa: Usar LangGraph diretamente

Se `create_agent` não suporta checkpointer, usar LangGraph diretamente:

```python
from langgraph.prebuilt import create_react_agent

graph = create_react_agent(
    model=self.model,
    tools=self.tools,
    state_modifier=self.system_prompt,
)
compiled = graph.compile(checkpointer=checkpointer)
```

---

## Próximos Passos

1. ✅ **Problema identificado:** Checkpointer inicializado tarde
2. ⏳ **Correção necessária:** Mover `get_checkpointer()` para dentro das funções
3. ⏳ **Verificar:** Se `create_agent` suporta checkpointer
4. ⏳ **Testar:** Após correção, verificar checkpoints no banco
5. ⏳ **Documentar:** Solução final

---

## Status Atual

| Item | Status | Observação |
|------|--------|------------|
| **PostgreSQL rodando** | ✅ | Container saudável |
| **Tabelas criadas** | ✅ | Todas as tabelas existem |
| **Checkpointers inicializados** | ✅ | PostgresSaver + AsyncPostgresSaver |
| **Checkpointer usado no código** | ❌ | MemorySaver (não inicializado) |
| **Checkpoints salvos** | ❌ | 0 checkpoints no banco |

---

**Documento gerado:** 27/01/2026  
**Status:** ⚠️ Requer correção de código
