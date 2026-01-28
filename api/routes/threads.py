"""Thread and message history API routes backed by LangGraph checkpoints.

These endpoints expose the conversation threads stored in the PostgreSQL
checkpointer so that the frontend does NOT depend on localStorage to
reconstruir o histórico.

Design notes (based on LangGraph + checkpoint-postgres docs):
- Checkpoints are stored in the `checkpoints` and `checkpoint_writes` tables
  managed by `PostgresSaver` / `AsyncPostgresSaver`.
- The async checkpointer exposes:
    - `alist(config)`  -> async iterator over checkpoints
    - `aget(config)`   -> latest checkpoint state for a given thread
- The state/checkpoint structure may evolve, so the code below is defensive:
    it tenta extrair as mensagens de múltiplas formas antes de desistir.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from langchain_core.messages import BaseMessage

from core.checkpointing import get_async_checkpointer
from core.database import get_conn


router = APIRouter()


def _message_to_dict(msg: Any) -> Optional[Dict[str, Any]]:
    """Convert a LangChain BaseMessage (or dict-like) to a JSON-serializable dict.

    The frontend espera mensagens no formato:
    {
        "id": str,
        "role": "user" | "assistant",
        "content": str,
    }
    """
    # BaseMessage (HumanMessage, AIMessage, etc.)
    if isinstance(msg, BaseMessage):
        role = "assistant"
        msg_type = getattr(msg, "type", "") or msg.__class__.__name__.lower()
        if "human" in msg_type:
            role = "user"
        elif "system" in msg_type:
            # System messages não são exibidas como usuário/assistente no chat;
            # podemos ignorar ou mapear como "assistant". Aqui, ignoramos.
            return None

        return {
            "id": getattr(msg, "id", None),
            "role": role,
            "content": msg.content if isinstance(msg.content, str) else str(msg.content),
        }

    # Dict-like message (fallback)
    if isinstance(msg, dict):
        role = msg.get("role") or msg.get("type") or "assistant"
        if role in ("human", "user"):
            role = "user"
        elif role in ("ai", "assistant"):
            role = "assistant"

        content = msg.get("content")
        if not isinstance(content, str):
            content = str(content)

        return {
            "id": msg.get("id"),
            "role": role,
            "content": content,
        }

    # Unknown type – ignore
    return None


def _extract_messages_from_state(state: Any) -> List[Dict[str, Any]]:
    """Best-effort extraction of messages from a CheckpointState/Checkpoint.

    LangGraph internals podem mudar, então tentamos vários caminhos:
    - state.values["messages"]
    - state.channel_values["messages"]
    - state["values"]["messages"]
    - state["channel_values"]["messages"]
    """
    if state is None:
        return []

    # Helper to get attribute or dict key
    def _get(obj: Any, attr: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(attr)
        return getattr(obj, attr, None)

    # 1) values.messages
    values = _get(state, "values")
    channel_values = _get(state, "channel_values")

    messages = None
    if isinstance(values, dict):
        messages = values.get("messages")
    if messages is None and isinstance(channel_values, dict):
        messages = channel_values.get("messages")

    # 2) checkpoint.channel_values.messages (algumas versões expõem via .checkpoint)
    if messages is None:
        checkpoint = _get(state, "checkpoint")
        if isinstance(checkpoint, dict):
            cv = checkpoint.get("channel_values") or {}
            if isinstance(cv, dict):
                messages = cv.get("messages")

    if not messages:
        return []

    result: List[Dict[str, Any]] = []
    for msg in messages:
        converted = _message_to_dict(msg)
        if converted is not None:
            result.append(converted)
    return result


@router.get("")
async def list_threads() -> Dict[str, Any]:
    """Listar threads disponíveis a partir da tabela `checkpoints`.

    Usamos uma consulta SQL simples para evitar depender de detalhes
    internos da implementação do checkpointer.
    """
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                # Usa o timestamp dentro do JSON do checkpoint como last_ts
                cur.execute(
                    """
                    SELECT
                        thread_id,
                        MAX((checkpoint->>'ts')) AS last_ts
                    FROM checkpoints
                    GROUP BY thread_id
                    ORDER BY last_ts DESC NULLS LAST
                    """
                )
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar threads: {e}")

    threads = [
        {
            "id": row[0],
            "last_ts": row[1],
        }
        for row in rows
    ]
    return {"threads": threads}


@router.get("/{thread_id}")
async def get_thread(thread_id: str) -> Dict[str, Any]:
    """Recuperar mensagens de uma thread a partir do último checkpoint."""
    checkpointer = get_async_checkpointer()

    # Algumas implementações exigem apenas thread_id em configurable
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # aget deve retornar o último estado para o thread_id informado
        state = await checkpointer.aget(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar thread {thread_id}: {e}")

    if state is None:
        # Nenhum checkpoint encontrado para este thread
        return {"thread_id": thread_id, "messages": []}

    messages = _extract_messages_from_state(state)
    return {
        "thread_id": thread_id,
        "messages": messages,
    }


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str):
    """Placeholder para deleção de threads.

    No v1, não removemos dados do banco (seguindo princípios de auditoria),
    então este endpoint apenas existe para compatibilidade com o frontend.
    """
    # Se no futuro quisermos implementar deleção lógica, este é o lugar.
    return {}

