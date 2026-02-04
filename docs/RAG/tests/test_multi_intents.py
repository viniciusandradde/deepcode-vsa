import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage, ToolMessage
from app.agent.workflow import compiled_graph

# Marca todos os testes deste módulo como lentos (chamam LLM/DB)
pytestmark = pytest.mark.slow


def _contains_ai_text(messages, needle: str) -> bool:
    needle = (needle or "").lower()
    for m in messages:
        if isinstance(m, AIMessage):
            content = m.content
            if isinstance(content, str) and needle in content.lower():
                return True
            if isinstance(content, list):
                # extrai blocos de texto
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        if needle in (b.get("text") or "").lower():
                            return True
    return False


def _has_tool_call(messages, name: str) -> bool:
    for m in messages:
        if isinstance(m, ToolMessage) and getattr(m, "name", None) == name:
            return True
    return False


def test_multi_intents_plan_executes_queue():
    cfg = {"configurable": {"thread_id": "test:multi:intents:1"}}
    prompt = (
        "Cadastre o Lennon, adicione a nota follow-up e crie tarefa para amanhã; "
        "já rascunhe a proposta ACME."
    )
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)

    # Deve ter um lead atual consolidado
    lead = result.get("lead_atual")
    assert lead and lead.get("lead_id"), "Lead não foi consolidado no estado"

    # A fila de pendências deve estar vazia (consumida)
    ctx = result.get("context") or {}
    assert not ctx.get("pending_actions"), "Fila de pendências não esvaziada"

    messages = result.get("messages", [])
    # Pelo menos uma ação derivada deve aparecer (nota OU proposta OU tarefa)
    assert (
        _contains_ai_text(messages, "nota registrada")
        or _contains_ai_text(messages, "tarefa criada")
        or _has_tool_call(messages, "rascunhar_proposta")
    ), "Execução de ações derivadas não evidenciada"


def test_lead_and_note_only():
    cfg = {"configurable": {"thread_id": "test:multi:intents:2"}}
    prompt = "Cadastre o João e anote ligar às 9h."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    ctx = result.get("context") or {}
    assert not ctx.get("pending_actions"), "Fila não esvaziada"
    assert _contains_ai_text(result.get("messages", []), "nota registrada")


def test_lead_note_task():
    cfg = {"configurable": {"thread_id": "test:multi:intents:3"}}
    prompt = "Cadastre a Maria, adicione a nota retorno e crie tarefa para hoje."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    ctx = result.get("context") or {}
    assert not ctx.get("pending_actions"), "Fila não esvaziada"
    assert _contains_ai_text(msgs, "nota registrada") or _contains_ai_text(msgs, "tarefa criada")


def test_lead_and_proposal():
    cfg = {"configurable": {"thread_id": "test:multi:intents:4"}}
    prompt = "Cadastre o Paulo e já rascunhe a proposta ACME."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    assert _has_tool_call(msgs, "rascunhar_proposta") or _contains_ai_text(msgs, "proposta")


def test_note_task_proposal_variation():
    cfg = {"configurable": {"thread_id": "test:multi:intents:5"}}
    prompt = "Cadastre a Clara; nota: follow-up; crie tarefa ligação; rascunhe a proposta Onboarding."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    ctx = result.get("context") or {}
    assert not ctx.get("pending_actions"), "Fila não esvaziada"
    assert (
        _contains_ai_text(msgs, "nota registrada")
        or _contains_ai_text(msgs, "tarefa criada")
        or _has_tool_call(msgs, "rascunhar_proposta")
    )


def test_existing_lead_then_batch_actions():
    cfg = {"configurable": {"thread_id": "test:multi:intents:6"}}
    # Passo 1: cria lead
    compiled_graph.invoke({"messages": [HumanMessage(content="Cadastre o Dante da empresa Alpha")]}, config=cfg)
    # Passo 2: ações derivadas
    prompt = "Anote retorno e rascunhe a proposta Alpha."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    assert _contains_ai_text(msgs, "nota registrada") or _has_tool_call(msgs, "rascunhar_proposta")


def test_delimiters_semicolon_and_e_variations():
    cfg = {"configurable": {"thread_id": "test:multi:intents:7"}}
    prompt = "Cadastre o Rick; nota: call de alinhamento; e crie tarefa amanhã; já rascunhe a proposta Kickoff."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    ctx = result.get("context") or {}
    assert not ctx.get("pending_actions"), "Fila não esvaziada"
    assert (
        _contains_ai_text(msgs, "nota registrada")
        or _contains_ai_text(msgs, "tarefa criada")
        or _has_tool_call(msgs, "rascunhar_proposta")
    )


def test_task_today_keyword():
    cfg = {"configurable": {"thread_id": "test:multi:intents:8"}}
    prompt = "Cadastre o Nestor e crie tarefa reunião hoje."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    assert _contains_ai_text(msgs, "tarefa criada") or _has_tool_call(msgs, "criar_tarefa")


def test_only_note_after_lead_in_same_turn():
    cfg = {"configurable": {"thread_id": "test:multi:intents:9"}}
    prompt = "Cadastre o Obi-Wan e deixe uma nota follow-up."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    assert _contains_ai_text(result.get("messages", []), "nota registrada")


def test_proposal_name_extraction():
    cfg = {"configurable": {"thread_id": "test:multi:intents:10"}}
    prompt = "Cadastre o Qui-Gon, rascunhe a proposta Onboarding."
    result = compiled_graph.invoke({"messages": [HumanMessage(content=prompt)]}, config=cfg)
    msgs = result.get("messages", [])
    assert _has_tool_call(msgs, "rascunhar_proposta") or _contains_ai_text(msgs, "proposta")
