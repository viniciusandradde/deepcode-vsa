---
name: langgraph-agent
description: LangGraph agent development patterns. State machines, graph construction, node design, conditional edges. Use when building AI agents with LangGraph.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# LangGraph Agent Development

> Princípios para construção de agentes com LangGraph.
> **Aprenda a PENSAR em grafos de estado, não copiar código.**

---

## 1. Conceitos Fundamentais

### O que é LangGraph?

Framework para construção de agentes como **grafos de estado**:

- Nós executam lógica
- Edges definem transições
- Estado é compartilhado entre nós

### Quando Usar LangGraph

```
Use LangGraph quando:
├── Precisa de fluxo complexo (não linear)
├── Múltiplos passos com decisões condicionais
├── Loop de refinamento (retry, reflection)
├── Estado precisa persistir entre passos
└── Precisa de controle explícito do fluxo

Não use quando:
├── Simples prompt → resposta
├── Chain linear simples
└── Sem necessidade de loops
```

---

## 2. Arquitetura Básica

### Componentes

| Componente | Propósito |
|------------|-----------|
| **State** | Dados compartilhados entre nós |
| **Node** | Função que processa estado |
| **Edge** | Transição entre nós |
| **Conditional Edge** | Transição baseada em condição |
| **Graph** | Composição de nós e edges |

### Estrutura de Projeto

```
agent/
├── __init__.py
├── graph.py          # Definição do grafo
├── state.py          # Definição do estado
├── nodes/            # Nós do grafo
│   ├── __init__.py
│   ├── planner.py
│   ├── executor.py
│   └── reflector.py
└── tools/            # Ferramentas do agente
    └── ...
```

---

## 3. Definindo Estado

### State com TypedDict

```python
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Estado do agente."""
    # Mensagens com reducer para append
    messages: Annotated[list, add_messages]
    
    # Dados do fluxo
    plan: Optional[list[str]]
    current_step: int
    results: dict
    
    # Controle
    should_continue: bool
    error: Optional[str]
```

### Reducers

```python
# add_messages: Faz append de novas mensagens
# operator.add: Concatena listas
# lambda a, b: b: Sempre usa o novo valor (padrão)

from operator import add

class State(TypedDict):
    logs: Annotated[list[str], add]  # Append
    counter: int  # Sobrescreve (padrão)
```

---

## 4. Criando Nós

### Anatomia de um Nó

```python
from langchain_core.messages import HumanMessage, AIMessage

def planner_node(state: AgentState) -> dict:
    """
    Nó que planeja as etapas.
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Atualizações parciais do estado
    """
    messages = state["messages"]
    
    # Lógica do nó
    plan = create_plan(messages[-1].content)
    
    # Retorna atualizações do estado
    return {
        "plan": plan,
        "current_step": 0,
        "messages": [AIMessage(content=f"Plano criado: {plan}")]
    }
```

### Nó Assíncrono

```python
async def executor_node(state: AgentState) -> dict:
    """Nó assíncrono para execução."""
    plan = state["plan"]
    step = state["current_step"]
    
    # Execução assíncrona
    result = await execute_step(plan[step])
    
    return {
        "results": {**state["results"], step: result},
        "current_step": step + 1
    }
```

---

## 5. Construindo o Grafo

### Grafo Básico

```python
from langgraph.graph import StateGraph, END, START

# Criar grafo
workflow = StateGraph(AgentState)

# Adicionar nós
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reflector", reflector_node)

# Edges simples
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")

# Compilar
app = workflow.compile()
```

### Edges Condicionais

```python
def should_continue(state: AgentState) -> str:
    """Decide próximo passo baseado no estado."""
    if state.get("error"):
        return "error_handler"
    if state["current_step"] >= len(state["plan"]):
        return "reflector"
    return "executor"

# Adicionar edge condicional
workflow.add_conditional_edges(
    "executor",  # Nó de origem
    should_continue,  # Função de decisão
    {
        "executor": "executor",  # Loop
        "reflector": "reflector",
        "error_handler": "error_handler"
    }
)
```

### Loop de Reflexão

```python
def should_replan(state: AgentState) -> str:
    """Decide se precisa replanejar."""
    if state.get("needs_replan"):
        return "planner"  # Loop back
    return END

workflow.add_conditional_edges(
    "reflector",
    should_replan,
    {
        "planner": "planner",
        END: END
    }
)
```

---

## 6. Padrões Comuns

### Planner-Executor-Reflector

```
START → Planner → Executor → Reflector → END
              ↑       ↓           ↓
              └───────┴───────────┘
                 (loops de retry)
```

```python
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("reflector", reflector)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")

workflow.add_conditional_edges(
    "reflector",
    lambda s: "planner" if s["needs_replan"] else END,
    {"planner": "planner", END: END}
)

app = workflow.compile()
```

### Tool Calling Agent

```python
from langgraph.prebuilt import create_react_agent

# Agente ReAct pré-construído
agent = create_react_agent(
    model,
    tools=[search_tool, calc_tool],
    state_modifier="You are a helpful assistant..."
)
```

---

## 7. Checkpoints e Memória

### Memória em Memória

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Invocar com thread_id para persistência
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(initial_state, config)
```

### Memória com SQLite

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string(":memory:") as memory:
    app = workflow.compile(checkpointer=memory)
```

---

## 8. Streaming

### Stream de Eventos

```python
async for event in app.astream(initial_state):
    node_name = list(event.keys())[0]
    print(f"Nó: {node_name}")
    print(f"Output: {event[node_name]}")
```

### Stream de Tokens

```python
async for event in app.astream_events(initial_state, version="v2"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
```

---

## 9. Tratamento de Erros

### Nó de Fallback

```python
def error_handler(state: AgentState) -> dict:
    """Trata erros do fluxo."""
    error = state.get("error")
    
    return {
        "messages": [AIMessage(content=f"Erro: {error}. Tentando novamente...")],
        "error": None,
        "retry_count": state.get("retry_count", 0) + 1
    }

# Adicionar ao grafo
workflow.add_node("error_handler", error_handler)
```

### Limite de Retries

```python
def should_retry(state: AgentState) -> str:
    if state.get("retry_count", 0) >= 3:
        return END  # Desiste após 3 tentativas
    return "executor"
```

---

## 10. Testes

### Testar Nós Isoladamente

```python
import pytest

def test_planner_creates_plan():
    state = {"messages": [HumanMessage(content="Analisar riscos")]}
    
    result = planner_node(state)
    
    assert "plan" in result
    assert len(result["plan"]) > 0
```

### Testar Grafo Completo

```python
@pytest.mark.asyncio
async def test_full_workflow():
    initial_state = {
        "messages": [HumanMessage(content="Query test")],
        "plan": None,
        "results": {}
    }
    
    result = await app.ainvoke(initial_state)
    
    assert result["current_step"] == len(result["plan"])
```

---

## 11. Checklist

### Antes de Implementar

- [ ] Definiu estado com TypedDict?
- [ ] Identificou nós necessários?
- [ ] Mapeou transições (edges)?
- [ ] Identificou loops/condicionais?
- [ ] Planejou tratamento de erros?

### Durante Implementação

- [ ] Nós retornam dict com updates?
- [ ] Edges condicionais retornam string?
- [ ] Estado é tipado corretamente?
- [ ] Async onde necessário?

### Depois de Implementar

- [ ] Testes unitários para nós?
- [ ] Teste de integração do grafo?
- [ ] Limite de loops configurado?
- [ ] Logging adequado?

---

## 12. Anti-Patterns

### ❌ NÃO FAÇA

```python
# Estado mutável
def bad_node(state):
    state["data"].append(x)  # Mutação!
    return state

# Sem tipagem
def untyped(state):
    return {"foo": "bar"}  # Sem TypedDict
```

### ✅ FAÇA

```python
# Estado imutável
def good_node(state: AgentState) -> dict:
    new_data = [*state["data"], x]  # Cópia
    return {"data": new_data}

# Tipado
def typed(state: AgentState) -> dict:
    return {"plan": [...]}
```

---

## 📖 Referências

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)

---

> **Lembre-se:** LangGraph é sobre **controle explícito de fluxo**. Use quando precisar de loops, condicionais e estado persistente.
