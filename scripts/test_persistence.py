#!/usr/bin/env python3
"""Script para testar persistência de checkpoints no PostgreSQL."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.checkpointing import initialize_checkpointer, get_checkpointer, get_async_checkpointer
from core.agents.simple import SimpleAgent
from core.tools.search import tavily_search
from langchain_core.messages import HumanMessage


async def test_persistence():
    """Testa persistência de checkpoints."""
    print("🔄 Inicializando checkpointers...")
    await initialize_checkpointer()
    
    print("\n📊 Verificando checkpointers...")
    sync_cp = get_checkpointer()
    async_cp = get_async_checkpointer()
    
    print(f"Sync checkpointer: {type(sync_cp).__name__}")
    print(f"Async checkpointer: {type(async_cp).__name__}")
    
    is_postgres_sync = "PostgresSaver" in str(type(sync_cp))
    is_postgres_async = "PostgresSaver" in str(type(async_cp)) or "AsyncPostgresSaver" in str(type(async_cp))
    
    print(f"✅ Sync usando PostgreSQL: {is_postgres_sync}")
    print(f"✅ Async usando PostgreSQL: {is_postgres_async}")
    
    if not is_postgres_sync:
        print("⚠️  ATENÇÃO: Sync checkpointer não está usando PostgreSQL!")
        return
    
    print("\n🤖 Criando agente...")
    agent = SimpleAgent(
        model_name=os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
        tools=[tavily_search],
        checkpointer=sync_cp,
    )
    
    print("\n💬 Enviando mensagem de teste...")
    thread_id = "test-persistence-script"
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="Teste de persistência")]},
        config=config
    )
    
    print(f"✅ Mensagem processada: {result.get('messages', [])[-1].content[:50]}...")
    print(f"📝 Thread ID: {thread_id}")
    
    # Verificar se checkpoint foi salvo
    print("\n🔍 Verificando checkpoint no banco...")
    from core.database import get_conn
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM checkpoints WHERE thread_id = %s",
                (thread_id,)
            )
            count = cur.fetchone()[0]
            
            if count > 0:
                print(f"✅ Checkpoint encontrado! Total: {count}")
                
                cur.execute(
                    "SELECT checkpoint_id, created_at FROM checkpoints WHERE thread_id = %s ORDER BY created_at DESC LIMIT 1",
                    (thread_id,)
                )
                row = cur.fetchone()
                if row:
                    print(f"   Checkpoint ID: {row[0]}")
                    print(f"   Criado em: {row[1]}")
            else:
                print("❌ Nenhum checkpoint encontrado no banco")
                print("⚠️  Possível problema: create_agent pode não estar salvando checkpoints automaticamente")


if __name__ == "__main__":
    asyncio.run(test_persistence())
