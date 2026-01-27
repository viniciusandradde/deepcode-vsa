# Análise Completa: UnifiedAgent - Desempenho e Persistência

## 📋 Sumário Executivo

**Data:** 2026-01-27
**Arquivo Analisado:** `core/agents/unified.py` (589 linhas)
**Status Atual:** ⚠️ **PARCIALMENTE IMPLEMENTADO** - Várias funcionalidades incompletas

**Problemas Críticos Identificados:**
1. 🔴 Planner node retorna plano vazio (linha 442)
2. 🔴 Confirmation node não implementado
3. 🟡 Múltiplas chamadas LLM por requisição (Router + Classifier)
4. 🟡 Checkpointer não está sendo passado corretamente
5. 🟡 Estado complexo com 15+ campos, mas muitos não usados

---

## 🏗️ Arquitetura do UnifiedAgent

### Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO COMPLETO (ITIL=true)                │
└─────────────────────────────────────────────────────────────┘

START
  ↓
┌──────────┐
│  Router  │ ← Classifica intenção (conversa/IT/multi/search)
└──────────┘
  ↓ (se IT_REQUEST)
┌────────────┐
│ Classifier │ ← ITIL + GUT Score (G×U×T)
└────────────┘
  ↓
┌──────────┐
│ Planner  │ ← ⚠️ VAZIO! Retorna [] (não implementado)
└──────────┘
  ↓
┌──────────┐
│ Executor │ ← Invoca model.bind_tools(tools)
└──────────┘
  ↓
┌──────────┐
│  Tools   │ ← Se tool_calls presentes
└──────────┘
  ↓ (loop back to Executor)
┌───────────┐
│ Responder │ ← Final response
└───────────┘
  ↓
END
```

### Fluxo Simplificado (ITIL=false)

```
START → Executor → Tools (loop) → Responder → END
```

---

## 🔬 Análise de Componentes

### 1. **Router Node** (linhas 326-365)

**Função:** Classifica intenção do usuário usando LLM

**Performance:**
- ✅ **Latência:** ~500-800ms (1 chamada LLM)
- ⚠️ **Custo:** 1 LLM call por mensagem
- ⚠️ **Necessidade:** Questionável para aplicação VSA (sempre é IT)

**Problema:**
```python
# Faz uma chamada LLM completa apenas para classificar
response = self.model.invoke([
    SystemMessage(content=ROUTER_SYSTEM_PROMPT),
    HumanMessage(content=user_content)
])
```

**Solução Proposta:**
- Para VSA (sempre IT), pode ser **hardcoded** ou usar **regex simples**
- Economiza ~$0.001 por requisição + 500ms latência

---

### 2. **Classifier Node** (linhas 367-433)

**Função:** Classifica categoria ITIL + calcula GUT Score

**Performance:**
- ✅ **Funcional:** Implementado corretamente
- ⚠️ **Latência:** ~800-1200ms (1 chamada LLM)
- ⚠️ **Parsing JSON:** Vulnerável a erros de formato

**Código:**
```python
response = self.model.invoke([
    SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
    HumanMessage(content=user_content)
])

# Parse JSON (pode falhar)
data = json.loads(content)
gut_score = gravidade * urgencia * tendencia
```

**Métricas Geradas:**
- `task_category`: incidente/problema/mudanca/requisicao/conversa
- `gut_score`: 1-125 (G×U×T)
- `priority`: critico/alto/medio/baixo

**Problema:**
- Se JSON parsing falhar, cai para `TaskCategory.CONVERSA`
- Sem retry ou fallback

---

### 3. **Planner Node** (linhas 435-443)

**🔴 CRÍTICO: NÃO IMPLEMENTADO!**

```python
def _planner_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
    """Plan actions based on classification."""
    dbg("Planner node executing...")

    if not self.enable_planning:
        return {}

    # For now, return empty plan - will be enhanced
    return {"plan": [], "current_step": 0}  # ← VAZIO!
```

**Impacto:**
- ✅ Não quebra execução (plano vazio)
- ❌ Funcionalidade de **Task 2.6** (Plano de Ação) não funciona via UnifiedAgent
- ❌ System Prompt do chat.py que gera plano de ação funciona, mas não via este node

**O que deveria fazer:**
1. Usar LLM com `PLANNER_SYSTEM_PROMPT`
2. Retornar lista de ações: `[{tool, params, requires_confirm, description}]`
3. Executor seguir o plano step-by-step

---

### 4. **Executor Node** (linhas 445-478)

**Função:** Executa ações com ferramentas

**Performance:**
- ✅ **Funcional:** Implementado corretamente
- ✅ **Tools binding:** Usa `model.bind_tools(self.tools)`
- ✅ **Context injection:** Adiciona ITIL info como SystemMessage

**Código:**
```python
# Adiciona contexto ITIL
context_parts = []
if state.get("task_category"):
    context_parts.append(f"Categoria ITIL: {state['task_category'].upper()}")
if state.get("gut_score"):
    context_parts.append(f"GUT Score: {state['gut_score']}")

# Invoca model com tools
model_with_tools = self.model.bind_tools(self.tools)
response = model_with_tools.invoke(full_messages)
```

**Latência:** ~1-3s (depende de tool calls)

---

### 5. **Confirmation Node** (Task 2.8)

**🔴 CRÍTICO: NÃO EXISTE!**

**Problema:**
- `enable_confirmation` flag existe (linha 192), mas não há node implementado
- Estado tem `pending_confirmation` e `confirmed_actions` (linhas 92-93), mas não são usados
- Sem fluxo de confirmação, operações WRITE executam direto (inseguro)

**O que falta:**
```python
def _confirmer_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
    """Request user confirmation for write operations."""
    # Check if any pending action requires confirmation
    # Return pending_confirmation to UI
    # Wait for user response
    pass
```

---

## 📊 Análise de Desempenho

### Latência por Requisição (ITIL=true)

| Componente | Latência Típica | Pode Otimizar? |
|------------|----------------|----------------|
| Router     | 500-800ms      | ✅ Sim (hardcode ou regex) |
| Classifier | 800-1200ms     | 🟡 Parcial (cache) |
| Planner    | 0ms (vazio)    | ⚠️ Precisa implementar |
| Executor   | 1000-3000ms    | 🟡 Depende de tools |
| Tools      | 200-2000ms     | ❌ Depende de APIs |
| **TOTAL**  | **2.5-7s**     | ✅ Pode reduzir para 1.5-4s |

### Custo por Requisição (OpenRouter)

| Componente | Tokens Estimados | Custo (Gemini Flash) |
|------------|------------------|---------------------|
| Router     | 100-200          | $0.0001             |
| Classifier | 200-400          | $0.0002             |
| Executor   | 500-2000         | $0.001              |
| **TOTAL**  | **800-2600**     | **$0.0013**         |

**Nota:** Com `enable_itil=false`, economiza $0.0003 por requisição

---

## 🔐 Análise de Persistência

### Como Checkpointing Funciona

**Linha 193:** `checkpointer: Optional[Any] = None`

**Linha 259:** `checkpointer = checkpointer or self.checkpointer`

**Linha 321:** `self._graph = builder.compile(checkpointer=checkpointer)`

**Problema:**
- Checkpointer é passado para `compile()` ✅
- MAS: Precisa de `thread_id` no config para funcionar

### Checkpointing Config Necessário

```python
# Correto (com thread_id)
config = {"configurable": {"thread_id": "thread-123"}}
agent.invoke(input, config=config)

# Errado (sem thread_id)
agent.invoke(input)  # ← Não persiste!
```

### Verificação no chat.py

**PRECISA VERIFICAR:** Se `chat.py` está passando `thread_id` no config!

---

## 🐛 Problemas Críticos Identificados

### 1. Planner Node Vazio (CRÍTICO)

**Arquivo:** `core/agents/unified.py:442`

**Problema:**
```python
return {"plan": [], "current_step": 0}  # ← VAZIO!
```

**Impacto:**
- Plano de ação nunca é gerado via UnifiedAgent
- Task 2.6 (ActionPlan UI) não funciona com este agente
- System Prompt do chat.py compensa, mas não é ideal

**Fix:**
```python
def _planner_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
    """Plan actions based on classification."""
    if not self.enable_planning:
        return {}

    messages = state.get("messages", [])
    task_category = state.get("task_category", "conversa")
    gut_score = state.get("gut_score", 0)

    # Build context
    context = f"""
    Categoria ITIL: {task_category.upper()}
    GUT Score: {gut_score}
    Prioridade: {state.get('priority', 'medio')}

    Ferramentas disponíveis:
    {', '.join([tool.name for tool in self.tools]) if self.tools else 'nenhuma'}
    """

    try:
        response = self.model.invoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            SystemMessage(content=context),
            messages[-1]
        ])

        # Parse plan JSON
        import json
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        data = json.loads(content)
        plan = data.get("plan", [])

        return {"plan": plan, "current_step": 0}
    except Exception as e:
        dbg(f"Planner error: {e}")
        return {"plan": [], "current_step": 0}
```

---

### 2. Confirmation Node Ausente (CRÍTICO)

**Problema:**
- Flag `enable_confirmation` existe mas não faz nada
- Estado tem campos, mas não são usados
- WRITE operations executam sem confirmação

**Fix:** Implementar node `_confirmer_node` + adicionar ao grafo

---

### 3. Router Desnecessário para VSA (OTIMIZAÇÃO)

**Problema:**
- VSA sempre lida com IT requests
- Router adiciona 500-800ms + $0.0001 por requisição

**Fix:**
```python
def _router_node(self, state: UnifiedAgentState) -> Dict[str, Any]:
    """Route user message to appropriate handler."""
    # Para VSA, sempre IT request
    if os.getenv("VSA_MODE", "true").lower() == "true":
        return {"intent": Intent.IT_REQUEST.value}

    # Resto do código LLM...
```

---

### 4. Checkpointer Config Missing (CRÍTICO)

**Problema:**
- UnifiedAgent aceita checkpointer, mas não garante thread_id no config
- Precisa verificar se `chat.py` passa thread_id

**Fix:** Verificar `chat.py` e garantir:
```python
config = {"configurable": {"thread_id": session_id}}
```

---

### 5. Estado Inchado (TECHNICAL DEBT)

**Problema:**
- `UnifiedAgentState` tem 15 campos (linha 72-101)
- Muitos não são usados: `pending_actions`, `pending_confirmation`, `confirmed_actions`, `current_step`, `should_continue`

**Solução:**
- Remover campos não usados
- Simplificar estado para campos essenciais

---

## 🎯 Propostas de Melhoria

### Proposta 1: Implementar Planner (1-2h)

**Prioridade:** 🔴 ALTA

**Benefício:**
- Task 2.6 (ActionPlan) funcionará via UnifiedAgent
- Melhor estruturação de respostas complexas
- Execution step-by-step com tracking

**Esforço:** 1-2 horas

---

### Proposta 2: Implementar Confirmation Node (2-3h)

**Prioridade:** 🔴 ALTA (Governança)

**Benefício:**
- Task 2.8 (Confirmação WRITE) funcionará
- Segurança ADR-007 (Safe execution)
- Dry-run → Confirm → Execute

**Esforço:** 2-3 horas

---

### Proposta 3: Otimizar Router (30 min)

**Prioridade:** 🟡 MÉDIA

**Benefício:**
- Reduz latência em 500-800ms
- Economiza $0.0001 por requisição
- Mais previsível para VSA

**Esforço:** 30 minutos

**Implementação:**
```python
# Modo VSA: sempre IT
if os.getenv("VSA_ALWAYS_IT", "true").lower() == "true":
    return {"intent": Intent.IT_REQUEST.value}
```

---

### Proposta 4: Simplificar Estado (1h)

**Prioridade:** 🟢 BAIXA (Technical Debt)

**Benefício:**
- Código mais limpo
- Menos memória
- Mais fácil debugar

**Esforço:** 1 hora

---

### Proposta 5: Garantir Persistência (30 min)

**Prioridade:** 🔴 CRÍTICA

**Benefício:**
- Checkpointing funcionará corretamente
- Conversas persistem no PostgreSQL
- Sem perda de estado

**Esforço:** 30 minutos

**Fix:**
```python
# Em chat.py, ao invocar UnifiedAgent
config = {
    "configurable": {
        "thread_id": session_id,
        "checkpoint_ns": "unified_agent"
    }
}

result = agent.astream(input, config=config)
```

---

## 📈 Métricas de Desempenho - Antes vs Depois

### Cenário Atual (ITIL=true, Planner vazio)

| Métrica | Valor |
|---------|-------|
| Latência Total | 2.5-7s |
| LLM Calls | 2-3 (Router + Classifier + Executor) |
| Custo por Req | $0.0013 |
| Persistência | ⚠️ Depende de config |
| Plano de Ação | ❌ Não funciona |
| Confirmação WRITE | ❌ Não funciona |

### Cenário Proposto (Após fixes)

| Métrica | Valor | Delta |
|---------|-------|-------|
| Latência Total | 1.5-5s | ✅ -1s a -2s |
| LLM Calls | 2-4 (sem Router, +Planner) | 🟡 +1 ou -1 |
| Custo por Req | $0.0012 | ✅ -8% |
| Persistência | ✅ Garantida | ✅ Fix |
| Plano de Ação | ✅ Funciona | ✅ Implementado |
| Confirmação WRITE | ✅ Funciona | ✅ Implementado |

---

## 🔧 Checklist de Implementação

### Fase 1: Persistência (30 min) - URGENTE
- [ ] Verificar se chat.py passa thread_id no config
- [ ] Adicionar thread_id em todas invocações do UnifiedAgent
- [ ] Testar persistência com reinicializações
- [ ] Verificar dados no PostgreSQL

### Fase 2: Planner (2h) - ALTA PRIORIDADE
- [ ] Implementar `_planner_node` completo
- [ ] Parsear JSON do plano
- [ ] Testar geração de plano para INCIDENTE/PROBLEMA
- [ ] Integrar com ActionPlan UI do frontend

### Fase 3: Confirmation (3h) - ALTA PRIORIDADE
- [ ] Implementar `_confirmer_node`
- [ ] Adicionar ao grafo com conditional edge
- [ ] Criar endpoint de confirmação no backend
- [ ] Integrar com WriteConfirmDialog UI

### Fase 4: Otimizações (2h) - MÉDIA PRIORIDADE
- [ ] Otimizar Router (hardcode para VSA)
- [ ] Simplificar estado (remover campos não usados)
- [ ] Adicionar cache para Classifier (mesma pergunta)
- [ ] Melhorar error handling

---

## 🧪 Como Testar

### Teste 1: Verificar Persistência

```bash
# 1. Enviar mensagem no frontend
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Teste", "thread_id": "test-123"}'

# 2. Verificar checkpoint no banco
docker compose exec postgres psql -U postgres -d deepcode_vsa \
  -c "SELECT thread_id FROM checkpoints WHERE thread_id = 'test-123';"

# Esperado: Ver checkpoint salvo
```

### Teste 2: Verificar Planner (após implementar)

```bash
# Enviar requisição IT
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "O servidor web01 está offline", "enable_itil": true}'

# Verificar logs
docker compose logs backend | grep "Planner"

# Esperado: Ver log "Planner node executing..." e plano gerado
```

### Teste 3: Verificar Performance

```bash
# Medir latência completa
time curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Liste tickets do GLPI", "enable_itil": true}'

# Esperado: < 5 segundos
```

---

## 📚 Referências

- **Arquivo:** `core/agents/unified.py`
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **PostgresSaver:** https://langchain-ai.github.io/langgraph/reference/checkpoints/#postgressaver
- **ADR-007:** Governança e Safe Execution
- **Task 2.6:** ActionPlan UI (frontend/src/components/app/ActionPlan.tsx)
- **Task 2.8:** WriteConfirmDialog UI (frontend/src/components/app/WriteConfirmDialog.tsx)

---

**Documento criado:** 2026-01-27
**Autor:** Claude Code
**Status:** Análise completa - aguardando implementação
**Próximo passo:** Implementar Fase 1 (Persistência) + Fase 2 (Planner)
