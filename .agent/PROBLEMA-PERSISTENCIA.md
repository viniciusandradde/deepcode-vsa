# Problema: Conversas não estão sendo salvas no PostgreSQL

## 🐛 Problemas Identificados

### 1. MemorySaver Hardcoded (Prioridade CRÍTICA)
**Arquivo:** `api/routes/chat.py` (linhas 30-32)

**Código atual:**
```python
# Initialize checkpointer with MemorySaver (simpler and reliable)
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
```

**Problema:** O código está usando `MemorySaver()` forçado, ignorando completamente a função `get_checkpointer()` que existe em `core/checkpointing.py` e que tenta usar PostgreSQL.

**Resultado:** Todas as conversas são armazenadas apenas em memória e são perdidas quando o container reinicia.

---

### 2. Banco de Dados Não Existe (Prioridade CRÍTICA)
**Erro ao tentar conectar:**
```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed:
FATAL:  database "deepcode_vsa" does not exist
```

**Problema:** O banco de dados PostgreSQL não foi criado. O container do Postgres está rodando, mas o database específico não existe.

---

### 3. Frontend Usando apenas localStorage
**Arquivo:** `frontend/src/app/api/threads/route.ts`

**Código atual:**
```typescript
export async function GET() {
  try {
    // Por enquanto, retorna lista vazia ou cria uma sessão padrão
    // Em produção, isso viria de um endpoint de listagem de threads
    return NextResponse.json({ threads: [] });
  } catch (error) {
    console.error("Error loading threads:", error);
    return NextResponse.json({ error: "Failed to load threads" }, { status: 500 });
  }
}
```

**Problema:** Os endpoints do frontend não estão fazendo proxy para o backend FastAPI. Eles apenas retornam dados vazios ou geram IDs localmente.

---

### 4. Backend Sem Rotas de Threads
**Arquivo:** `api/main.py`

**Rotas disponíveis:**
- `/api/v1/chat` ✅
- `/api/v1/rag` ✅
- `/api/v1/agents` ✅
- `/api/v1/threads` ❌ **NÃO EXISTE**

**Problema:** Não há endpoint no backend para criar/listar/deletar threads. O sistema depende apenas do checkpointing do LangGraph.

---

## ✅ Solução Proposta

### Solução 1: Criar Banco de Dados e Tabelas

**Passo 1:** Criar database
```bash
docker compose exec postgres psql -U postgres -c "CREATE DATABASE deepcode_vsa;"
```

**Passo 2:** Criar tabelas de checkpoint do LangGraph
```sql
-- Tabelas necessárias para PostgresSaver do LangGraph
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    value JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_writes_thread_id ON checkpoint_writes(thread_id);
```

**Passo 3:** Criar tabelas adicionais para sessões/mensagens (opcional mas recomendado)
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_id TEXT,
    used_tavily BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
```

---

### Solução 2: Usar get_checkpointer() em vez de MemorySaver

**Arquivo:** `api/routes/chat.py`

**ANTES:**
```python
# Initialize checkpointer with MemorySaver (simpler and reliable)
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
```

**DEPOIS:**
```python
# Initialize checkpointer (will use PostgreSQL if available, fallback to Memory)
from core.checkpointing import get_checkpointer
checkpointer = get_checkpointer()
```

**Benefícios:**
- ✅ Tenta usar PostgreSQL primeiro
- ✅ Fallback automático para MemorySaver se PostgreSQL falhar
- ✅ Checkpoints persistem no banco
- ✅ Conversas não são perdidas ao reiniciar

---

### Solução 3: Criar Endpoints de Threads no Backend (opcional)

**Arquivo:** `api/routes/threads.py` (NOVO)

```python
"""Thread/Session management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from core.database import get_conn

router = APIRouter()

class ThreadCreate(BaseModel):
    title: Optional[str] = None

class Thread(BaseModel):
    thread_id: str
    title: str
    created_at: str

@router.get("/")
async def list_threads() -> dict:
    """List all threads/sessions."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, created_at
            FROM sessions
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        threads = [
            {
                "thread_id": row[0],
                "title": row[1],
                "created_at": row[2].isoformat() if row[2] else None
            }
            for row in rows
        ]

        return {"threads": threads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_thread(data: ThreadCreate) -> dict:
    """Create a new thread/session."""
    import uuid
    from datetime import datetime

    thread_id = f"thread-{uuid.uuid4().hex[:8]}"
    title = data.title or f"Nova Sessão {datetime.now().strftime('%H:%M')}"

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (id, title, created_at)
            VALUES (%s, %s, NOW())
        """, (thread_id, title))
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "thread_id": thread_id,
            "title": title
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a thread/session."""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = %s", (thread_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Adicionar ao main.py:**
```python
from api.routes import chat, rag, agents, threads

app.include_router(threads.router, prefix="/api/v1/threads", tags=["threads"])
```

---

### Solução 4: Atualizar Frontend para Usar Backend

**Arquivo:** `frontend/src/app/api/threads/route.ts`

**DEPOIS:**
```typescript
import { NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

export async function GET() {
  try {
    // Proxy para o backend
    const res = await fetch(backend("/api/v1/threads"), {
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error("Backend request failed");
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error loading threads:", error);
    // Fallback: retorna lista vazia
    return NextResponse.json({ threads: [] });
  }
}

export async function POST() {
  try {
    // Proxy para o backend
    const res = await fetch(backend("/api/v1/threads"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: null }),
    });

    if (!res.ok) {
      throw new Error("Backend request failed");
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error creating thread:", error);
    // Fallback: gera ID local
    const threadId = `thread-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    return NextResponse.json({
      thread_id: threadId,
      thread: {
        thread_id: threadId,
        created_at: new Date().toISOString(),
      }
    });
  }
}
```

---

## 🎯 Prioridades de Implementação

### Mínimo Necessário (1h):
1. ✅ Criar banco de dados `deepcode_vsa`
2. ✅ Criar tabelas de checkpoint do LangGraph
3. ✅ Mudar `chat.py` para usar `get_checkpointer()`
4. ✅ Testar se checkpoints funcionam

**Resultado:** Conversas persistem via LangGraph checkpointing

### Completo Recomendado (3-4h):
1. Tudo do mínimo acima
2. Criar tabelas de sessions/messages
3. Implementar endpoints de threads no backend
4. Atualizar frontend para usar endpoints do backend
5. Testar persistência completa

**Resultado:** Sistema completo de persistência com UI de gerenciamento de sessões

---

## 🧪 Como Testar Após Fix

### Teste 1: Verificar Banco de Dados
```bash
docker compose exec postgres psql -U postgres -d deepcode_vsa -c "\dt"
```

**Esperado:** Ver tabelas `checkpoints` e `checkpoint_writes`

### Teste 2: Verificar Checkpointer
```bash
docker compose logs backend | grep -i checkpoint
```

**Esperado:** Ver log indicando PostgresSaver inicializado

### Teste 3: Criar Conversa e Reiniciar
1. Criar conversa no frontend
2. Enviar 2-3 mensagens
3. Reiniciar backend: `docker compose restart backend`
4. Recarregar frontend
5. **Verificar:** Conversa deve estar lá ✅

### Teste 4: Verificar Dados no Banco
```bash
docker compose exec postgres psql -U postgres -d deepcode_vsa -c "SELECT thread_id, checkpoint_id FROM checkpoints LIMIT 5;"
```

**Esperado:** Ver checkpoints salvos

---

## 📋 Checklist de Implementação

- [ ] Criar banco `deepcode_vsa`
- [ ] Criar tabelas de checkpoint
- [ ] Mudar `chat.py` para usar `get_checkpointer()`
- [ ] Testar persistência básica
- [ ] (Opcional) Criar tabelas sessions/messages
- [ ] (Opcional) Criar routes/threads.py
- [ ] (Opcional) Atualizar frontend proxies
- [ ] (Opcional) Testar UI de sessões

---

**Documento criado:** 2026-01-27
**Status:** Problemas identificados, aguardando implementação
**Prioridade:** CRÍTICA (conversas sendo perdidas)
