---
name: vsa-llm-config
description: LLM configuration patterns for VSA with hybrid model selection. Use when implementing LLM client, model routing, or multi-model strategies with OpenRouter.
---

# VSA LLM Configuration

## Hybrid Model Strategy

```python
from enum import Enum
from pydantic_settings import BaseSettings
from pydantic import Field

class ModelTier(str, Enum):
    FAST = "fast"       # Classificação, GUT, tarefas simples
    SMART = "smart"     # RCA, planejamento, análise
    PREMIUM = "premium" # Tarefas críticas, fallback
    CREATIVE = "creative"  # Geração de texto, relatórios

class LLMSettings(BaseSettings):
    provider: str = "openrouter"
    api_key: str = Field(..., env="OPENROUTER_API_KEY")
    
    # Modelo rápido/gratuito - classificação, GUT
    fast_model: str = "meta-llama/llama-3.3-70b-instruct"
    
    # Modelo inteligente/barato - RCA, planejamento
    smart_model: str = "deepseek/deepseek-chat"
    
    # Modelo premium - fallback, tarefas críticas
    premium_model: str = "anthropic/claude-3.5-sonnet"
    
    # Modelo criativo - relatórios, sínteses
    creative_model: str = "minimax/minimax-m2-her"
    
    # Default
    default_tier: ModelTier = ModelTier.SMART
    
    class Config:
        env_prefix = "LLM_"
```

---

## Model Router

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelConfig:
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7

class ModelRouter:
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.models = {
            ModelTier.FAST: ModelConfig(
                model_id=settings.fast_model,
                max_tokens=2048,
                temperature=0.3  # Mais determinístico
            ),
            ModelTier.SMART: ModelConfig(
                model_id=settings.smart_model,
                max_tokens=4096,
                temperature=0.5
            ),
            ModelTier.PREMIUM: ModelConfig(
                model_id=settings.premium_model,
                max_tokens=8192,
                temperature=0.7
            ),
            ModelTier.CREATIVE: ModelConfig(
                model_id=settings.creative_model,
                max_tokens=4096,
                temperature=0.9  # Mais criativo
            ),
        }
    
    def get_model(self, tier: ModelTier = None) -> ModelConfig:
        tier = tier or self.settings.default_tier
        return self.models[tier]
    
    def route_by_task(self, task_type: str) -> ModelConfig:
        """Auto-select model based on task type."""
        task_routing = {
            # Tarefas simples → FAST
            "classify": ModelTier.FAST,
            "gut_score": ModelTier.FAST,
            "itil_category": ModelTier.FAST,
            
            # Tarefas de análise → SMART
            "plan": ModelTier.SMART,
            "rca": ModelTier.SMART,
            "correlate": ModelTier.SMART,
            "analyze": ModelTier.SMART,
            
            # Geração de texto → CREATIVE
            "report": ModelTier.CREATIVE,
            "summary": ModelTier.CREATIVE,
            "explain": ModelTier.CREATIVE,
            
            # Fallback/crítico → PREMIUM
            "critical": ModelTier.PREMIUM,
            "fallback": ModelTier.PREMIUM,
        }
        tier = task_routing.get(task_type, self.settings.default_tier)
        return self.get_model(tier)
```

---

## OpenRouter Client

```python
import httpx
from typing import AsyncIterator

class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.router = ModelRouter(settings)
        self.headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "HTTP-Referer": "https://deepcode-vsa.local",
            "X-Title": "DeepCode VSA"
        }
    
    async def chat(
        self,
        messages: list[dict],
        tier: ModelTier = None,
        task_type: str = None,
        stream: bool = False
    ) -> dict:
        """Send chat completion request."""
        
        # Get model config
        if task_type:
            config = self.router.route_by_task(task_type)
        else:
            config = self.router.get_model(tier)
        
        payload = {
            "model": config.model_id,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": stream
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
        tier: ModelTier = None
    ) -> AsyncIterator[str]:
        """Stream chat completion."""
        config = self.router.get_model(tier)
        
        payload = {
            "model": config.model_id,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True
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
                            chunk = json.loads(data)
                            if content := chunk["choices"][0]["delta"].get("content"):
                                yield content
```

---

## Usage in Agent Nodes

```python
from ..llm.openrouter import OpenRouterClient, ModelTier

async def classifier_node(state: VSAAgentState, llm: OpenRouterClient) -> dict:
    """Uses FAST model for classification."""
    response = await llm.chat(
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": state["user_request"]}
        ],
        task_type="classify"  # Auto-routes to FAST
    )
    ...

async def planner_node(state: VSAAgentState, llm: OpenRouterClient) -> dict:
    """Uses SMART model for planning."""
    response = await llm.chat(
        messages=[...],
        task_type="plan"  # Auto-routes to SMART
    )
    ...

async def report_node(state: VSAAgentState, llm: OpenRouterClient) -> dict:
    """Uses CREATIVE (Minimax) for report generation."""
    response = await llm.chat(
        messages=[...],
        task_type="report"  # Auto-routes to CREATIVE (minimax-m2-her)
    )
    ...
```

---

## Environment Variables

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Optional: Override models
LLM_FAST_MODEL=meta-llama/llama-3.3-70b-instruct
LLM_SMART_MODEL=deepseek/deepseek-chat
LLM_PREMIUM_MODEL=anthropic/claude-3.5-sonnet
LLM_CREATIVE_MODEL=minimax/minimax-m2-her
```

---

## Cost Estimation

| Tier | Model | Input/1M | Output/1M | Uso típico |
|------|-------|----------|-----------|------------|
| FAST | Llama 3.3 70B | $0.40 | $0.40 | 60% das chamadas |
| SMART | DeepSeek V3 | $0.14 | $0.28 | 30% das chamadas |
| CREATIVE | Minimax M2 | $0.60 | $0.60 | 8% das chamadas |
| PREMIUM | Claude 3.5 | $3.00 | $15.00 | 2% (fallback) |

**Custo médio estimado:** ~$0.35/1M tokens (muito barato!)
