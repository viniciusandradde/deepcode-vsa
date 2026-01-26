"""VSA Agent Graph construction.

Reference: .claude/skills/vsa-agent-state/SKILL.md
"""

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres import PostgresSaver

from .state import VSAAgentState
from .nodes import classifier, planner, executor, analyzer


def create_vsa_agent(checkpointer: PostgresSaver | None = None) -> StateGraph:
    """Create and compile the VSA agent graph.
    
    Graph structure:
        START -> classifier -> planner -> executor -> analyzer
                                              ^            |
                                              |            v
                                              +-- (loop) --+
                                                           |
                                                           v
                                                          END
    
    Args:
        checkpointer: Optional PostgresSaver for state persistence
        
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(VSAAgentState)
    
    # Add nodes
    workflow.add_node("classifier", classifier.run)
    workflow.add_node("planner", planner.run)
    workflow.add_node("executor", executor.run)
    workflow.add_node("analyzer", analyzer.run)
    
    # Define edges
    workflow.add_edge(START, "classifier")
    workflow.add_edge("classifier", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "analyzer")
    
    # Conditional routing after analysis
    workflow.add_conditional_edges(
        "analyzer",
        _route_after_analysis,
        {
            "executor": "executor",  # Continue executing steps
            "planner": "planner",    # Needs replanning
            END: END,                # All done
        }
    )
    
    # Compile with optional checkpointer
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()


def _route_after_analysis(state: VSAAgentState) -> str:
    """Determine next node after analysis.
    
    Returns:
        - "planner" if needs replanning
        - "executor" if more steps to execute
        - END if all done or error
    """
    # Check for errors
    if state.get("error"):
        return END
    
    # Check if needs replanning
    if state.get("needs_replan"):
        return "planner"
    
    # Check if should continue executing
    plan = state.get("plan") or []
    current_step = state.get("current_step", 0)
    
    if state.get("should_continue") and current_step < len(plan):
        return "executor"
    
    return END


async def create_agent_with_postgres(connection_string: str) -> StateGraph:
    """Create agent with PostgreSQL checkpointer for persistence.
    
    Args:
        connection_string: PostgreSQL connection string
        
    Returns:
        Compiled StateGraph with persistence
    """
    checkpointer = PostgresSaver.from_conn_string(connection_string)
    await checkpointer.setup()  # Create tables if needed
    return create_vsa_agent(checkpointer=checkpointer)
