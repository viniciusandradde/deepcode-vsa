# Resultado do Teste de Persistência - 27/01/2026

## 🧪 Teste Executado: Opção A - Verificar Persistência

**Data:** 2026-01-27 15:50 BRT
**Objetivo:** Testar se checkpointing PostgreSQL está funcionando

---

## 🔴 RESULTADO: PROBLEMA CRÍTICO ENCONTRADO

### Erro Identificado

```
TypeError: Invalid checkpointer provided. Expected an instance of `BaseCheckpointSaver`,
`True`, `False`, or `None`. Received _GeneratorContextManager.
```

### Causa Raiz

**PostgresSaver.from_conn_string() retorna um CONTEXT MANAGER, não um BaseCheckpointSaver.**

**Código problemático:**
```python
# core/checkpointing.py (ANTES)
checkpointer = PostgresSaver.from_conn_string(db_url)
return checkpointer  # ← Retorna context manager, NÃO saver!
```

**Assinatura correta:**
```python
# LangGraph documentation
PostgresSaver.from_conn_string(conn_string) -> ContextManager[PostgresSaver]
AsyncPostgresSaver.from_conn_string(conn_string) -> AsyncContextManager[AsyncPostgresSaver]
```

### Por que Acontece

LangGraph PostgresSaver usa **context managers** para gerenciar a conexão com o banco:

```python
# Uso correto (sync)
with PostgresSaver.from_conn_string(db_url) as saver:
    # Use saver aqui
    graph.compile(checkpointer=saver)

# Uso correto (async)
async with AsyncPostgresSaver.from_conn_string(db_url) as saver:
    # Use saver aqui
    await graph.ainvoke(input, config)
```

**Problema:** Não podemos retornar um context manager de uma função simples como `get_checkpointer()`.

---

## ✅ SOLUÇÃO TEMPORÁRIA APLICADA

### Voltamos para MemorySaver

```python
def get_checkpointer():
    """Get appropriate checkpointer for environment.

    Returns:
        MemorySaver (PostgresSaver requires context manager setup)
    """
    print("ℹ️  Using MemorySaver (PostgreSQL checkpointing requires async context - TODO)")
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
```

**Resultado:**
- ✅ Sistema funciona novamente
- ❌ Checkpoints em memória (perdidos ao reiniciar)
- ⚠️ Persistência PostgreSQL requer refatoração

---

## 🔧 SOLUÇÃO DEFINITIVA (Implementação Futura)

### Opção 1: Connection Pool Global (Recomendado)

**Estratégia:** Criar um pool de conexões global que permanece aberto durante toda a vida da aplicação.

**Implementação:**

```python
# core/checkpointing.py
import asyncio
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Global connection pool
_connection_pool: Optional[AsyncConnectionPool] = None
_checkpointer: Optional[AsyncPostgresSaver] = None

async def initialize_checkpointer():
    """Initialize checkpointer with connection pool.

    Call this during app startup (FastAPI lifespan).
    """
    global _connection_pool, _checkpointer

    if _connection_pool is None:
        from core.database import get_db_url
        db_url = get_db_url()

        # Create connection pool
        _connection_pool = AsyncConnectionPool(
            conninfo=db_url,
            min_size=1,
            max_size=10,
        )

        # Create checkpointer with pool
        conn = await _connection_pool.getconn()
        _checkpointer = AsyncPostgresSaver(conn)
        await _checkpointer.setup()  # Create tables if needed

        print("✅ PostgreSQL checkpointer initialized with connection pool")

def get_checkpointer():
    """Get the global checkpointer instance."""
    if _checkpointer is None:
        print("⚠️  Checkpointer not initialized, using MemorySaver")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    return _checkpointer

async def cleanup_checkpointer():
    """Cleanup checkpointer resources.

    Call this during app shutdown (FastAPI lifespan).
    """
    global _connection_pool, _checkpointer

    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        _checkpointer = None
        print("ℹ️  Checkpointer cleanup complete")
```

**Integração no FastAPI:**

```python
# api/main.py
from contextlib import asynccontextmanager
from core.checkpointing import initialize_checkpointer, cleanup_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_checkpointer()
    yield
    # Shutdown
    await cleanup_checkpointer()

app = FastAPI(
    title="AI Agent + RAG API",
    lifespan=lifespan  # ← Add lifespan
)
```

**Benefícios:**
- ✅ Conexão permanente (não abre/fecha a cada requisição)
- ✅ Performance melhor (connection pooling)
- ✅ Checkpointer reutilizável
- ✅ Cleanup adequado no shutdown

---

### Opção 2: Context Manager por Requisição (Simples mas Lento)

**Estratégia:** Abrir context manager em cada endpoint.

**Implementação:**

```python
# api/routes/chat.py
@router.post("/")
async def chat_sync(request: ChatRequest):
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from core.database import get_db_url

    # Abre context manager por requisição
    async with AsyncPostgresSaver.from_conn_string(get_db_url()) as checkpointer:
        agent = UnifiedAgent(
            model_name=request.model,
            tools=tools,
            checkpointer=checkpointer,  # ← Passa o saver do context
        )

        config = {"configurable": {"thread_id": thread_id}}
        result = await agent.ainvoke(input, config)

        return ChatResponse(response=result["messages"][-1].content)
```

**Desvantagens:**
- ⚠️ Abre nova conexão a cada requisição (lento)
- ⚠️ Overhead de setup/teardown
- ⚠️ Não recomendado para produção

---

### Opção 3: MemorySaver com Backup Periódico (Híbrido)

**Estratégia:** Usar MemorySaver + salvar snapshots no PostgreSQL periodicamente.

**Implementação:**

```python
# core/checkpointing.py
import asyncio
import json
from langgraph.checkpoint.memory import MemorySaver

class MemorySaverWithBackup(MemorySaver):
    """MemorySaver that periodically backs up to PostgreSQL."""

    def __init__(self, backup_interval_seconds=300):
        super().__init__()
        self.backup_interval = backup_interval_seconds
        self._backup_task = None

    async def start_backup_task(self):
        """Start periodic backup task."""
        self._backup_task = asyncio.create_task(self._backup_loop())

    async def _backup_loop(self):
        """Backup checkpoints to PostgreSQL periodically."""
        from core.database import get_conn

        while True:
            await asyncio.sleep(self.backup_interval)

            try:
                conn = get_conn()
                cursor = conn.cursor()

                # Save all checkpoints to database
                for thread_id, checkpoints in self.storage.items():
                    for checkpoint_id, checkpoint_data in checkpoints.items():
                        cursor.execute("""
                            INSERT INTO checkpoints (thread_id, checkpoint_id, checkpoint, metadata)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (thread_id, checkpoint_id) DO UPDATE
                            SET checkpoint = EXCLUDED.checkpoint
                        """, (
                            thread_id,
                            checkpoint_id,
                            json.dumps(checkpoint_data),
                            json.dumps({})
                        ))

                conn.commit()
                cursor.close()
                conn.close()
                print(f"✅ Backed up checkpoints to PostgreSQL")
            except Exception as e:
                print(f"⚠️  Backup error: {e}")
```

**Benefícios:**
- ✅ Performance de memória
- ✅ Backup persistente
- ⚠️ Pode perder últimos N minutos em crash

---

## 📊 COMPARAÇÃO DE SOLUÇÕES

| Solução | Performance | Persistência | Complexidade | Recomendação |
|---------|-------------|--------------|--------------|--------------|
| **Opção 1: Connection Pool** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ **MELHOR** |
| Opção 2: Context por Request | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | 🟡 Simples mas lento |
| Opção 3: Memory + Backup | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 🟡 Híbrido |
| **Status Atual: MemorySaver** | ⭐⭐⭐⭐⭐ | ❌ | ⭐ | ⚠️ Temporário |

---

## 🎯 PLANO DE AÇÃO

### Curto Prazo (Hoje)
1. ✅ Manter MemorySaver (sistema funciona)
2. ✅ Documentar problema (este arquivo)
3. ⏳ Commitar alterações atuais (toggles funcionando)
4. ⏳ Testar funcionamento básico do chat

### Médio Prazo (Esta Semana)
1. ⏳ Implementar Opção 1 (Connection Pool)
2. ⏳ Adicionar FastAPI lifespan events
3. ⏳ Testar persistência PostgreSQL
4. ⏳ Validar que checkpoints sobrevivem restart

### Longo Prazo (Próxima Sprint)
1. ⏳ Monitorar performance do checkpointing
2. ⏳ Implementar limpeza de checkpoints antigos
3. ⏳ Adicionar métricas de persistência
4. ⏳ Documentar arquitetura final

---

## 🧪 TESTES PENDENTES

### Teste 1: Funcionamento Básico (MemorySaver)

```bash
# Enviar mensagem
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Teste básico",
    "thread_id": "test-memory-001"
  }'

# Esperado: ✅ Resposta OK (mas não persiste ao restart)
```

### Teste 2: Verificar Database (Após Implementar Opção 1)

```bash
# Verificar checkpoints
docker compose exec postgres psql -U postgres -d deepcode_vsa \
  -c "SELECT thread_id, checkpoint_id FROM checkpoints LIMIT 5;"

# Esperado: Ver checkpoints salvos
```

### Teste 3: Teste de Restart (Após Implementar Opção 1)

```bash
# 1. Enviar mensagens
curl -X POST http://localhost:8000/api/v1/chat \
  -d '{"message": "Msg 1", "thread_id": "thread-restart"}'

curl -X POST http://localhost:8000/api/v1/chat \
  -d '{"message": "Msg 2", "thread_id": "thread-restart"}'

# 2. Reiniciar backend
docker compose restart backend

# 3. Continuar conversa
curl -X POST http://localhost:8000/api/v1/chat \
  -d '{"message": "Msg 3", "thread_id": "thread-restart"}'

# Esperado: ✅ Contexto da conversa mantido
```

---

## 📚 REFERÊNCIAS

- **LangGraph Checkpointing:** https://langchain-ai.github.io/langgraph/how-tos/persistence/
- **AsyncPostgresSaver:** https://langchain-ai.github.io/langgraph/reference/checkpoints/#asyncpostgressaver
- **FastAPI Lifespan:** https://fastapi.tiangolo.com/advanced/events/
- **psycopg3 Connection Pool:** https://www.psycopg.org/psycopg3/docs/advanced/pool.html

---

## 💡 LIÇÕES APRENDIDAS

1. **PostgresSaver.from_conn_string() retorna context manager**
   - Não pode ser usado diretamente como retorno de função
   - Requer gerenciamento de ciclo de vida

2. **MemorySaver é adequado para desenvolvimento**
   - Performance excelente
   - Sem overhead de I/O
   - MAS: Perde dados ao reiniciar

3. **Connection pooling é essencial para PostgreSQL**
   - Evita overhead de conexão por requisição
   - Melhor para produção
   - Requer setup no lifecycle da aplicação

4. **Async context managers precisam de await**
   - Não podem ser inicializados em código sync
   - FastAPI lifespan events são perfeitos para isso

---

**Documento criado:** 2026-01-27 15:50 BRT
**Status:** ✅ Problema identificado e documentado
**Próximo passo:** Implementar Opção 1 (Connection Pool) quando prioridade permitir
**Workaround atual:** MemorySaver (funciona mas não persiste)
