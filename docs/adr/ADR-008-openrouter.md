# ADR-008: LLM via OpenRouter

## Status

**Aprovado** - Janeiro 2026

## Contexto

O DeepCode VSA requer acesso a Large Language Models (LLMs) para:
- Planejamento de tarefas
- Interpretação de dados
- Geração de insights
- Síntese executiva

As opções de acesso a LLMs incluem:
- API direta de provedores (OpenAI, Anthropic, etc.)
- Gateways/Aggregators (OpenRouter, LiteLLM)
- LLMs locais (Ollama, vLLM)

## Decisão

Uso de **OpenRouter** como gateway para acesso a múltiplos LLMs.

## Justificativa

### O que é OpenRouter?

OpenRouter é um gateway que fornece:
- API unificada para múltiplos provedores de LLM
- Fallback automático entre modelos
- Billing consolidado
- Acesso a modelos gratuitos/baratos

### Comparativo de Abordagens

| Critério | API Direta | OpenRouter | LLM Local |
|----------|-----------|------------|-----------|
| Custo | Variável | Otimizado | Hardware |
| Fallback | Manual | Automático | N/A |
| Modelos | 1 por provedor | 100+ modelos | Limitados |
| Latência | Baixa | Baixa | Muito baixa |
| Privacidade | Cloud | Cloud | Local |
| Manutenção | Por provedor | Única | Alta |

### Por que OpenRouter?

1. **Redução de Custo**
   - Acesso a modelos mais baratos
   - Competição de preços entre provedores
   - Modelos gratuitos para desenvolvimento

2. **Fallback Automático**
   - Se modelo primário falha, usa alternativo
   - Zero downtime por indisponibilidade
   - Configurável por preferência

3. **Múltiplos Modelos**
   - GPT-4, Claude, Llama, Mistral, etc.
   - Escolha do modelo ideal por tarefa
   - Fácil experimentação

4. **API Compatível com OpenAI**
   - Mesma interface da OpenAI API
   - Fácil migração se necessário
   - Compatível com LangChain/LangGraph

## Arquitetura de Integração

```
┌─────────────────────────────────────────────────────────────┐
│                      DeepCode VSA                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  LLM Client Layer                    │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  LLMClient                                   │   │   │
│  │  │  - provider: OpenRouter                      │   │   │
│  │  │  - model: configurable                       │   │   │
│  │  │  - fallback_models: [...]                    │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                       │                             │   │
│  └───────────────────────┼─────────────────────────────┘   │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │      OpenRouter        │
              │  ┌──────────────────┐  │
              │  │ Unified API      │  │
              │  └────────┬─────────┘  │
              │           │            │
              │  ┌────────┴─────────┐  │
              │  │                  │  │
              │  ▼                  ▼  │
              │ ┌────┐  ┌────┐  ┌────┐│
              │ │GPT4│  │Claude│ │Llama││
              │ └────┘  └────┘  └────┘│
              └────────────────────────┘
```

## Configuração

```python
# config.py
from pydantic import BaseSettings

class LLMConfig(BaseSettings):
    """Configuração do LLM."""

    provider: str = "openrouter"
    api_key: str  # OPENROUTER_API_KEY

    # Modelo principal
    model: str = "anthropic/claude-3.5-sonnet"

    # Fallbacks em ordem de preferência
    fallback_models: list[str] = [
        "openai/gpt-4-turbo",
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mistral-large"
    ]

    # Configurações
    temperature: float = 0.1
    max_tokens: int = 4096

    class Config:
        env_prefix = "LLM_"
```

```yaml
# config.yaml
llm:
  provider: openrouter
  model: anthropic/claude-3.5-sonnet

  fallback_models:
    - openai/gpt-4-turbo
    - meta-llama/llama-3.1-70b-instruct

  # Modelo específico para tarefas simples (economia)
  fast_model: openai/gpt-4o-mini

  temperature: 0.1
  max_tokens: 4096
```

## Implementação do Cliente

```python
from openai import AsyncOpenAI

class LLMClient:
    """Cliente LLM via OpenRouter."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.api_key,
            default_headers={
                "HTTP-Referer": "https://deepcode-vsa.io",
                "X-Title": "DeepCode VSA"
            }
        )

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs
    ) -> str:
        """Executa completion com fallback automático."""
        model = model or self.config.model
        models_to_try = [model] + self.config.fallback_models

        for attempt_model in models_to_try:
            try:
                response = await self.client.chat.completions.create(
                    model=attempt_model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    **kwargs
                )
                return response.choices[0].message.content

            except Exception as e:
                logger.warning(
                    f"Model {attempt_model} failed: {e}, trying next"
                )
                continue

        raise RuntimeError("All LLM models failed")
```

## Modelos Recomendados por Tarefa

| Tarefa | Modelo Recomendado | Alternativa |
|--------|-------------------|-------------|
| Planejamento complexo | claude-3.5-sonnet | gpt-4-turbo |
| Análise de dados | claude-3.5-sonnet | gpt-4o |
| Síntese rápida | gpt-4o-mini | llama-3.1-8b |
| Code generation | claude-3.5-sonnet | gpt-4-turbo |

## Consequências

### Positivas

- **Flexibilidade**: Trocar modelos sem mudar código
- **Resiliência**: Fallback automático
- **Custo otimizado**: Usar modelo mais barato quando possível
- **Experimentação**: Fácil testar novos modelos
- **API estável**: Compatível com OpenAI SDK

### Negativas

- Dependência de serviço terceiro
- Latência adicional (mínima)
- Menor controle sobre roteamento

## Custos Estimados (Jan 2026)

| Modelo | Input (1M tokens) | Output (1M tokens) |
|--------|-------------------|-------------------|
| claude-3.5-sonnet | $3.00 | $15.00 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| llama-3.1-70b | $0.52 | $0.75 |

## Alternativas Consideradas

### API Direta (OpenAI/Anthropic)
Lock-in em um provedor, sem fallback nativo, custos potencialmente maiores.

### LLM Local (Ollama)
Performance inferior para tarefas complexas, requer hardware dedicado.

### LiteLLM (Self-hosted)
Mais controle, mas requer infraestrutura própria.

## Referências

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
