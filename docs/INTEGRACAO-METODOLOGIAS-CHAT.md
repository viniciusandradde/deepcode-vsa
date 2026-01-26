# Integração de Metodologias ITIL no Sistema de Chat

**Documento:** Guia de Implementação
**Objetivo:** Detalhar como integrar metodologias de gestão de TI (ITIL, GUT, RCA, 5W2H) no sistema de chat existente
**Autor:** Equipe DeepCode VSA
**Data:** Janeiro 2026

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura Proposta](#2-arquitetura-proposta)
3. [Fluxos de Conversação](#3-fluxos-de-conversação)
4. [Implementação Técnica](#4-implementação-técnica)
5. [Intents e Roteamento](#5-intents-e-roteamento)
6. [Prompts e Templates](#6-prompts-e-templates)
7. [Interface do Usuário](#7-interface-do-usuário)
8. [Exemplos de Código](#8-exemplos-de-código)

---

## 1. Visão Geral

### 1.1 Objetivo

Transformar o chat atual (SimpleAgent básico) em um **Assistente Inteligente de Gestão de TI** que:

- 🎯 **Detecta automaticamente** o tipo de demanda (Incident, Problem, Change, Request)
- 📊 **Prioriza usando GUT Matrix** (Gravidade, Urgência, Tendência)
- 🔍 **Consulta GLPI e Zabbix** quando relevante
- 🔗 **Correlaciona dados** entre sistemas
- 📝 **Aplica metodologias ITIL** nas respostas
- 🤖 **Sugere ações estruturadas** (RCA, 5W2H, PDCA)

### 1.2 Abordagem

```
Usuário → Chat → Intent Detection → Metodologia Aplicada → Execução de Tools → Resposta Estruturada
```

**Diferencial:** Não é apenas um chat com acesso a APIs - é um **analista virtual** que aplica frameworks de gestão de TI.

---

## 2. Arquitetura Proposta

### 2.1 Fluxo do Agente VSA no Chat

```
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND (ChatPane)                            │
│  Usuário digita: "O servidor web01 está com problemas"           │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                 BACKEND (/api/v1/chat/stream)                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                 VSAAgent (LangGraph)                        │  │
│  │                                                             │  │
│  │  START                                                      │  │
│  │    ↓                                                        │  │
│  │  ┌──────────────┐                                          │  │
│  │  │ CLASSIFIER   │  → Intent: INCIDENT                      │  │
│  │  │              │  → Category: Infraestrutura              │  │
│  │  │              │  → GUT Score: 125 (5,5,5)                │  │
│  │  └──────┬───────┘                                          │  │
│  │         ↓                                                   │  │
│  │  ┌──────────────┐                                          │  │
│  │  │ PLANNER      │  → Plan: [diagnóstico, correlação,       │  │
│  │  │              │           resolução, documentação]       │  │
│  │  └──────┬───────┘                                          │  │
│  │         ↓                                                   │  │
│  │  ┌──────────────┐                                          │  │
│  │  │ EXECUTOR     │  → Execute tools:                        │  │
│  │  │              │    - zabbix_get_alerts(host=web01)       │  │
│  │  │              │    - glpi_get_tickets(search=web01)      │  │
│  │  └──────┬───────┘                                          │  │
│  │         ↓                                                   │  │
│  │  ┌──────────────┐                                          │  │
│  │  │ ANALYZER     │  → Correlate:                            │  │
│  │  │              │    - Timeline analysis                   │  │
│  │  │              │    - Pattern detection                   │  │
│  │  └──────┬───────┘                                          │  │
│  │         ↓                                                   │  │
│  │  ┌──────────────┐                                          │  │
│  │  │ REFLECTOR    │  → Validate:                             │  │
│  │  │              │    - Goals achieved?                     │  │
│  │  │              │    - Need more info?                     │  │
│  │  └──────┬───────┘                                          │  │
│  │         ↓                                                   │  │
│  │  ┌──────────────┐                                          │  │
│  │  │ INTEGRATOR   │  → Generate:                             │  │
│  │  │              │    - Executive summary                   │  │
│  │  │              │    - Structured response (5W2H)          │  │
│  │  │              │    - Action recommendations              │  │
│  │  └──────┬───────┘                                          │  │
│  │         ↓                                                   │  │
│  │  END                                                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │ Streaming SSE
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND (ChatPane)                            │
│  Exibe resposta estruturada com badges, timeline, e recomendações│
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Integração com Chat Existente

**Modificação em `api/routes/chat.py`:**

```python
# ANTES (SimpleAgent)
agent = SimpleAgent(
    model_name=request.model,
    tools=[tavily_search] if request.use_tavily else [],
    checkpointer=checkpointer,
)

# DEPOIS (VSAAgent com metodologias)
from core.agents.vsa import VSAAgent
from core.tools.glpi import glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket
from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host

# Detectar automaticamente se deve usar VSA ou SimpleAgent
use_vsa = request.enable_vsa or _should_use_vsa(request.message)

if use_vsa:
    agent = VSAAgent(
        model_name=request.model,
        tools=[
            glpi_get_tickets,
            glpi_get_ticket_details,
            glpi_create_ticket,
            zabbix_get_alerts,
            zabbix_get_host,
        ],
        dry_run=True,  # Sempre dry_run por padrão
    )
else:
    agent = SimpleAgent(
        model_name=request.model,
        tools=[tavily_search] if request.use_tavily else [],
        checkpointer=checkpointer,
    )
```

---

## 3. Fluxos de Conversação

### 3.1 Fluxo: Incident Management

```
👤 "O servidor de email não está respondendo"

🤖 [CLASSIFIER]
   ✓ Intent: INCIDENT
   ✓ Categoria: Infraestrutura
   ✓ Urgência: 5 (Muito Alta)
   ✓ Impacto: 5 (Muito Alto - serviço crítico)
   ✓ GUT Score: 125

🤖 [PLANNER]
   Plano de Ação (ITIL Incident Management):
   1. Diagnóstico inicial
   2. Verificar alertas de monitoramento
   3. Verificar tickets relacionados
   4. Propor workaround se disponível
   5. Escalar se necessário

🤖 [EXECUTOR]
   🔍 Consultando Zabbix...
      ✓ Host: mail01
      ⚠️ Alertas ativos:
         - SMTP Service down (12:30)
         - High CPU usage (12:28)

   🔍 Consultando GLPI...
      ✓ Tickets relacionados a mail01:
         - #1245 "Email lento" (aberto 12:25)
         - #1240 "Não recebo emails" (aberto 12:27)

🤖 [ANALYZER]
   📊 Análise de Correlação:

   Timeline:
   12:28 → Alerta Zabbix: High CPU on mail01
   12:30 → Alerta Zabbix: SMTP Service down
   12:25 → Ticket GLPI #1245 (usuário: email lento)
   12:27 → Ticket GLPI #1240 (usuário: não recebe email)
   12:32 → Sua solicitação atual

   Padrão identificado: CPU alta → SMTP down → usuários afetados

🤖 [REFLECTOR]
   ✓ Diagnóstico completo
   ✓ Causa aparente identificada
   ⚠️ Resolução não executada (aguardando aprovação)

🤖 [INTEGRATOR]

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📋 RESUMO EXECUTIVO - Incident #mail01
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   🔴 CRITICIDADE: ALTA (GUT: 125)
   ⏰ TEMPO DE RESPOSTA: 2 minutos
   👥 IMPACTO: ~200 usuários (estimativa)

   📌 SITUAÇÃO:
   Servidor de email (mail01) com SMTP service down.
   CPU em 98% desde 12:28.

   🔍 EVIDÊNCIAS:
   - Alerta Zabbix: SMTP Service down (12:30)
   - Alerta Zabbix: High CPU usage (12:28)
   - 2 tickets GLPI de usuários afetados

   💡 CAUSA APARENTE:
   Processo consumindo CPU excessivamente, causando
   travamento do serviço SMTP.

   🎯 RECOMENDAÇÕES IMEDIATAS:

   1️⃣ WORKAROUND (5 min):
      - Restart do serviço SMTP
      - Comando: systemctl restart postfix
      - Risco: Baixo

   2️⃣ RESOLUÇÃO TEMPORÁRIA (15 min):
      - Identificar e matar processo problemático
      - Monitorar CPU após restart

   3️⃣ PRÓXIMOS PASSOS:
      - Criar ticket de Problem Management
      - Investigar causa raiz do CPU spike
      - Implementar monitoring adicional

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Deseja que eu:
   ✅ Crie um ticket de Incident no GLPI?
   ✅ Notifique a equipe de infraestrutura?
   ✅ Crie um Problem Management para RCA?
```

### 3.2 Fluxo: Problem Management (RCA)

```
👤 "Preciso entender por que o banco de dados fica lento toda segunda-feira"

🤖 [CLASSIFIER]
   ✓ Intent: PROBLEM
   ✓ Categoria: Performance
   ✓ Recorrência: Semanal (segunda-feira)
   ✓ GUT Score: 75 (Gravidade: 3, Urgência: 5, Tendência: 5)

🤖 [PLANNER]
   Plano de Investigação (ITIL Problem Management):
   1. Coletar evidências históricas
   2. Identificar padrões
   3. Aplicar RCA (5 Whys)
   4. Propor ações corretivas

🤖 [EXECUTOR]
   🔍 Consultando histórico Zabbix (últimas 4 segundas)...
      ✓ Padrão identificado:
         - Segunda 06/01: CPU 90% às 09:00-11:00
         - Segunda 13/01: CPU 95% às 09:00-11:00
         - Segunda 20/01: CPU 98% às 09:00-11:00
         - Segunda 27/01: CPU 99% às 09:00-11:00 (hoje)

   🔍 Consultando tickets GLPI relacionados...
      ✓ 8 tickets com keyword "lento" nas segundas
      ✓ Todos abertos entre 09:00 e 11:00

🤖 [ANALYZER - RCA]

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🔍 ROOT CAUSE ANALYSIS (5 Whys)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ❓ Por que o banco fica lento às segundas?
   ↳ 💬 CPU do servidor DB fica em 90%+ das 9h às 11h

   ❓ Por que a CPU fica alta nesse horário?
   ↳ 💬 Processo de backup pesado executando

   ❓ Por que o backup executa em horário de pico?
   ↳ 💬 Configuração padrão: segunda 09:00

   ❓ Por que não foi reconfigurado?
   ↳ 💬 Falta de visibilidade do impacto

   ❓ Por que falta visibilidade?
   ↳ 💬 Ausência de monitoramento de SLA

   ✅ CAUSA RAIZ IDENTIFICADA:
   Backup executando em horário de pico + falta de SLA monitoring

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 [INTEGRATOR]

   📋 ANÁLISE 5W2H
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   WHAT (O que?)
   → Lentidão recorrente no banco de dados

   WHY (Por que?)
   → Backup agendado em horário de pico de uso

   WHERE (Onde?)
   → Servidor db01 (banco de produção)

   WHEN (Quando?)
   → Todas as segundas-feiras, 09:00-11:00

   WHO (Quem?)
   → Impacta ~150 usuários do sistema ERP

   HOW (Como resolver?)
   → Reagendar backup para horário de baixo uso (02:00)
   → Implementar backup incremental
   → Adicionar SLA monitoring

   HOW MUCH (Quanto custa?)
   → Impacto atual: 2h downtime/semana = 8h/mês
   → Custo estimado de inatividade: R$ 5.000/mês
   → Investimento solução: 4h de trabalho técnico

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   💡 PLANO DE AÇÃO (PDCA)

   📌 PLAN (Planejar):
   1. Reagendar backup para 02:00
   2. Implementar backup incremental (diário)
   3. Configurar alertas de SLA

   ⚙️ DO (Fazer):
   - Alterar cron job de backup
   - Configurar incremental no script
   - Criar dashboard de SLA

   ✅ CHECK (Verificar):
   - Monitorar CPU nas próximas 4 segundas
   - Validar tempo de backup
   - Confirmar ausência de tickets de lentidão

   🔄 ACT (Agir):
   - Documentar procedimento
   - Criar runbook para futuros backups
   - Treinar equipe

   Deseja que eu crie um ticket de Change Management
   para implementar estas mudanças?
```

### 3.3 Fluxo: Correlação Multi-Sistema

```
👤 "Relacione os problemas do Zabbix com tickets do GLPI de hoje"

🤖 [CLASSIFIER]
   ✓ Intent: CORRELACAO
   ✓ Fontes: Zabbix + GLPI
   ✓ Período: Hoje (últimas 24h)

🤖 [EXECUTOR]
   🔍 Coletando dados...
      ✓ Zabbix: 12 alertas ativos
      ✓ GLPI: 18 tickets abertos hoje

   🔗 Correlacionando por hostname, timestamp, keywords...

🤖 [ANALYZER]

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📊 MAPA DE CORRELAÇÃO
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   🔴 GRUPO 1: Servidor web01
   ├─ ⚠️ Zabbix: CPU 98% (09:30)
   ├─ ⚠️ Zabbix: Memory 95% (09:32)
   ├─ 🎫 GLPI #1234: "Site lento" (09:35)
   ├─ 🎫 GLPI #1235: "Erro 503" (09:40)
   └─ 📈 Correlação: 95% (temporal + keywords)

   🟡 GRUPO 2: Servidor mail01
   ├─ ⚠️ Zabbix: SMTP down (10:15)
   ├─ 🎫 GLPI #1236: "Email não envia" (10:18)
   └─ 📈 Correlação: 90% (temporal + service)

   🟢 GRUPO 3: Impressora sala-204
   ├─ 🎫 GLPI #1237: "Impressora offline" (11:00)
   └─ 📈 Sem correlação Zabbix (device não monitorado)

   ⚪ Sem Correlação:
   ├─ 8 alertas Zabbix sem tickets GLPI
   └─ 13 tickets GLPI sem alertas Zabbix

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 [INTEGRATOR]

   💡 INSIGHTS:

   1️⃣ Alta correlação em servidores críticos (web01, mail01)
      → Boa integração Zabbix ↔ Service Desk

   2️⃣ 8 alertas Zabbix sem tickets
      → Possível: alertas resolvidos automaticamente
      → Ação: Verificar se precisam atenção

   3️⃣ 13 tickets sem alertas Zabbix
      → Possível: problemas de aplicação (não infraestrutura)
      → Ação: Avaliar necessidade de monitoring adicional

   4️⃣ Impressoras não monitoradas
      → Oportunidade: Adicionar impressoras ao Zabbix

   🎯 RECOMENDAÇÕES:

   ✅ Priorizar GRUPO 1 (web01) - impacto em produção
   ✅ Investigar 8 alertas Zabbix não reportados
   ✅ Adicionar monitoramento de impressoras
   ✅ Criar dashboard de correlação automática

   Deseja que eu gere um relatório executivo em PDF?
```

---

## 4. Implementação Técnica

### 4.1 Modificações no VSAAgent

**Arquivo: `core/agents/vsa.py`**

Adicionar método de integração com chat:

```python
class VSAAgent(BaseAgent):
    """VSA Agent with ITIL methodologies."""

    def __init__(
        self,
        model_name: str = "google/gemini-2.5-flash",
        tools: Optional[List[BaseTool]] = None,
        dry_run: bool = True,
        enable_streaming: bool = True,
    ):
        """Initialize VSA Agent with chat support."""
        super().__init__(...)
        self.dry_run = dry_run
        self.enable_streaming = enable_streaming

    async def astream_with_metadata(
        self,
        input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        """Stream responses with metadata for frontend rendering.

        Yields structured events:
        - {"type": "classification", "data": {...}}
        - {"type": "plan", "data": {...}}
        - {"type": "tool_call", "data": {...}}
        - {"type": "analysis", "data": {...}}
        - {"type": "content", "data": "..."}
        """
        graph = self.create_graph()

        async for event in graph.astream(input, config, stream_mode="updates"):
            # Transform LangGraph events to frontend-friendly format
            if "classifier" in event:
                yield {
                    "type": "classification",
                    "data": {
                        "intent": event["classifier"]["intent"],
                        "category": event["classifier"]["task_category"],
                        "priority": event["classifier"]["priority"],
                        "gut_score": event["classifier"]["gut_score"],
                    }
                }

            elif "planner" in event:
                yield {
                    "type": "plan",
                    "data": {
                        "steps": event["planner"]["plan"],
                        "methodology": event["planner"]["methodology"],
                    }
                }

            elif "executor" in event:
                for result in event["executor"]["tool_results"]:
                    yield {
                        "type": "tool_call",
                        "data": {
                            "tool": result["tool_name"],
                            "status": result["status"],
                            "output": result["output"],
                        }
                    }

            elif "analyzer" in event:
                yield {
                    "type": "analysis",
                    "data": event["analyzer"]["analysis"],
                }

            elif "integrator" in event:
                # Final response with complete structure
                yield {
                    "type": "final_response",
                    "data": {
                        "summary": event["integrator"]["summary"],
                        "recommendations": event["integrator"]["recommendations"],
                        "actions": event["integrator"]["suggested_actions"],
                        "audit_trail": event["integrator"]["audit"],
                    }
                }
```

### 4.2 Modificações no Endpoint de Chat

**Arquivo: `api/routes/chat.py`**

```python
@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Chat with VSA Agent - streaming with metadata."""
    from core.agents.vsa import VSAAgent
    from core.tools.glpi import glpi_get_tickets, glpi_create_ticket
    from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host

    try:
        # Determine which agent to use
        if request.enable_vsa:
            agent = VSAAgent(
                model_name=request.model or os.getenv("DEFAULT_MODEL_NAME"),
                tools=[
                    glpi_get_tickets,
                    glpi_create_ticket,
                    zabbix_get_alerts,
                    zabbix_get_host,
                ],
                dry_run=request.dry_run if hasattr(request, 'dry_run') else True,
            )
        else:
            # Fallback to SimpleAgent
            agent = SimpleAgent(...)

        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}

        async def generate():
            try:
                if request.enable_vsa and hasattr(agent, 'astream_with_metadata'):
                    # VSA Agent with structured events
                    async for event in agent.astream_with_metadata(
                        {"messages": [HumanMessage(content=request.message)]},
                        config=config
                    ):
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                else:
                    # SimpleAgent with basic streaming
                    async for chunk, metadata in agent.astream(...):
                        if isinstance(chunk, (AIMessage, AIMessageChunk)) and chunk.content:
                            data = {
                                "type": "content",
                                "content": chunk.content,
                                "thread_id": thread_id,
                            }
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

            except Exception as e:
                logger.error(f"Stream error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.3 Request Model Atualizado

**Arquivo: `api/models/requests.py`**

```python
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = None
    use_tavily: bool = False

    # VSA-specific fields
    enable_vsa: bool = False
    dry_run: bool = True
    enable_glpi: bool = False
    enable_zabbix: bool = False
```

---

## 5. Intents e Roteamento

### 5.1 Detecção de Intent

**Tipos de Intent para Gestão de TI:**

```python
class ITIntent(str, Enum):
    """IT Management intents."""
    INCIDENT = "incident"              # Problema operacional urgente
    PROBLEM = "problem"                # Investigação de causa raiz
    CHANGE = "change"                  # Mudança planejada
    REQUEST = "request"                # Solicitação de serviço
    QUERY_GLPI = "query_glpi"         # Consulta direta GLPI
    QUERY_ZABBIX = "query_zabbix"     # Consulta direta Zabbix
    CORRELATION = "correlation"        # Correlação multi-sistema
    CHAT = "chat"                      # Conversa geral
```

### 5.2 Prompt de Classificação

```python
CLASSIFIER_PROMPT = """Você é um especialista em ITIL v4.

Analise a mensagem do usuário e classifique em uma das categorias:

**INCIDENT**: Problema operacional que precisa resolução imediata
  Exemplos: "servidor offline", "sistema lento", "usuários sem acesso"

**PROBLEM**: Investigação de causa raiz de problemas recorrentes
  Exemplos: "sempre fica lento às segundas", "por que o backup falha"

**CHANGE**: Solicitação de mudança planejada
  Exemplos: "preciso atualizar o servidor", "vamos migrar para cloud"

**REQUEST**: Solicitação de serviço padrão
  Exemplos: "preciso acesso ao sistema", "criar conta de email"

**QUERY_GLPI**: Consulta direta ao GLPI
  Exemplos: "liste tickets", "mostre chamados abertos"

**QUERY_ZABBIX**: Consulta direta ao Zabbix
  Exemplos: "alertas críticos", "status do servidor"

**CORRELATION**: Correlacionar dados de múltiplos sistemas
  Exemplos: "relacione alertas com tickets", "mostre problemas correlacionados"

**CHAT**: Conversa geral sem ação específica
  Exemplos: "olá", "como funciona", "obrigado"

Além da classificação, calcule o GUT score:
- **Gravidade** (1-5): Impacto do problema
- **Urgência** (1-5): Pressão de tempo
- **Tendência** (1-5): Probabilidade de piorar

GUT Score = G × U × T

Responda APENAS com JSON:
{
  "intent": "...",
  "category": "...",
  "priority": "...",
  "gut": {"g": X, "u": Y, "t": Z, "score": XYZ}
}
"""
```

### 5.3 Roteamento Inteligente

```python
def _route_based_on_intent(state: VSAAgentState) -> str:
    """Route to appropriate handler based on intent."""
    intent = state.get("intent")

    if intent == ITIntent.INCIDENT:
        return "incident_handler"
    elif intent == ITIntent.PROBLEM:
        return "problem_handler"  # RCA workflow
    elif intent == ITIntent.CORRELATION:
        return "correlation_handler"
    elif intent in [ITIntent.QUERY_GLPI, ITIntent.QUERY_ZABBIX]:
        return "direct_query_handler"
    else:
        return "chat_handler"
```

---

## 6. Prompts e Templates

### 6.1 Prompt para Planner (Incident)

```python
INCIDENT_PLANNER_PROMPT = """Você é um especialista em ITIL Incident Management.

Contexto do Incident:
- Tipo: {intent}
- Categoria: {category}
- Prioridade GUT: {gut_score}
- Descrição: {user_message}

Crie um plano de ação seguindo ITIL:

1. **DIAGNÓSTICO**: Coletar informações
   - Verificar alertas de monitoramento
   - Consultar tickets relacionados
   - Identificar sistemas afetados

2. **CONTENÇÃO**: Ação imediata para reduzir impacto
   - Workaround disponível?
   - Isolamento necessário?

3. **RESOLUÇÃO**: Corrigir problema
   - Ação corretiva
   - Validação da resolução

4. **DOCUMENTAÇÃO**: Registrar
   - Criar/atualizar ticket GLPI
   - Documentar passos executados

5. **FOLLOW-UP**: Próximos passos
   - Necessidade de Problem Management?
   - Prevenção de recorrência

Responda com JSON:
{
  "steps": [
    {"phase": "diagnóstico", "action": "...", "tools": ["..."]},
    {"phase": "contenção", "action": "...", "tools": ["..."]},
    ...
  ],
  "estimated_time": "...",
  "requires_approval": true/false
}
"""
```

### 6.2 Prompt para RCA (Problem)

```python
RCA_PROMPT = """Você é um especialista em Root Cause Analysis (RCA).

Aplique a técnica dos **5 Whys** para investigar a causa raiz:

Problema: {problem_description}
Evidências coletadas: {evidence}

Formato de saída:

🔍 ROOT CAUSE ANALYSIS (5 Whys)

❓ Por que [problema]?
↳ 💬 [resposta 1]

❓ Por que [resposta 1]?
↳ 💬 [resposta 2]

❓ Por que [resposta 2]?
↳ 💬 [resposta 3]

❓ Por que [resposta 3]?
↳ 💬 [resposta 4]

❓ Por que [resposta 4]?
↳ 💬 [CAUSA RAIZ]

✅ CAUSA RAIZ IDENTIFICADA:
[Explicação detalhada]

💡 AÇÕES CORRETIVAS RECOMENDADAS:
1. [Ação 1]
2. [Ação 2]
3. [Ação 3]
"""
```

### 6.3 Template 5W2H

```python
TEMPLATE_5W2H = """
📋 ANÁLISE 5W2H

WHAT (O que?)
→ {what}

WHY (Por que?)
→ {why}

WHERE (Onde?)
→ {where}

WHEN (Quando?)
→ {when}

WHO (Quem?)
→ {who}

HOW (Como?)
→ {how}

HOW MUCH (Quanto?)
→ {how_much}
"""
```

---

## 7. Interface do Usuário

### 7.1 Badges e Indicadores Visuais

**Componente React para badges:**

```tsx
// frontend/src/components/app/ITILBadge.tsx
interface ITILBadgeProps {
  type: 'incident' | 'problem' | 'change' | 'request';
  gutScore?: number;
  priority?: 'critical' | 'high' | 'medium' | 'low';
}

export function ITILBadge({ type, gutScore, priority }: ITILBadgeProps) {
  const colors = {
    incident: 'bg-red-500',
    problem: 'bg-orange-500',
    change: 'bg-blue-500',
    request: 'bg-green-500',
  };

  return (
    <div className="flex items-center gap-2">
      <span className={`px-2 py-1 rounded-md text-white text-xs font-semibold ${colors[type]}`}>
        {type.toUpperCase()}
      </span>

      {gutScore && (
        <span className="px-2 py-1 rounded-md bg-gray-700 text-white text-xs">
          GUT: {gutScore}
        </span>
      )}

      {priority && (
        <span className={`px-2 py-1 rounded-md text-white text-xs ${
          priority === 'critical' ? 'bg-red-600' :
          priority === 'high' ? 'bg-orange-600' :
          priority === 'medium' ? 'bg-yellow-600' :
          'bg-gray-600'
        }`}>
          {priority.toUpperCase()}
        </span>
      )}
    </div>
  );
}
```

### 7.2 Timeline de Correlação

```tsx
// frontend/src/components/app/CorrelationTimeline.tsx
interface TimelineEvent {
  time: string;
  source: 'zabbix' | 'glpi' | 'user';
  description: string;
  severity?: 'critical' | 'warning' | 'info';
}

interface CorrelationTimelineProps {
  events: TimelineEvent[];
}

export function CorrelationTimeline({ events }: CorrelationTimelineProps) {
  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-sm">📈 Timeline de Eventos</h3>
      <div className="border-l-2 border-gray-300 pl-4 space-y-4">
        {events.map((event, idx) => (
          <div key={idx} className="relative">
            <div className="absolute -left-[21px] w-4 h-4 rounded-full bg-white border-2 border-gray-300" />
            <div className="text-xs text-gray-500">{event.time}</div>
            <div className={`text-sm ${
              event.severity === 'critical' ? 'text-red-600 font-semibold' :
              event.severity === 'warning' ? 'text-orange-600' :
              'text-gray-700'
            }`}>
              {event.source === 'zabbix' && '⚠️ '}
              {event.source === 'glpi' && '🎫 '}
              {event.source === 'user' && '👤 '}
              {event.description}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 7.3 Toggle VSA Mode

```tsx
// frontend/src/components/app/SettingsPanel.tsx

export function SettingsPanel() {
  const { enableVSA, setEnableVSA } = useGenesisUI();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Modo VSA (Gestão de TI)</h3>
          <p className="text-xs text-gray-500">
            Ativa metodologias ITIL, GUT, RCA e integração com GLPI/Zabbix
          </p>
        </div>
        <Switch
          checked={enableVSA}
          onCheckedChange={setEnableVSA}
        />
      </div>

      {enableVSA && (
        <div className="border-l-2 border-blue-500 pl-4 space-y-2">
          <div className="flex items-center gap-2">
            <Checkbox id="glpi" />
            <label htmlFor="glpi" className="text-sm">
              Habilitar GLPI Tools
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox id="zabbix" />
            <label htmlFor="zabbix" className="text-sm">
              Habilitar Zabbix Tools
            </label>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 8. Exemplos de Código

### 8.1 Integração Completa no ChatPane

```tsx
// frontend/src/components/app/ChatPane.tsx

async function handleSendMessage(message: string) {
  setIsSending(true);

  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        thread_id: currentSessionId,
        model: selectedModelId,
        enable_vsa: enableVSA,
        enable_glpi: enableGLPI,
        enable_zabbix: enableZabbix,
      }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    let accumulatedContent = '';
    let classification: any = null;
    let plan: any = null;
    let toolCalls: any[] = [];

    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n\n');

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const data = JSON.parse(line.slice(6));

        if (data.type === 'classification') {
          classification = data.data;
          // Exibir badge ITIL
          setCurrentClassification(classification);
        }
        else if (data.type === 'plan') {
          plan = data.data;
          // Exibir plano de ação
          setCurrentPlan(plan);
        }
        else if (data.type === 'tool_call') {
          toolCalls.push(data.data);
          // Exibir "Consultando GLPI..."
          setToolStatus(data.data);
        }
        else if (data.type === 'analysis') {
          // Exibir timeline/correlação
          setAnalysis(data.data);
        }
        else if (data.type === 'content') {
          accumulatedContent += data.content;
          // Streaming de texto
          setStreamingContent(accumulatedContent);
        }
        else if (data.type === 'final_response') {
          // Exibir resposta final estruturada
          setFinalResponse(data.data);
        }
        else if (data.type === 'done') {
          // Finalizar
          break;
        }
      }
    }
  } catch (error) {
    console.error('Error sending message:', error);
  } finally {
    setIsSending(false);
  }
}
```

### 8.2 Componente de Resposta Estruturada

```tsx
// frontend/src/components/app/StructuredResponse.tsx

interface StructuredResponseProps {
  classification?: {
    intent: string;
    priority: string;
    gut_score: number;
  };
  plan?: {
    steps: Array<{phase: string; action: string}>;
  };
  toolCalls?: Array<{tool: string; status: string; output: any}>;
  analysis?: any;
  finalResponse?: {
    summary: string;
    recommendations: string[];
    actions: string[];
  };
}

export function StructuredResponse({
  classification,
  plan,
  toolCalls,
  analysis,
  finalResponse,
}: StructuredResponseProps) {
  return (
    <div className="space-y-4">
      {classification && (
        <div className="border-l-4 border-red-500 pl-4">
          <ITILBadge
            type={classification.intent}
            gutScore={classification.gut_score}
            priority={classification.priority}
          />
        </div>
      )}

      {plan && (
        <div className="bg-blue-50 p-4 rounded-md">
          <h4 className="font-semibold mb-2">📋 Plano de Ação</h4>
          <ol className="list-decimal list-inside space-y-1">
            {plan.steps.map((step, idx) => (
              <li key={idx} className="text-sm">
                <strong>{step.phase}:</strong> {step.action}
              </li>
            ))}
          </ol>
        </div>
      )}

      {toolCalls && toolCalls.length > 0 && (
        <div className="space-y-2">
          {toolCalls.map((call, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">
                {call.status === 'running' ? '🔄' : '✓'}
              </span>
              <span>
                {call.tool === 'glpi_get_tickets' && 'Consultando GLPI...'}
                {call.tool === 'zabbix_get_alerts' && 'Consultando Zabbix...'}
              </span>
            </div>
          ))}
        </div>
      )}

      {analysis && analysis.timeline && (
        <CorrelationTimeline events={analysis.timeline} />
      )}

      {finalResponse && (
        <div className="border-t pt-4">
          <div className="prose prose-sm max-w-none">
            <h4>📋 Resumo Executivo</h4>
            <p>{finalResponse.summary}</p>

            {finalResponse.recommendations.length > 0 && (
              <>
                <h5>💡 Recomendações</h5>
                <ul>
                  {finalResponse.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </>
            )}

            {finalResponse.actions.length > 0 && (
              <>
                <h5>🎯 Próximas Ações</h5>
                <ul>
                  {finalResponse.actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Conclusão

Este documento fornece um guia completo para integrar metodologias de gestão de TI (ITIL, GUT, RCA, 5W2H) no sistema de chat existente. A implementação deve ser **gradual** e **iterativa**, começando com funcionalidades simples (consultas GLPI/Zabbix) e evoluindo para capacidades avançadas (correlação automática, RCA, planos de ação).

**Próximos passos:**
1. Revisar e aprovar este guia
2. Iniciar implementação da Fase 1 (Semanas 1-2)
3. Validar com usuários beta
4. Iterar baseado em feedback real

---

**Documento elaborado por:** Equipe DeepCode VSA
**Última atualização:** Janeiro 2026
