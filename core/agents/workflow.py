"""Workflow agent with multi-intent planning.

Based on ai-agent-sales-main approach with intent classification,
planning, and routing.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Annotated
from types import SimpleNamespace

import json
import re

from dotenv import load_dotenv
from langchain_core.messages import (
    AnyMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, ConfigDict

from core.agents.base import BaseAgent


load_dotenv()


# Intent types
IntentLiteral = Literal[
    "conversa_geral",
    "rag_search",
    "web_search",
    "custom_action",
]

# Required slots for each intent
REQUIRED_SLOTS: Dict[str, List[str]] = {
    "rag_search": ["query"],
    "web_search": ["query"],
    "conversa_geral": [],
    "custom_action": [],
}


class ParserResponse(BaseModel):
    """Parser response for intent classification."""
    intent: IntentLiteral
    slots: List[str]
    model_config = ConfigDict(extra='forbid')


class PlanAction(BaseModel):
    """Represents an atomic action extracted from user message."""
    intent: IntentLiteral
    slots: List[str] = []
    model_config = ConfigDict(extra='forbid')


class AgentState(TypedDict, total=False):
    """State for workflow agent."""
    messages: Annotated[List[AnyMessage], add_messages]
    intent: IntentLiteral
    slots: Dict[str, Any]
    errors: List[str]
    context: Dict[str, Any]
    pending_actions: List[Dict[str, Any]]


def normalize_json_like(s: str) -> str:
    """Normalize common JSON variants returned by LLMs."""
    t = (s or "").strip()
    if t.startswith("actions="):
        t = "{" + t.replace("actions=", "\"actions\":", 1) + "}"
    if t.startswith("[") and t.endswith("]"):
        t = "{\"actions\": " + t + "}"
    t = re.sub(r"([,{]\s*)([A-Za-z_][A-Za-z0-9_\-]*)\s*:", r'\1"\2":', t)
    t = t.replace("'", '"')
    return t


def parse_plan_actions_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract actions list from LLM text response."""
    raw = (text or "").strip()
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\bactions\b\s*:\s*\[.*\]\s*\}", raw, re.DOTALL)
        if m:
            snippet = normalize_json_like(m.group(0))
            try:
                obj = json.loads(snippet)
            except Exception:
                obj = None
        else:
            try:
                obj = json.loads(normalize_json_like(raw))
            except Exception:
                obj = None
    
    if not isinstance(obj, dict):
        return []
    
    actions = obj.get("actions")
    if not isinstance(actions, list):
        return []
    
    cleaned: List[Dict[str, Any]] = []
    for it in actions:
        if not isinstance(it, dict):
            continue
        intent = it.get("intent")
        slots = it.get("slots", [])
        if not isinstance(slots, list):
            if isinstance(slots, dict):
                try:
                    slots = [json.dumps(slots, ensure_ascii=False)]
                except Exception:
                    slots = []
            else:
                slots = []
        if intent:
            cleaned.append({"intent": intent, "slots": slots})
    
    return cleaned


def slots_strings_to_dict(slots_strings: List[str]) -> Dict[str, Any]:
    """Convert slots strings list to Python dict."""
    import json as _json
    out: Dict[str, Any] = {}
    for s in slots_strings or []:
        if not isinstance(s, str):
            continue
        txt = s.strip()
        if txt.startswith("{") and txt.endswith("}"):
            txt2 = re.sub(r"([,{]\s*)([A-Za-z_][A-Za-z0-9_\-]*)\s*:", r'\1"\2":', txt)
            txt2 = txt2.replace("'", '"')
            try:
                data = _json.loads(txt2)
                if isinstance(data, dict):
                    out.update({k: v for k, v in data.items()})
                    continue
            except Exception:
                pass
        if "=" in txt:
            k, v = txt.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def extract_text_content(msg: BaseMessage) -> str:
    """Extract text content from message."""
    if hasattr(msg, "content"):
        content = msg.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle list of content blocks
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            return " ".join(texts)
    return ""


# Prompts
PARSER_SYSTEM_PROMPT = """Você é um assistente especializado em classificar intenções e extrair informações.

Sua tarefa é:
1. Identificar a intenção do usuário
2. Extrair os slots (parâmetros) mencionados na mensagem

## Intenções e Slots:

- conversa_geral: Conversa geral sem ação específica
- rag_search: Busca na knowledge base (requer: query)
- web_search: Busca na web (requer: query)
- custom_action: Ação customizada

## Instruções:
- Extraia APENAS os slots mencionados explicitamente.
- Use os nomes exatos dos slots listados acima.
- Mantenha os valores no formato original.

Exemplo:
Mensagem: "Busque informações sobre Python"
Resposta: intent="rag_search", slots=["query=Python"]
"""

PLAN_SYSTEM_PROMPT = """Você é um planejador de ações. Leia uma mensagem e extraia TODAS as ações pedidas.

Intents válidos: conversa_geral, rag_search, web_search, custom_action.

Formato da saída (obrigatório):
- Responda SOMENTE com um JSON: {"actions": [{"intent": "...", "slots": ["{chave: 'valor'}"]}, ...]}

Regras:
- Extraia todas as ações mencionadas.
- Ordene logicamente (buscar antes de processar).
- Não invente valores; extraia apenas o explícito.
"""


class WorkflowAgent(BaseAgent):
    """Workflow agent with multi-intent planning and routing.
    
    Features:
    - Intent classification
    - Multi-intent planning
    - Dynamic routing to specialized handlers
    - State management
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        tools: Optional[List] = None,
        enable_planning: bool = True,
        **kwargs
    ):
        """Initialize workflow agent.
        
        Args:
            model_name: Model identifier
            tools: List of tools
            enable_planning: Enable multi-intent planning
        """
        model = ChatOpenAI(model=model_name, temperature=0.2)
        super().__init__(
            model=model,
            tools=tools or [],
            name="WorkflowAgent"
        )
        self.enable_planning = enable_planning
        self.parser_llm = model.with_structured_output(ParserResponse)
        self.planner_model = ChatOpenAI(model=model_name, temperature=0.3)
        self._graph = None
    
    def create_graph(self):
        """Create workflow graph."""
        if self._graph is None:
            graph = StateGraph(AgentState)
            
            # Add nodes
            graph.add_node("parse_intent", self._parse_intent)
            if self.enable_planning:
                graph.add_node("plan_actions", self._plan_actions)
            graph.add_node("router", self._router)
            graph.add_node("execute_action", self._execute_action)
            graph.add_node("respond", self._respond)
            
            # Add edges
            graph.add_edge(START, "parse_intent")
            if self.enable_planning:
                graph.add_edge("parse_intent", "plan_actions")
                graph.add_edge("plan_actions", "router")
            else:
                graph.add_edge("parse_intent", "router")
            graph.add_conditional_edges(
                "router",
                self._should_continue,
                {
                    "continue": "execute_action",
                    "done": "respond"
                }
            )
            graph.add_edge("execute_action", "router")
            graph.add_edge("respond", END)
            
            self._graph = graph.compile()
        
        return self._graph
    
    def _parse_intent(self, state: AgentState) -> AgentState:
        """Parse user intent from messages."""
        messages = state.get("messages", [])
        parsed = self.parser_llm.invoke([
            SystemMessage(content=PARSER_SYSTEM_PROMPT),
            *messages
        ])
        
        slots_dict = {}
        for slot_str in parsed.slots:
            if "=" in slot_str:
                name, value = slot_str.split("=", 1)
                slots_dict[name.strip()] = value.strip()
        
        return {
            "intent": parsed.intent,
            "slots": slots_dict
        }
    
    def _plan_actions(self, state: AgentState) -> AgentState:
        """Plan multiple actions from user message."""
        messages = state.get("messages", [])
        context = state.get("context", {})
        
        try:
            plan_text = self.planner_model.invoke([
                SystemMessage(content=PLAN_SYSTEM_PROMPT),
                *messages
            ]).content
            
            actions = parse_plan_actions_from_text(plan_text)
            
            pending = []
            for action in actions:
                intent_a = action.get("intent")
                slots_a = slots_strings_to_dict(action.get("slots", []))
                pending.append({"intent": intent_a, "slots": slots_a})
            
            context["pending_actions"] = pending
        except Exception as e:
            context["planning_error"] = str(e)
        
        return {"context": context}
    
    def _router(self, state: AgentState) -> AgentState:
        """Route to appropriate handler."""
        context = state.get("context", {})
        pending = context.get("pending_actions", [])
        
        if pending:
            # Execute next pending action
            action = pending.pop(0)
            context["pending_actions"] = pending
            return {
                "context": context,
                "intent": action.get("intent"),
                "slots": action.get("slots", {})
            }
        
        # Use current intent
        return {}
    
    def _should_continue(self, state: AgentState) -> str:
        """Decide if should continue or finish."""
        context = state.get("context", {})
        pending = context.get("pending_actions", [])
        
        if pending:
            return "continue"
        return "done"
    
    def _execute_action(self, state: AgentState) -> AgentState:
        """Execute the current action."""
        intent = state.get("intent", "conversa_geral")
        slots = state.get("slots", {})
        
        # Simple execution - can be extended with specialized handlers
        if intent == "rag_search":
            # RAG search would be handled by tool
            pass
        elif intent == "web_search":
            # Web search would be handled by tool
            pass
        
        return {}
    
    def _respond(self, state: AgentState) -> AgentState:
        """Generate final response."""
        messages = state.get("messages", [])
        last_user = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user = extract_text_content(msg)
                break
        
        # Simple response - can be enhanced with LLM
        response_text = f"Processei sua solicitação: {last_user or 'N/A'}"
        
        return {
            "messages": [AIMessage(content=response_text)]
        }
    
    def invoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke workflow agent."""
        graph = self.create_graph()
        return graph.invoke(input, config or {})
    
    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke workflow agent asynchronously."""
        graph = self.create_graph()
        return await graph.ainvoke(input, config or {})

