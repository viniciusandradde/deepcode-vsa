"""OpenRouter LLM Client with hybrid model routing.

Reference: .claude/skills/vsa-llm-config/SKILL.md
"""

import json
from dataclasses import dataclass
from typing import AsyncIterator

import httpx

from ..config.settings import LLMSettings, ModelTier


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7


class ModelRouter:
    """Routes tasks to appropriate LLM models."""
    
    # Task type to model tier mapping
    TASK_ROUTING: dict[str, ModelTier] = {
        # Simple tasks → FAST (Llama)
        "classify": ModelTier.FAST,
        "gut_score": ModelTier.FAST,
        "itil_category": ModelTier.FAST,
        "validate": ModelTier.FAST,
        
        # Analysis tasks → SMART (DeepSeek)
        "plan": ModelTier.SMART,
        "rca": ModelTier.SMART,
        "correlate": ModelTier.SMART,
        "analyze": ModelTier.SMART,
        "diagnose": ModelTier.SMART,
        
        # Creative tasks → CREATIVE (Minimax)
        "report": ModelTier.CREATIVE,
        "summary": ModelTier.CREATIVE,
        "explain": ModelTier.CREATIVE,
        "document": ModelTier.CREATIVE,
        
        # Critical tasks → PREMIUM (Claude)
        "critical": ModelTier.PREMIUM,
        "fallback": ModelTier.PREMIUM,
        "complex": ModelTier.PREMIUM,
    }
    
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.models = {
            ModelTier.FAST: ModelConfig(
                model_id=settings.fast_model,
                max_tokens=2048,
                temperature=0.3  # More deterministic
            ),
            ModelTier.SMART: ModelConfig(
                model_id=settings.smart_model,
                max_tokens=4096,
                temperature=0.5
            ),
            ModelTier.CREATIVE: ModelConfig(
                model_id=settings.creative_model,
                max_tokens=4096,
                temperature=0.9  # More creative
            ),
            ModelTier.PREMIUM: ModelConfig(
                model_id=settings.premium_model,
                max_tokens=8192,
                temperature=0.7
            ),
        }
    
    def get_model(self, tier: ModelTier | None = None) -> ModelConfig:
        """Get model config for a tier."""
        tier = tier or self.settings.default_tier
        return self.models[tier]
    
    def route_by_task(self, task_type: str) -> ModelConfig:
        """Auto-select model based on task type."""
        tier = self.TASK_ROUTING.get(task_type, self.settings.default_tier)
        return self.get_model(tier)


class OpenRouterClient:
    """OpenRouter API client with hybrid model support."""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.router = ModelRouter(settings)
        self.headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "HTTP-Referer": "https://deepcode-vsa.local",
            "X-Title": "DeepCode VSA",
            "Content-Type": "application/json",
        }
    
    async def chat(
        self,
        messages: list[dict],
        tier: ModelTier | None = None,
        task_type: str | None = None,
        stream: bool = False,
    ) -> dict:
        """Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tier: Model tier to use (overrides task_type)
            task_type: Task type for auto-routing
            stream: Enable streaming (returns different format)
            
        Returns:
            OpenAI-compatible response dict
        """
        # Get model config
        if tier:
            config = self.router.get_model(tier)
        elif task_type:
            config = self.router.route_by_task(task_type)
        else:
            config = self.router.get_model()
        
        payload = {
            "model": config.model_id,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": stream,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
    
    async def stream_chat(
        self,
        messages: list[dict],
        tier: ModelTier | None = None,
        task_type: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat completion.
        
        Yields:
            Content chunks as they arrive
        """
        if tier:
            config = self.router.get_model(tier)
        elif task_type:
            config = self.router.route_by_task(task_type)
        else:
            config = self.router.get_model()
        
        payload = {
            "model": config.model_id,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                if content := delta.get("content"):
                                    yield content
                            except json.JSONDecodeError:
                                continue
    
    def get_content(self, response: dict) -> str:
        """Extract content from response."""
        return response["choices"][0]["message"]["content"]
