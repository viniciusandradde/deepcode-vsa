"""Unified Agent combining SimpleAgent, VSAAgent, and WorkflowAgent.

This agent orchestrates:
- Router: Intent classification (from WorkflowAgent)
- Classifier: ITIL categorization (from VSAAgent)
- Planner: Multi-step action planning
- Confirmer: User confirmation for write operations
- Executor: Tool execution (from SimpleAgent)
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
from enum import Enum

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from core.agents.base import BaseAgent


load_dotenv()

DEFAULT_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}


def dbg(*args):
    """Debug logging helper."""
    if DEBUG_AGENT_LOGS:
        try:
            print("[UnifiedAgent]", *args, flush=True)
        except Exception:
            pass


# --- Enums ---

class Intent(str, Enum):
    """User intent categories."""
    CONVERSA_GERAL = "conversa_geral"
    IT_REQUEST = "it_request"
    MULTI_ACTION = "multi_action"
    WEB_SEARCH = "web_search"


class TaskCategory(str, Enum):
    """ITIL Task Categories."""
    INCIDENTE = "incidente"
    PROBLEMA = "problema"
    MUDANCA = "mudanca"
    REQUISICAO = "requisicao"
    CONVERSA = "conversa"


class Priority(str, Enum):
    """Priority levels."""
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"


# --- State ---

class UnifiedAgentState(TypedDict):
    """Unified agent state combining all agent capabilities."""
    # Base messages
    messages: Annotated[List[AnyMessage], add_messages]
    
    # Router (from WorkflowAgent)
    intent: Optional[str]
    pending_actions: List[Dict[str, Any]]
    
    # Classifier (from VSAAgent)
    task_category: Optional[str]
    priority: Optional[str]
    gut_score: Optional[int]
    gut_details: Optional[Dict[str, int]]  # {gravidade, urgencia, tendencia}
    
    # Planner
    plan: Optional[List[Dict[str, Any]]]
    current_step: int
    
    # Confirmer
    pending_confirmation: Optional[Dict[str, Any]]
    confirmed_actions: List[str]
    
    # Executor
    tool_results: List[Dict[str, Any]]
    
    # Control
    should_continue: bool
    error: Optional[str]
    dry_run: bool


def create_initial_state(user_message: str = "", dry_run: bool = False) -> UnifiedAgentState:
    """Create initial state for the agent."""
    return {
        "messages": [HumanMessage(content=user_message)] if user_message else [],
        "intent": None,
        "pending_actions": [],
        "task_category": None,
        "priority": None,
        "gut_score": None,
        "gut_details": None,
        "plan": None,
        "current_step": 0,
        "pending_confirmation": None,
        "confirmed_actions": [],
        "tool_results": [],
        "should_continue": True,
        "error": None,
        "dry_run": dry_run,
    }


# --- Prompts ---

ROUTER_SYSTEM_PROMPT = """Você é um roteador de intenções. Classifique a mensagem do usuário em UMA das categorias:

- conversa_geral: Saudações, perguntas genéricas, conversas informais
- it_request: Solicitações de TI (tickets, alertas, monitoramento, GLPI, Zabbix)
- multi_action: Múltiplas ações em uma mensagem ("liste tickets e depois crie um alerta")
- web_search: Busca de informações na internet

Responda APENAS com a categoria, sem explicações."""

CLASSIFIER_SYSTEM_PROMPT = """Você é um Especialista em Gestão de Serviços de TI (ITIL).
Classifique a solicitação do usuário em UMA categoria ITIL:

- INCIDENTE: Interrupção inesperada de serviço ou degradação
- PROBLEMA: Causa raiz de incidentes recorrentes
- MUDANÇA: Alteração planejada em sistemas/infraestrutura
- REQUISIÇÃO: Solicitação de serviço padrão
- CONVERSA: Conversa geral, não relacionada a TI

Responda em JSON:
{
    "categoria": "INCIDENTE|PROBLEMA|MUDANÇA|REQUISIÇÃO|CONVERSA",
    "gravidade": 1-5,
    "urgencia": 1-5,
    "tendencia": 1-5,
    "justificativa": "breve explicação"
}"""

PLANNER_SYSTEM_PROMPT = """Você é um planejador de ações de TI.
Dado o contexto e a categoria ITIL, crie um plano de ação.

Cada ação deve ter:
- tool: nome da ferramenta (glpi_get_tickets, zabbix_get_alerts, etc)
- params: parâmetros da ferramenta
- requires_confirm: true se modifica dados (CREATE, UPDATE, DELETE)
- description: descrição da ação em português

Responda em JSON:
{
    "plan": [
        {"tool": "...", "params": {...}, "requires_confirm": false, "description": "..."},
        ...
    ]
}"""


# --- Agent Class ---

class UnifiedAgent(BaseAgent):
    """Unified agent combining SimpleAgent, VSAAgent, and WorkflowAgent capabilities.
    
    Features:
    - Intent routing (conversa, IT, multi-action, search)
    - ITIL classification (Incidente, Problema, Mudança, Requisição)
    - GUT prioritization (Gravidade, Urgência, Tendência)
    - Multi-step planning with confirmations
    - Tool execution with streaming
    """
    
    def __init__(
        self,
        model_name: str = "google/gemini-2.5-flash",
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        enable_itil: bool = True,
        enable_planning: bool = True,
        enable_confirmation: bool = True,
        checkpointer: Optional[Any] = None,
        openrouter_api_key: Optional[str] = None,
        openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
        temperature: float = 0.2,
        fast_model_name: Optional[str] = None,
    ):
        """Initialize unified agent.
        
        Args:
            model_name: Model for executor (must support tools when tools are used).
            tools: List of tools available to the agent.
            system_prompt: Custom system prompt (optional).
            enable_itil: Enable ITIL classification.
            enable_planning: Enable multi-step planning.
            enable_confirmation: Enable confirmation for write operations.
            checkpointer: LangGraph checkpointer for persistence.
            openrouter_api_key: OpenRouter API key.
            openrouter_base_url: OpenRouter base URL.
            temperature: Model temperature.
            fast_model_name: Optional cheaper model for router/classifier (tiered).
        """
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Defina OPENROUTER_API_KEY para inicializar o agente.")

        # Default system prompt
        if system_prompt is None:
            data_atual = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")
            system_prompt = (
                f"Você é o VSA (Virtual Support Agent), um assistente de TI especializado. "
                f"Hoje é {data_atual} (fuso de São Paulo). "
                "Você pode ajudar com tickets GLPI, alertas Zabbix, issues Linear e buscas na web. "
                "Seja direto, profissional e proativo nas soluções."
            )

        model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base=openrouter_base_url,
        )

        # Tiered: cheap model for router/classifier when provided
        self._fast_model = None
        if fast_model_name and fast_model_name != model_name:
            self._fast_model = ChatOpenAI(
                model=fast_model_name,
                temperature=0.1,
                openai_api_key=api_key,
                openai_api_base=openrouter_base_url,
            )
            dbg(f"Tiered: fast_model={fast_model_name} for router/classifier")

        super().__init__(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            name="UnifiedAgent"
        )

        self.model_name = model_name
        self.enable_itil = enable_itil
        self.enable_planning = enable_planning
        self.enable_confirmation = enable_confirmation
        self.checkpointer = checkpointer
        self.openrouter_api_key = api_key
        self.openrouter_base_url = openrouter_base_url
        self.temperature = temperature
        self._graph = None
    
    def create_graph(self, checkpointer=None):
        """Create the unified agent graph.
        
        Returns:
            Compiled LangGraph graph
        """
        if self._graph is not None:
            return self._graph
        
        checkpointer = checkpointer or self.checkpointer
        
        # Build graph
        builder = StateGraph(UnifiedAgentState)
        
        # Add nodes based on configuration
        builder.add_node("executor", self._executor_node)
        builder.add_node("responder", self._responder_node)
        
        # Add tool node if tools available
        if self.tools:
            tool_node = ToolNode(self.tools)
            builder.add_node("tools", tool_node)
        
        # Simplified graph when ITIL is disabled (no router/classifier)
        if not self.enable_itil:
            # Direct path: START → executor → (tools loop) → responder → END
            builder.add_edge(START, "executor")
        else:
            # Full ITIL path with router and classifier
            builder.add_node("router", self._router_node)
            builder.add_node("classifier", self._classifier_node)
            builder.add_node("planner", self._planner_node)
            
            builder.add_edge(START, "router")
            
            # Router decides next step
            builder.add_conditional_edges(
                "router",
                self._route_after_router,
                {
                    "classifier": "classifier",
                    "executor": "executor",
                    "responder": "responder",
                }
            )
            
            # Classifier → Planner (if enabled) or Executor
            if self.enable_planning:
                builder.add_edge("classifier", "planner")
                builder.add_edge("planner", "executor")
            else:
                builder.add_edge("classifier", "executor")
        
        # Executor → Tools (if tools called) or Responder
        builder.add_conditional_edges(
            "executor",
            self._route_after_executor,
            {
                "tools": "tools",
                "responder": "responder",
            }
        )
        
        # Tools → Executor (loop back for more tool calls)
        if self.tools:
            builder.add_edge("tools", "executor")
        
        # Responder → END
        builder.add_edge("responder", END)
        
        # Compile
        self._graph = builder.compile(checkpointer=checkpointer)
        return self._graph
    
    # --- Node Implementations ---
    
    def _router_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
        """Route user message to appropriate handler."""
        dbg("Router node executing...")
        
        messages = state.get("messages", [])
        if not messages:
            return {"intent": Intent.CONVERSA_GERAL.value, "error": "No messages"}
        
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {"intent": Intent.CONVERSA_GERAL.value}
        
        user_content = last_message.content
        dbg(f"Routing message: {user_content[:100]}...")
        
        # Use LLM to classify intent (tiered: fast model if available)
        model = self._fast_model if self._fast_model else self.model
        try:
            response = model.invoke([
                SystemMessage(content=ROUTER_SYSTEM_PROMPT),
                HumanMessage(content=user_content)
            ])
            
            intent_text = response.content.strip().lower()
            
            # Map to enum
            if "it_request" in intent_text or "it" in intent_text:
                intent = Intent.IT_REQUEST.value
            elif "multi" in intent_text:
                intent = Intent.MULTI_ACTION.value
            elif "web" in intent_text or "search" in intent_text:
                intent = Intent.WEB_SEARCH.value
            else:
                intent = Intent.CONVERSA_GERAL.value
            
            dbg(f"Classified intent: {intent}")
            return {"intent": intent}
            
        except Exception as e:
            dbg(f"Router error: {e}")
            return {"intent": Intent.CONVERSA_GERAL.value, "error": str(e)}
    
    def _classifier_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
        """Classify request using ITIL methodology."""
        dbg("Classifier node executing...")
        
        if not self.enable_itil:
            return {}
        
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {}
        
        user_content = last_message.content

        # Tiered: fast model if available
        model = self._fast_model if self._fast_model else self.model
        try:
            response = model.invoke([
                SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
                HumanMessage(content=user_content)
            ])
            
            # Parse JSON response
            import json
            content = response.content.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            
            categoria = data.get("categoria", "CONVERSA").upper()
            gravidade = int(data.get("gravidade", 3))
            urgencia = int(data.get("urgencia", 3))
            tendencia = int(data.get("tendencia", 3))
            gut_score = gravidade * urgencia * tendencia
            
            # Map to priority
            if gut_score >= 64:
                priority = Priority.CRITICO.value
            elif gut_score >= 27:
                priority = Priority.ALTO.value
            elif gut_score >= 8:
                priority = Priority.MEDIO.value
            else:
                priority = Priority.BAIXO.value
            
            dbg(f"ITIL: {categoria}, GUT: {gut_score}, Priority: {priority}")
            
            return {
                "task_category": categoria.lower(),
                "priority": priority,
                "gut_score": gut_score,
                "gut_details": {
                    "gravidade": gravidade,
                    "urgencia": urgencia,
                    "tendencia": tendencia,
                },
            }
            
        except Exception as e:
            dbg(f"Classifier error: {e}")
            return {"task_category": TaskCategory.CONVERSA.value}
    
    def _planner_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
        """Plan actions based on classification."""
        dbg("Planner node executing...")
        
        if not self.enable_planning:
            return {}
        
        # For now, return empty plan - will be enhanced
        return {"plan": [], "current_step": 0}
    
    def _try_format_tool_results_as_report(self, messages: List[AnyMessage]) -> Optional[str]:
        """If last messages are tool results from GLPI/Zabbix/Linear, format with core.reports (no LLM)."""
        if not messages:
            return None
        last = messages[-1]
        if not isinstance(last, ToolMessage):
            return None
        # Find AIMessage with tool_calls that preceded these ToolMessages
        tool_calls_by_id = {}
        for m in reversed(messages):
            if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
                for tc in m.tool_calls:
                    tool_calls_by_id[tc.get("id")] = tc.get("name", "")
                break
        report_tools = {"glpi_get_tickets", "zabbix_get_alerts", "linear_get_issues"}
        glpi_data = None
        zabbix_data = None
        linear_data = None
        for m in messages:
            if isinstance(m, ToolMessage):
                name = tool_calls_by_id.get(getattr(m, "tool_call_id", ""), "")
                if name not in report_tools:
                    return None
                try:
                    import json
                    content = m.content if isinstance(m.content, str) else str(m.content)
                    data = json.loads(content) if content.strip().startswith("{") else None
                    if not data:
                        return None
                    if name == "glpi_get_tickets":
                        glpi_data = data
                    elif name == "zabbix_get_alerts":
                        zabbix_data = data
                    elif name == "linear_get_issues":
                        linear_data = data
                except Exception:
                    return None
        if not glpi_data and not zabbix_data and not linear_data:
            return None
        try:
            from core.config import get_settings
            from core.reports import format_glpi_report, format_zabbix_report, format_linear_report
            from core.reports.dashboard import format_dashboard_report
            settings = get_settings()
            glpi_base_url = settings.glpi.base_url if settings.glpi.enabled else None
            zabbix_base_url = settings.zabbix.base_url if settings.zabbix.enabled else None
            parts = []
            if glpi_data:
                parts.append(format_glpi_report(glpi_data, glpi_base_url=glpi_base_url))
            if zabbix_data:
                parts.append(format_zabbix_report(zabbix_data, zabbix_base_url=zabbix_base_url))
            if linear_data:
                parts.append(format_linear_report(linear_data))
            if len(parts) == 1:
                return parts[0]
            return format_dashboard_report(
                glpi_data=glpi_data,
                zabbix_data=zabbix_data,
                linear_data=linear_data,
                glpi_base_url=glpi_base_url,
                zabbix_base_url=zabbix_base_url,
            )
        except Exception as e:
            dbg(f"Report format failed: {e}")
            return None

    def _executor_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
        """Execute actions using tools."""
        dbg("Executor node executing...")

        messages = state.get("messages", [])

        # If we have ToolMessages from report tools, format with code (no LLM)
        report_md = self._try_format_tool_results_as_report(messages)
        if report_md:
            dbg("Using report formatter (no LLM) for tool results")
            return {"messages": [AIMessage(content=report_md)]}

        # Build context message with ITIL info
        context_parts = []
        if state.get("task_category"):
            context_parts.append(f"Categoria ITIL: {state['task_category'].upper()}")
        if state.get("priority"):
            context_parts.append(f"Prioridade: {state['priority'].upper()}")
        if state.get("gut_score"):
            context_parts.append(f"GUT Score: {state['gut_score']}")

        # Bind tools to model
        if self.tools:
            model_with_tools = self.model.bind_tools(self.tools)
        else:
            model_with_tools = self.model

        # Prepare messages with system prompt
        full_messages = [SystemMessage(content=self.system_prompt)]
        if context_parts:
            full_messages.append(SystemMessage(content="\n".join(context_parts)))
        full_messages.extend(messages)

        try:
            response = model_with_tools.invoke(full_messages)
            dbg(f"Executor response: {response.content[:100] if response.content else 'tool_calls'}...")
            return {"messages": [response]}
        except Exception as e:
            dbg(f"Executor error: {e}")
            return {"error": str(e)}
    
    def _responder_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
        """Generate final response."""
        dbg("Responder node executing...")
        # Response already in messages from executor
        return {"should_continue": False}
    
    # --- Routing Functions ---
    
    def _route_after_router(self, state: UnifiedAgentState) -> str:
        """Decide where to go after routing."""
        intent = state.get("intent", Intent.CONVERSA_GERAL.value)
        
        if intent == Intent.CONVERSA_GERAL.value:
            return "executor"  # Direct to simple response
        elif intent in [Intent.IT_REQUEST.value, Intent.MULTI_ACTION.value]:
            if self.enable_itil:
                return "classifier"
            return "executor"
        else:
            return "executor"
    
    def _route_after_executor(self, state: UnifiedAgentState) -> str:
        """Decide where to go after execution."""
        messages = state.get("messages", [])
        
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
        
        return "responder"
    
    # --- Public Interface ---
    
    def invoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke agent synchronously."""
        graph = self.create_graph()
        
        # Ensure state has required fields
        if "messages" not in input:
            input = create_initial_state()
            input["messages"] = [HumanMessage(content=input.get("content", ""))]
        
        return graph.invoke(input, config or {})
    
    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke agent asynchronously."""
        graph = self.create_graph()
        
        if "messages" not in input:
            input = create_initial_state()
            input["messages"] = [HumanMessage(content=input.get("content", ""))]
        
        return await graph.ainvoke(input, config or {})
    
    async def astream(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None, **kwargs):
        """Stream agent responses asynchronously."""
        graph = self.create_graph()
        
        if "messages" not in input:
            input = create_initial_state()
            input["messages"] = [HumanMessage(content=input.get("content", ""))]
        
        async for chunk in graph.astream(input, config or {}, **kwargs):
            yield chunk


# --- Factory Function ---

def create_unified_agent(
    model_name: str = "google/gemini-2.5-flash",
    tools: Optional[List[BaseTool]] = None,
    system_prompt: Optional[str] = None,
    enable_itil: bool = True,
    enable_planning: bool = True,
    enable_confirmation: bool = True,
    checkpointer: Optional[Any] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
    temperature: float = 0.2,
) -> UnifiedAgent:
    """Factory function to create a unified agent.
    
    Args:
        model_name: Model identifier
        tools: List of tools
        system_prompt: Custom system prompt
        enable_itil: Enable ITIL classification
        enable_planning: Enable multi-step planning
        enable_confirmation: Enable confirmation for writes
        checkpointer: LangGraph checkpointer
        openrouter_api_key: OpenRouter API key
        openrouter_base_url: OpenRouter base URL
        temperature: Model temperature
        
    Returns:
        Configured UnifiedAgent instance
    """
    return UnifiedAgent(
        model_name=model_name,
        tools=tools,
        system_prompt=system_prompt,
        enable_itil=enable_itil,
        enable_planning=enable_planning,
        enable_confirmation=enable_confirmation,
        checkpointer=checkpointer,
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=openrouter_base_url,
        temperature=temperature,
    )
