"""Backend agent for LangGraph Studio export."""

import os
from dotenv import load_dotenv

from core.agents.simple import create_simple_agent
from core.tools.search import tavily_search


load_dotenv()

# Default configuration from environment
DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash")
DEFAULT_USE_TAVILY = os.getenv("DEFAULT_USE_TAVILY", "false").strip().lower() in {"1", "true", "yes"}

# Create default agent graph
tools = []
if DEFAULT_USE_TAVILY:
    tools.append(tavily_search)

agent_instance = create_simple_agent(
    model_name=DEFAULT_MODEL_NAME,
    tools=tools,
)

# Export graph for LangGraph Studio
graph = agent_instance.create_graph()

