"""Dynamic settings middleware for runtime model/tool configuration."""

import json
import os
from typing import Optional, Callable, List

from dotenv import load_dotenv
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool


load_dotenv()

DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}
DEFAULT_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


def dbg(*args):
    """Debug logging helper."""
    if DEBUG_AGENT_LOGS:
        try:
            print(*args, flush=True)
        except Exception:
            pass


def extract_settings_from_messages(messages) -> tuple[Optional[str], Optional[dict]]:
    """Extract settings from SystemMessage with JSON {"type":"settings"}.
    
    Returns:
        Tuple of (model_name, tool_settings_dict)
    """
    model_name: Optional[str] = None
    tool_settings: Optional[dict] = None
    
    for msg in reversed(messages or []):
        try:
            if getattr(msg, "type", None) != "system":
                continue
            content = getattr(msg, "content", None)
            if not isinstance(content, str):
                continue
            data = json.loads(content)
            if isinstance(data, dict) and data.get("type") == "settings":
                if isinstance(data.get("model"), str) and data["model"].strip():
                    model_name = data["model"].strip()
                # Extract tool settings (e.g., {"use_tavily": True})
                tool_settings = {k: v for k, v in data.items() if k not in ("type", "model")}
                break
        except Exception:
            continue
    
    return model_name, tool_settings


def strip_settings_messages(messages):
    """Remove settings messages from the flow before LLM."""
    cleaned = []
    for msg in messages or []:
        try:
            if getattr(msg, "type", None) == "system":
                content = getattr(msg, "content", None)
                if isinstance(content, str):
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict) and data.get("type") == "settings":
                            continue
                    except Exception:
                        pass
        except Exception:
            pass
        cleaned.append(msg)
    return cleaned


def resolve_settings(messages, runtime) -> tuple[Optional[str], dict]:
    """Resolve model_name and tool settings from all sources.
    
    Returns:
        Tuple of (model_name, tool_settings_dict)
    """
    model_name, tool_settings = extract_settings_from_messages(messages)
    tool_settings = tool_settings or {}
    
    # Resolve runtime config
    try:
        runtime_cfg = getattr(runtime, "config", None)
        if isinstance(runtime_cfg, dict):
            cfg = runtime_cfg.get("configurable", {}) or {}
            if isinstance(cfg.get("model_name"), str) and cfg["model_name"].strip():
                model_name = cfg["model_name"].strip()
            # Merge tool settings from config
            for k, v in cfg.items():
                if k != "model_name" and k.startswith("use_") or k.startswith("enable_"):
                    tool_settings[k] = v
        ctx = getattr(runtime, "context", None)
        if isinstance(ctx, dict):
            if isinstance(ctx.get("model_name"), str) and ctx["model_name"].strip():
                model_name = ctx["model_name"].strip()
            # Merge tool settings from context
            for k, v in ctx.items():
                if k != "model_name" and (k.startswith("use_") or k.startswith("enable_")):
                    tool_settings[k] = v
    except Exception:
        pass
    
    return model_name, tool_settings


class DynamicSettingsMiddleware(AgentMiddleware):
    """Middleware for dynamic model and tool configuration.
    
    Supports:
    - Dynamic model switching via SystemMessage or runtime config
    - Dynamic tool enabling/disabling (e.g., use_tavily, enable_rag)
    """
    
    def __init__(self, tool_filters: Optional[dict] = None):
        """Initialize middleware.
        
        Args:
            tool_filters: Dict mapping tool names to filter functions
                Example: {"tavily_search": lambda tools, enabled: ...}
        """
        self.tool_filters = tool_filters or {}
    
    def filter_tools(self, tools: List[BaseTool], tool_settings: dict) -> List[BaseTool]:
        """Filter tools based on settings.
        
        Args:
            tools: List of available tools
            tool_settings: Dict with tool enable/disable flags
            
        Returns:
            Filtered list of tools
        """
        filtered = list(tools)
        
        # Apply custom filters
        for tool_name, filter_func in self.tool_filters.items():
            enabled = tool_settings.get(f"use_{tool_name}", tool_settings.get(f"enable_{tool_name}", True))
            if callable(filter_func):
                filtered = filter_func(filtered, enabled)
            else:
                # Default: remove tool if disabled
                if not enabled:
                    filtered = [t for t in filtered if getattr(t, "name", None) != tool_name]
        
        return filtered
    
    def apply_settings(self, request: ModelRequest, model_name: Optional[str], tool_settings: dict):
        """Apply model and tool settings to request."""
        # Filter tools
        tools = list(getattr(request, "tools", []) or [])
        tools_filtered = self.filter_tools(tools, tool_settings)
        
        # Clean messages
        messages = getattr(request, "messages", None) or []
        cleaned = strip_settings_messages(messages)
        
        # Create new model if specified
        new_model = getattr(request, "model", None)
        try:
            if model_name:
                new_model = ChatOpenAI(
                    model=model_name,
                    temperature=0.2,
                    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                    openai_api_base=os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL),
                )
                dbg(f"[SETTINGS] Modelo: {model_name}, Tool settings: {tool_settings}")
        except Exception as e:
            dbg(f"[SETTINGS] Erro ao aplicar modelo: {e}")
        
        # Update request
        request.model = new_model
        request.messages = cleaned
        request.tools = tools_filtered
        
        dbg(f"[MIDDLEWARE] Tools: {len(tools)} → {len(tools_filtered)}")
    
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """Sync version: intercept model call."""
        messages = getattr(request, "messages", None) or []
        runtime = getattr(request, "runtime", None)
        model_name, tool_settings = resolve_settings(messages, runtime)
        
        self.apply_settings(request, model_name, tool_settings)
        return handler(request)
    
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """Async version: intercept model call."""
        messages = getattr(request, "messages", None) or []
        runtime = getattr(request, "runtime", None)
        model_name, tool_settings = resolve_settings(messages, runtime)
        
        self.apply_settings(request, model_name, tool_settings)
        return await handler(request)

