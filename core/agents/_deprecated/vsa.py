"""VSA Agent Implementation.

Ported from legacy CLI implementation.
Implements ITIL/GUT methodology using LangGraph.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langchain.tools import BaseTool

from core.agents.base import BaseAgent
from core.tools.glpi import glpi_create_ticket, glpi_get_tickets, glpi_get_ticket_details
from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host

# --- State Definition ---

class Methodology(str, Enum):
    ITIL = "itil"
    GUT = "gut"
    RCA = "rca"
    W5H2 = "5w2h"
    PDCA = "pdca"

class TaskCategory(str, Enum):
    """ITIL Task Categories (Portuguese BR)"""
    INCIDENTE = "incidente"
    PROBLEMA = "problema"
    MUDANCA = "mudanca"
    REQUISICAO = "requisicao"
    CONVERSA = "conversa"

class Priority(str, Enum):
    """Priority Levels (Portuguese BR)"""
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"

class VSAAgentState(TypedDict):
    """VSA Agent State."""
    messages: Annotated[List[AnyMessage], add_messages]
    user_request: str
    plan: Optional[List[str]]
    current_step: int
    methodology: Optional[Methodology]
    task_category: Optional[TaskCategory]
    priority: Optional[Priority]
    gut_score: Optional[int]
    tool_results: List[dict]
    should_continue: bool
    needs_replan: bool
    error: Optional[str]
    dry_run: bool
    # Contexts
    glpi_context: Optional[dict]
    zabbix_context: Optional[dict]

def create_initial_state(user_request: str, dry_run: bool = True) -> VSAAgentState:
    return {
        "messages": [],
        "user_request": user_request,
        "plan": None,
        "current_step": 0,
        "methodology": None,
        "task_category": None,
        "priority": None,
        "gut_score": None,
        "tool_results": [],
        "should_continue": True,
        "needs_replan": False,
        "error": None,
        "dry_run": dry_run,
        "glpi_context": None,
        "zabbix_context": None,
    }

# --- Prompts ---

CLASSIFIER_PROMPT = """Você é um Especialista em Gestão de Serviços de TI (ITIL).
Analise a solicitação do usuário e classifique nas categorias ITIL em português:
- INCIDENTE: Interrupção inesperada de serviço
- PROBLEMA: Causa raiz de incidentes
- MUDANÇA: Alteração controlada em serviços
- REQUISIÇÃO: Solicitação de serviço padrão
- CONVERSA: Interação geral sem demanda técnica

Estime também urgência/impacto para calcular o GUT score.
"""

PLANNER_PROMPT = """Crie um plano de ação passo-a-passo seguindo a metodologia ITIL.
Para CONVERSA, apenas responda normalmente.
Para INCIDENTE, inclua etapas de diagnóstico e resolução.
Para PROBLEMA, inclua análise de causa raiz (5 Porquês).
Para MUDANÇA, inclua avaliação de impacto e planejamento.
"""

# --- Agent Class ---

class VSAAgent(BaseAgent):
    """Virtual Support Agent specialized in IT Mgmt."""

    def __init__(
        self,
        model_name: str = "google/gemini-2.5-flash",
        tools: Optional[List[BaseTool]] = None,
        openrouter_api_key: Optional[str] = None
    ):
        # Default tools if none provided
        if tools is None:
            tools = [
                glpi_create_ticket, glpi_get_tickets, glpi_get_ticket_details,
                zabbix_get_alerts, zabbix_get_host
            ]

        # Init base (creates self.model)
        super().__init__(
            model=None, # Will use default created by BaseAgent or pass explicit
            tools=tools,
            name="VSAAgent",
            system_prompt=None # Use dynamic
        )
        # Re-init model with specific name if needed, BaseAgent creates ChatOpenAI
        # Actually BaseAgent takes 'model' instance. 
        # I should construct the model here.
        from langchain_openai import ChatOpenAI
        import os
        
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            temperature=0.2
        )
        
        self._graph = None

    def create_graph(self, checkpointer=None):
        if self._graph is None:
            workflow = StateGraph(VSAAgentState)

            # Nodes
            workflow.add_node("classifier", self._classifier_node)
            workflow.add_node("planner", self._planner_node)
            workflow.add_node("executor", self._executor_node)
            # workflow.add_node("reflector", self._reflector_node) # Future

            # Edges
            workflow.add_edge(START, "classifier")
            workflow.add_edge("classifier", "planner")
            workflow.add_edge("planner", "executor")
            
            # Conditional loop in executor
            workflow.add_conditional_edges(
                "executor",
                self._should_continue,
                {
                    "continue": "executor",
                    "end": END
                }
            )

            self._graph = workflow.compile(checkpointer=checkpointer)
        return self._graph

    # --- Node Implementations ---

    async def _classifier_node(self, state: VSAAgentState) -> dict:
        import logging
        from core.config import get_settings
        logger = logging.getLogger(__name__)
        settings = get_settings()
        
        try:
            request = state.get("user_request")
            if not request:
                messages = state.get("messages", [])
                request = messages[-1].content if messages else "N/A"
            
            # Use model for intelligent classification
            prompt = [
                SystemMessage(content=CLASSIFIER_PROMPT),
                HumanMessage(content=f"Análise esta solicitação: {request}")
            ]
            
            # Use the fast model for classification if configured, or default
            response = await self.model.ainvoke(prompt)
            content = response.content.upper()
            
            # Parse response - expecting CATEGORY: <CAT>, GUT: <SCORE>
            cat = TaskCategory.CHAT
            if "INCIDENT" in content: cat = TaskCategory.INCIDENT
            elif "PROBLEM" in content: cat = TaskCategory.PROBLEM
            elif "CHANGE" in content: cat = TaskCategory.CHANGE
            elif "REQUEST" in content: cat = TaskCategory.REQUEST
            
            # Extract GUT score if present
            gut = 27
            import re
            match = re.search(r"GUT:\s*(\d+)", content)
            if match:
                gut = int(match.group(1))
            
            logger.info(f"Intelligent Classification: Category={cat.value}, GUT={gut}")
                
            return {
                "task_category": cat,
                "gut_score": gut,
                "methodology": Methodology.ITIL,
                "messages": [AIMessage(content=f"📊 Inteligência VSA: Classificado como {cat.value.upper()} (GUT: {gut})")]
            }
        except Exception as e:
            logger.error(f"Error in intelligent classifier: {e}", exc_info=True)
            # Fallback to simple heuristic
            return {
                "task_category": TaskCategory.CHAT,
                "gut_score": 27,
                "messages": [AIMessage(content="⚠️ Falha no classificador IA, usando modo Chat fallback.")]
            }

    async def _planner_node(self, state: VSAAgentState) -> dict:
        cat = state.get("task_category")
        request = state.get("user_request")
        
        # Use LLM to create a real plan based on the request and category
        system_msg = f"{PLANNER_PROMPT}\nCategoria atual: {cat.value}"
        
        try:
            response = await self.model.ainvoke([
                SystemMessage(content=system_msg),
                HumanMessage(content=f"Crie um plano para: {request}")
            ])
            
            # Expecting a bulleted list or numbered list
            plan_content = response.content
            import re
            steps = re.findall(r"(?:^|\n)(?:\d+\.|\-)\s+(.+)", plan_content)
            
            if not steps:
                # Fallback plans based on category if LLM output is messy
                if cat == TaskCategory.CHAT:
                    steps = ["Responder ao usuário"]
                elif cat == TaskCategory.INCIDENT:
                    steps = ["Verificar estado atual", "Identificar causa raiz", "Consultar KB", "Propor solução"]
                else:
                    steps = ["Analisar detalhes", "Executar procedimento padrão"]
            
            return {
                "plan": steps,
                "current_step": 0,
                "messages": [AIMessage(content=f"📋 Plano de Ação Gerado:\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)]))]
            }
        except Exception as e:
            return {
                "plan": ["Processar solicitação"],
                "messages": [AIMessage(content="⚠️ Erro ao gerar plano detalhado, usando plano simplificado.")]
            }

    async def _executor_node(self, state: VSAAgentState) -> dict:
        plan = state.get("plan") or []
        step_idx = state.get("current_step", 0)
        
        if step_idx >= len(plan):
            return {"should_continue": False}
            
        step_name = plan[step_idx]
        cat = state.get("task_category")
        
        # Real Execution Logic using Tools
        if cat == TaskCategory.CHAT:
            # For pure chat, just use the model to respond
            response = await self.model.ainvoke(state["messages"])
            return {
                "current_step": len(plan),
                "should_continue": False,
                "messages": [AIMessage(content=response.content)]
            }
        
        # For ITIL categories, use tools if needed or analyze
        # The agent will Decide if it needs a tool for the current step
        # Using a simplified tool-calling loop here or direct tool execution
        
        result_content = f"Executando: {step_name}"
        
        # Logic to decide which tool to call based on step name or context
        # Porting Tool Logic:
        try:
            if "Zabbix" in step_name or "alerta" in step_name.lower():
                from core.tools.zabbix import zabbix_get_alerts
                alerts = await zabbix_get_alerts.ainvoke({})
                result_content = f"Consulta Zabbix: {alerts}"
            elif "GLPI" in step_name or "ticket" in step_name.lower():
                from core.tools.glpi import glpi_get_tickets
                tickets = await glpi_get_tickets.ainvoke({})
                result_content = f"Consulta GLPI: {tickets}"
            else:
                # Use LLM to perform the step using general knowledge or tool results so far
                response = await self.model.ainvoke([
                    SystemMessage(content=f"Você está executando este passo ITIL: {step_name}"),
                    HumanMessage(content=f"Contexto: {state['user_request']}\nResultados anteriores: {state['tool_results']}")
                ])
                result_content = response.content
        except Exception as e:
            result_content = f"Erro ao executar passo {step_name}: {str(e)}"

        return {
            "current_step": step_idx + 1,
            "tool_results": state.get("tool_results", []) + [{"step": step_name, "result": result_content}],
            "should_continue": True,
            "messages": [AIMessage(content=f"✅ {result_content}")]
        }

    def _should_continue(self, state: VSAAgentState) -> str:
        if state.get("should_continue") and state.get("current_step", 0) < len(state.get("plan") or []):
            return "continue"
        return "end"

    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke agent with state persistence support."""
        msgs = input.get("messages", [])
        last_content = msgs[-1].content if msgs else None
        req_text = input.get("user_request") or last_content or "No request"
        
        # Check for existing state in checkpointer
        initial_state = create_initial_state(
            user_request=req_text,
            dry_run=input.get("dry_run", True)
        )
        if "messages" in input:
            initial_state["messages"] = input["messages"]
            
        graph = self.create_graph(checkpointer=config.get("configurable", {}).get("checkpointer") if config else None)
        return await graph.ainvoke(initial_state, config or {})

    def invoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sync invoke adapter."""
        import asyncio
        import logging
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.ainvoke(input, config))

