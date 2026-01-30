---
name: vsa-llm-config
description: Hybrid LLM model strategy and configuration for DeepCode VSA.
---

# VSA LLM Configuration

DeepCode VSA uses a tiered model approach via OpenRouter to balance cost, performance, and intelligence.

## 🚀 Tiered Model Strategy

| Tier | Usage | Recommended Models |
| ---- | ----- | ------------------ |
| **FAST** | Classification, GUT scoring, basic validation | `meta-llama/llama-3.3-70b-instruct`, `google/gemini-flash-1.5` |
| **SMART** | Planning, ITIL analysis, correlation | `deepseek/deepseek-chat`, `x-ai/grok-4.1-fast` |
| **PREMIUM** | Complex RCA, critical decision support, fallback | `anthropic/claude-3.5-sonnet`, `openai/gpt-4o` |
| **CREATIVE** | Reporting, executive summaries, 5W2H | `minimax/minimax-m2-her`, `google/gemini-pro-1.5` |

## ⚙️ Configuration Patterns

Models should be configured in `core/config.py` using Pydantic Settings.

### Example Environment Variables

```bash
# Model Selection
DEFAULT_MODEL_NAME=x-ai/grok-4.1-fast
FAST_MODEL=meta-llama/llama-3.3-70b-instruct
SMART_MODEL=deepseek/deepseek-chat
PREMIUM_MODEL=anthropic/claude-3.5-sonnet

# API Keys
OPENROUTER_API_KEY=sk-or-...
```

## 🧠 Dynamic Switching

The `UnifiedAgent` should dynamically select the tier based on the task complexity determined by the `Classifier` node.

- **Intent**: `CHAT` -> FAST or SMART
- **Intent**: `INCIDENTE` / `PROBLEMA` -> SMART or PREMIUM
