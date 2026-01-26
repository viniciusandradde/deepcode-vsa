# ADR-004: Orquestração - LangGraph

## Status

**Aprovado** - Janeiro 2026

## Contexto

A arquitetura de agente definida em ADR-003 (Planner-Executor-Reflector) requer um framework de orquestração que:
- Permita controle explícito de fluxo
- Suporte estados bem definidos
- Seja escalável para agentes complexos
- Integre bem com LLMs

## Decisão

**LangGraph** será usado para orquestrar o agente DeepCode VSA.

## Justificativa

### Comparativo de Frameworks

| Framework | Controle de Fluxo | Estados | Maturidade | Flexibilidade |
|-----------|------------------|---------|------------|---------------|
| LangGraph | Excelente | Explícitos | Alta | Alta |
| LangChain Agents | Limitado | Implícitos | Alta | Média |
| AutoGen | Médio | Parciais | Média | Alta |
| CrewAI | Médio | Limitados | Média | Média |
| Custom | Total | Manual | N/A | Total |

### Por que LangGraph?

1. **Controle Explícito de Fluxo**
   - Grafos de estado permitem modelar exatamente o fluxo desejado
   - Decisões condicionais claras entre nós
   - Loops controlados (ex: Reflector → Planner)

2. **Estados Bem Definidos**
   - Estado tipado e versionado
   - Persistência opcional (checkpoints)
   - Fácil debug e observabilidade

3. **Escalabilidade**
   - Suporta grafos complexos com múltiplos agentes
   - Subgrafos para modularização
   - Streaming nativo

4. **Integração com Ecossistema**
   - Parte do LangChain ecosystem
   - Compatível com todos os LLMs
   - Tools e prompts reutilizáveis

## Arquitetura com LangGraph

```python
from langgraph.graph import StateGraph, END

# Definição do estado
class AgentState(TypedDict):
    messages: list
    plan: Optional[Plan]
    api_results: dict
    reflection: Optional[str]
    final_output: Optional[str]

# Construção do grafo
workflow = StateGraph(AgentState)

# Nós
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reflector", reflector_node)

# Edges
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")
workflow.add_conditional_edges(
    "reflector",
    should_continue,
    {
        "replan": "planner",
        "complete": END
    }
)

# Compilação
agent = workflow.compile()
```

## Diagrama de Estados

```
                    ┌─────────────────┐
                    │     START       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
             ┌─────▶│    PLANNER      │
             │      └────────┬────────┘
             │               │
             │               ▼
             │      ┌─────────────────┐
             │      │    EXECUTOR     │
             │      └────────┬────────┘
             │               │
             │               ▼
             │      ┌─────────────────┐
             │      │   REFLECTOR     │
             │      └────────┬────────┘
             │               │
             │       ┌───────┴───────┐
             │       │               │
             │   replan?         complete?
             │       │               │
             └───────┘               ▼
                            ┌─────────────────┐
                            │      END        │
                            └─────────────────┘
```

## Consequências

### Positivas

- Fluxo de agente completamente controlado
- Estados persistentes e debugáveis
- Fácil adição de novos nós/capacidades
- Suporte nativo a streaming
- Boa documentação e comunidade

### Negativas

- Dependência de biblioteca externa
- Curva de aprendizado inicial
- Overhead para casos muito simples

## Configurações Recomendadas

```python
# Configuração de checkpoint para debug
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")
agent = workflow.compile(checkpointer=memory)

# Execução com streaming
async for event in agent.astream(initial_state):
    print(event)
```

## Alternativas Consideradas

### LangChain Agents (Puro)
Muito limitado para fluxos complexos, difícil de customizar.

### AutoGen
Focado em multi-agente conversacional, não ideal para fluxos estruturados.

### Implementação Custom
Maior controle, mas reinventa a roda e aumenta manutenção.

## Referências

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
