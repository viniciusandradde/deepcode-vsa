import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage, AIMessage


# Ajusta o PATH para importar o pacote local quando executado diretamente
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Desativa fixtures pesadas do conftest (DB) apenas neste módulo
@pytest.fixture(autouse=True)
def clean_db():
    yield


def _has_ai_text(messages, needle: str) -> bool:
    needle = (needle or "").lower()
    for m in messages:
        if isinstance(m, AIMessage):
            content = m.content
            if isinstance(content, str) and needle in content.lower():
                return True
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        if needle in (b.get("text") or "").lower():
                            return True
    return False


class _FakeTool:
    def __init__(self, name: str, data_key: str, id_value: str):
        self.name = name
        self._result = {"message": "ok", "data": {data_key: id_value}}

    def invoke(self, payload):
        return self._result


def test_quick_multi_intents_note_and_task(monkeypatch):
    # Importa módulos após ajustar sys.path
    from app.agent import workflow as wf
    from app.agent import tools as tools

    # Stub do parser: força a intenção primária como nota + slot de texto
    monkeypatch.setattr(
        wf,
        "parser_llm",
        SimpleNamespace(
            invoke=lambda msgs: SimpleNamespace(intent="nota_adicionar", slots=["texto=follow-up"])
        ),
    )
    # Stub do planejador: adiciona uma tarefa a executar no mesmo turno
    monkeypatch.setattr(
        wf,
        "plan_llm",
        SimpleNamespace(
            invoke=lambda msgs: SimpleNamespace(
                actions=[SimpleNamespace(intent="tarefa_criar", slots={"titulo": "ligar amanhã"})]

            )
        ),
    )

    # Stub das tools (evita acesso a DB): nota e tarefa retornam sucesso imediato
    monkeypatch.setattr(tools, "add_note_to_lead", _FakeTool("add_note_to_lead", "note_id", "N-1"))
    monkeypatch.setattr(tools, "create_task", _FakeTool("create_task", "tarefa_id", "T-1"))

    # Stub do finalizador LLM para evitar chamada externa
    monkeypatch.setattr(wf, "finalizer_model", SimpleNamespace(invoke=lambda msgs: SimpleNamespace(content="ok")))

    # Injeta um lead atual no estado inicial para evitar fluxo de criação/resolve
    lead_atual = {"lead_id": "L-1", "nome": "Lead Teste", "email": None, "empresa": "ACME"}

    result = wf.compiled_graph.invoke(
        {"messages": [HumanMessage(content="adicionar nota e criar tarefa amanhã")], "lead_atual": lead_atual},
        config={"configurable": {"thread_id": "quick:multi:intents:1"}},
    )

    msgs = result.get("messages", [])
    ctx = result.get("context") or {}

    assert _has_ai_text(msgs, "nota registrada"), "Não registrou a nota (stub)"
    assert _has_ai_text(msgs, "tarefa criada"), "Não criou a tarefa (stub)"
    assert not ctx.get("pending_actions"), "A fila de pendências deveria estar vazia"
