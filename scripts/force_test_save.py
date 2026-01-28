import asyncio
import os
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.checkpointing import initialize_checkpointer, get_checkpointer
from core.database import get_conn
from langchain_core.messages import HumanMessage, AIMessage
import psycopg
from psycopg.rows import dict_row

async def test_db_save():
    print("🚀 Iniciando teste de salvamento de checkpoint...")
    
    # 1. Forçar inicialização do checkpointer
    await initialize_checkpointer()
    checkpointer = get_checkpointer()
    
    print(f"📦 Tipo do checkpointer: {type(checkpointer).__name__}")
    if "PostgresSaver" not in str(type(checkpointer)):
        print("❌ ERRO: O checkpointer não é PostgresSaver. Verifique o .env e core/checkpointing.py")
        return

    # 2. Dados do checkpoint fake
    thread_id = "test-manual-save-001"
    checkpoint_id = "1ef4f797-8335-6428-8001-8a1503f9b875"
    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": ""
        }
    }
    
    checkpoint = {
        "v": 1,
        "id": checkpoint_id,
        "ts": "2026-01-27T20:00:00Z",
        "channel_values": {
            "messages": [
                HumanMessage(content="Teste de persistência manual"),
                AIMessage(content="Checkpoint salvo com sucesso no banco!")
            ]
        },
        "channel_versions": {"messages": 1},
        "versions_seen": {},
        "pending_sends": []
    }
    
    metadata = {
        "source": "manual_test",
        "step": 0,
        "writes": {}
    }

    # 3. Tentar salvar
    print(f"💾 Tentando salvar checkpoint para thread: {thread_id}...")
    try:
        checkpointer.put(config, checkpoint, metadata, {})
        print("✅ Comando put executado sem erros.")
    except Exception as e:
        print(f"❌ Erro ao executar put: {e}")
        return

    # 4. Verificar no banco via SQL direto
    print("🔍 Verificando no banco de dados...")
    db_name = os.getenv("DB_NAME", "ai_agent_db")
    
    try:
        from core.database import get_db_url
        with psycopg.connect(get_db_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as total FROM checkpoints WHERE thread_id = %s", (thread_id,))
                result = cur.fetchone()
                print(f"📊 Total de checkpoints para esta thread: {result['total']}")
                
                if result['total'] > 0:
                    print("✨ SUCESSO: Checkpoint persistido no PostgreSQL!")
                else:
                    print("⚠️ FALHA: O comando não deu erro, mas o registro não aparece no banco.")
    except Exception as e:
        print(f"❌ Erro ao consultar banco: {e}")

if __name__ == "__main__":
    asyncio.run(test_db_save())
