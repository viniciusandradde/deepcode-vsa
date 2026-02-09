"""Chat API routes."""

import asyncio
import re
import logging
import os
import uuid

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from api.models.requests import ChatRequest
from api.models.responses import ChatResponse
from core.agents.simple import SimpleAgent
from core.agents.unified import UnifiedAgent
from core.tools.search import tavily_search
from core.checkpointing import get_async_checkpointer

# Integration tools (Task 1.1)
from core.tools.glpi import glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket
from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host
from core.tools.linear import (
    linear_get_issues,
    linear_get_issue,
    linear_create_issue,
    linear_get_teams,
    linear_create_project,
    linear_create_full_project,
)
from core.tools.planning import PLANNING_TOOLS
from core.tools.planning_rag import search_project_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Tiered models: vêm de core/config.py (LLMSettings); env pode sobrescrever
# https://openrouter.ai/docs/guides/features/tool-calling


def _get_tool_capable_default() -> str:
    """Default para chamadas com ferramentas: TOOL_CAPABLE_MODEL ou config smart_model."""
    from core.config import get_settings

    return os.getenv("TOOL_CAPABLE_MODEL") or get_settings().llm.smart_model


def _resolve_model_for_request(request: ChatRequest, has_tools: bool) -> str:
    """Modelo da requisição: respeita request.model; senão DEFAULT_MODEL_NAME ou default do tier."""
    default = os.getenv("DEFAULT_MODEL_NAME") or _get_tool_capable_default()
    chosen = request.model or default
    if not chosen:
        chosen = "deepseek/deepseek-chat"
    if has_tools:
        logger.info(
            "[CHAT] Ferramentas ativas: modelo=%s (solicitado=%s, default tools=%s)",
            chosen,
            request.model or "(não informado)",
            _get_tool_capable_default(),
        )
    return chosen


def _resolve_fast_model() -> str:
    """Modelo barato para router/classifier (tiered): FAST_MODEL ou config fast_model."""
    from core.config import get_settings

    return os.getenv("FAST_MODEL") or get_settings().llm.fast_model


# Router por regras: detecta intenção de relatório para bypass LLM (zero tokens)
# Padrões específicos para evitar falsos positivos - devem ser comandos simples
# IMPORTANTE: patterns mais específicos devem vir ANTES dos genéricos
INTENT_PATTERNS = {
    # GLPI específico: "chamados novos sem atribuição" (deve vir antes do genérico)
    "glpi_new_unassigned": re.compile(
        r"^(chamados?|tickets?)\s+(novos?|abertos?)\s+sem\s+(atribui|tecnico)", re.I
    ),
    # GLPI específico: "chamados pendentes antigos" / "pendentes > 7 dias"
    "glpi_pending_old": re.compile(
        r"^(chamados?|tickets?)\s+pendentes?\s+(antigos?|velhos?|parados?|mais\s+de|\>\s*\d)", re.I
    ),
    # GLPI genérico: "tickets", "chamados", "listar tickets", "glpi", "glpi tickets"
    "glpi_tickets": re.compile(
        r"^(listar?|mostrar?|ver|exibir|buscar?)?\s*(os\s+)?(ultimos?\s+)?(\d+\s+)?"
        r"(tickets?|chamados?|glpi)(\s+(do\s+)?glpi|\s+abertos?|\s+novos?|\s+recentes?)?\.?$",
        re.I,
    ),
    # Zabbix: "alertas", "alertas zabbix", "zabbix alertas", "problemas zabbix"
    "zabbix_alerts": re.compile(
        r"^(listar?|mostrar?|ver|exibir|buscar?)?\s*(os\s+)?(ultimos?\s+)?(\d+\s+)?"
        r"(alertas?|problemas?|zabbix|alarmes?)(\s+(do\s+)?zabbix|\s+ativos?|\s+criticos?)?\.?$",
        re.I,
    ),
    # Dashboard: "dashboard", "visão geral", "status geral", "resumo"
    "dashboard": re.compile(
        r"^(mostrar?|ver|exibir)?\s*(o\s+)?"
        r"(dashboard|status\s*geral|visao\s*geral|resumo(\s+geral)?|painel)\.?$",
        re.I,
    ),
    # Linear: "issues", "issues linear", "tarefas", "backlog"
    "linear_issues": re.compile(
        r"^(listar?|mostrar?|ver|exibir|buscar?)?\s*(as\s+)?(ultimas?\s+)?(\d+\s+)?"
        r"(issues?|tarefas?|linear|backlog)(\s+(do\s+)?linear)?\.?$",
        re.I,
    ),
    # Análise composta: (DESATIVADO para permitir LLM)
    # "dashboard_analysis": re.compile(
    #    r"(an[aá]lis[ea]r?|relat[oó]rio|resumo|overview|revis[aã]o|fa[cç]a\s+an[aá]lise)"
    #    r"\s+(completa?\s+)?(d[aoe]s?\s+)?"
    #    r"(eventos?|semana|operac|incidentes?|atividades?|chamados?|alertas?)",
    #    re.I,
    #),
    # Relatório Excel Centro de Custo (Bypass LLM como solicitado)
    "glpi_excel_report": re.compile(
        r"^(gerar\s+)?relat[oó]rio\s+(excel\s+)?(de\s+)?(atendimentos\s+)?(por\s+)?centro\s+(de\s+)?custo",
        re.I
    ),
}


def _resolve_intent(message: str) -> str | None:
    """Se a mensagem for claramente um relatório conhecido, retorna o intent; senão None."""
    if not message or not message.strip():
        return None
    msg_lower = message.strip().lower()
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(msg_lower):
            return intent
    return None


CACHE_TTL = {
    "glpi_tickets": 120,         # 2 min
    "glpi_new_unassigned": 120,  # 2 min
    "glpi_pending_old": 300,     # 5 min — very stable data
    "zabbix_alerts": 60,         # 1 min — changes faster
    "linear_issues": 180,        # 3 min
    "dashboard": 90,             # 1.5 min — combines sources
    "dashboard_analysis": 90,
}

# Mapping from intent to artifact metadata for SSE artifact events
INTENT_ARTIFACT_META: dict[str, dict[str, str]] = {
    "glpi_tickets": {"title": "Relatório GLPI - Tickets", "artifact_type": "glpi_report"},
    "glpi_new_unassigned": {"title": "GLPI - Novos sem Atribuição", "artifact_type": "glpi_report"},
    "glpi_pending_old": {"title": "GLPI - Pendentes Antigos", "artifact_type": "glpi_report"},
    "zabbix_alerts": {"title": "Relatório Zabbix - Alertas", "artifact_type": "zabbix_report"},
    "linear_issues": {"title": "Relatório Linear - Issues", "artifact_type": "linear_report"},
    "dashboard": {"title": "Dashboard - Visão Geral", "artifact_type": "dashboard"},
    "dashboard_analysis": {"title": "Análise Operacional", "artifact_type": "dashboard"},
    "glpi_excel_report": {"title": "Relatório Excel", "artifact_type": "glpi_report"},
}


async def _generate_report_by_intent(intent: str, api_key: str | None = None) -> tuple[str, bool]:
    """Gera relatório via código (sem LLM) baseado no intent detectado.

    Returns:
        (markdown_report, success)
    """
    from core.cache import get_cached, set_cached
    from core.config import get_settings
    from core.reports import (
        format_glpi_report,
        format_zabbix_report,
        format_linear_report,
        format_new_unassigned_report,
        format_pending_old_report,
    )
    from core.reports.dashboard import format_dashboard_report

    # --- Redis cache check ---
    cache_key = f"report:{intent}"
    cached = get_cached(cache_key)
    if cached:
        logger.info("⚡ [CACHE HIT] intent=%s", intent)
        return cached["report"], cached["success"]

    report_md: str | None = None
    success = False

    try:
        settings = get_settings()
        glpi_base_url = settings.glpi.base_url if settings.glpi.enabled else None
        zabbix_base_url = settings.zabbix.base_url if settings.zabbix.enabled else None

        if intent == "glpi_new_unassigned":
            from core.tools.glpi import get_client

            client = get_client()
            result = await client.get_tickets_new_unassigned(min_age_hours=24, limit=20)
            if result.success:
                report_md = format_new_unassigned_report(
                    result.output, glpi_base_url=glpi_base_url
                )
                success = True
            else:
                report_md = f"**Erro GLPI:** {result.error}"

        elif intent == "glpi_pending_old":
            from core.tools.glpi import get_client

            client = get_client()
            result = await client.get_tickets_pending_old(min_age_days=7, limit=20)
            if result.success:
                report_md = format_pending_old_report(result.output, glpi_base_url=glpi_base_url)
                success = True
            else:
                report_md = f"**Erro GLPI:** {result.error}"

        elif intent == "glpi_tickets":
            from core.tools.glpi import get_client

            client = get_client()
            result = await client.get_tickets(limit=15)
            if result.success:
                report_md = format_glpi_report(result.output, glpi_base_url=glpi_base_url)
                success = True
            else:
                report_md = f"**Erro GLPI:** {result.error}"

        elif intent == "zabbix_alerts":
            from core.tools.zabbix import get_client

            client = get_client()
            result = await client.get_problems(limit=15, severity=3)
            if result.success:
                data = {"problems": result.output, "count": len(result.output), "min_severity": 3}
                report_md = format_zabbix_report(data, zabbix_base_url=zabbix_base_url)
                success = True
            else:
                report_md = f"**Erro Zabbix:** {result.error}"

        elif intent == "linear_issues":
            from core.tools.linear import get_client

            client = get_client()
            result = await client.get_issues(limit=15)
            if result.success:
                report_md = format_linear_report(result.output)
                success = True
            else:
                report_md = f"**Erro Linear:** {result.error}"

        elif intent == "glpi_excel_report":
            # Gera link para download direto via endpoint dedicado
            # Endpoint adicionado em reports.router: /api/v1/reports/glpi/cost-center/excel
            
            # Não precisamos gerar o arquivo aqui, apenas retornar o link.
            # O endpoint fará a geração sob demanda (streaming).
            
            download_url = "/api/v1/reports/glpi/cost-center/excel"
            from core.reports.excel import get_previous_month_range
            start_date, end_date = get_previous_month_range()
            
            # Append api_key if provided
            url_with_auth = download_url
            if api_key and api_key != "dev-mode":
                url_with_auth = f"{download_url}?api_key={api_key}"

            report_md = f"""
### 📊 Relatório Disponível

O relatório **Atendimentos por Centro de Custo ({start_date} a {end_date})** pode ser baixado abaixo.

[📥 Baixar Arquivo Excel]({url_with_auth})
"""
            success = True
            filename = "relatorio.xlsx" # Dummy for API compat if needed, though not used here
            # Para evitar erro de unbound local variable se 'filename' for usado depois?
            # O código original usava 'filename' no f-string.
            # Aqui já construímos o report_md.

        elif intent in ("dashboard", "dashboard_analysis"):
            glpi_data = None
            zabbix_data = None

            try:
                from core.tools.glpi import get_client as get_glpi_client

                client = get_glpi_client()
                result = await client.get_tickets(limit=15)
                if result.success:
                    glpi_data = result.output
                else:
                    glpi_data = {"error": result.error}
            except Exception as e:
                glpi_data = {"error": str(e)}

            try:
                from core.tools.zabbix import get_client as get_zabbix_client

                client = get_zabbix_client()
                result = await client.get_problems(limit=15, severity=3)
                if result.success:
                    zabbix_data = {
                        "problems": result.output,
                        "count": len(result.output),
                        "min_severity": 3,
                    }
                else:
                    zabbix_data = {"error": result.error}
            except Exception as e:
                zabbix_data = {"error": str(e)}

            report_md = format_dashboard_report(
                glpi_data=glpi_data,
                zabbix_data=zabbix_data,
                glpi_base_url=glpi_base_url,
                zabbix_base_url=zabbix_base_url,
            )
            success = True

    except Exception as e:
        logger.exception("Report generation failed for intent %s: %s", intent, e)
        report_md = f"**Erro ao gerar relatório:** {e}"
        success = False

    # --- Cache successful results ---
    if success and report_md:
        ttl = CACHE_TTL.get(intent, 120)
        set_cached(cache_key, {"report": report_md, "success": success}, ttl)
        logger.info("📦 [CACHE SET] intent=%s ttl=%ds", intent, ttl)

    return report_md, success


def _fetch_project_context(query: str, project_id: str) -> str | None:
    try:
        return search_project_knowledge.invoke(
            {
                "query": query,
                "project_id": project_id,
            }
        )
    except Exception as e:
        logger.warning("Project RAG fetch failed: %s", e)
        return None


# Phase 2: ITIL System Prompt for VSA Mode (compressed: core + examples on demand)
VSA_CORE_PROMPT = """Você é o **DeepCode VSA** (Virtual Support Agent), especialista em Gestão de TI (ITIL, GUT).

## Papel
Classifique em ITIL (INCIDENTE, PROBLEMA, MUDANÇA, REQUISIÇÃO, CONVERSA). Priorize com GUT (G×U×T). Use ferramentas GLPI/Zabbix/Linear para dados reais. Apresente resultados em tabelas markdown.

## Tipos ITIL (português)
INCIDENTE: interrupção/degradação de serviço. PROBLEMA: causa raiz. MUDANÇA: alteração planejada. REQUISIÇÃO: serviço padrão. CONVERSA: geral.

## Categorias
Infraestrutura, Rede, Software, Hardware, Segurança, Acesso, Consulta.

## Fluxo
1. CLASSIFICAÇÃO (tipo + GUT) 2. PLANO DE AÇÃO 3. EXECUÇÃO (ferramentas) 4. RESULTADO (tabelas + recomendações).

## Regras
- Use TABELAS MARKDOWN para dados (GLPI, Zabbix, classificação).
- Seja direto e técnico. Cite IDs reais (Ticket #N, etc).
- Sem dados: diga "Nenhum registro encontrado" ou "Erro ao consultar".
- **Criar projeto no Linear:** Use linear_get_teams para obter team_id. Gere o plano (project + milestones + tasks) em JSON e chame linear_create_full_project(team_id, project_plan, dry_run=True). Mostre o preview ao usuário e diga que pode confirmar. Na confirmação do usuário, você DEVE chamar linear_create_full_project novamente com o MESMO JSON de project_plan que usou no preview (copie o JSON exato da sua resposta anterior). Nunca chame com project_plan vazio.

## Anti-alucinação
NUNCA invente dados. IDs, nomes, datas e status vêm EXCLUSIVAMENTE das ferramentas. Se ferramenta falhar, peça ao usuário verificar configurações."""

VSA_EXAMPLES_PROMPT = """

## Exemplos de planos
INCIDENTE: Coleta (GLPI+Zabbix) → Diagnóstico → Resolução → Documentação.
PROBLEMA: Coleta → RCA (5 Porquês) → Ação corretiva → Documentação.
MUDANÇA: Impacto → Planejamento → Validação → Documentação.
REQUISIÇÃO: Validação → Execução → Verificação → Documentação.
CONVERSA: Entendimento → Resposta → Encaminhamento se necessário.

## Formato de resposta (tabelas)
### CLASSIFICAÇÃO ITIL: | Campo | Valor | (Tipo, Categoria, GUT Score, Prioridade)
### PLANO DE AÇÃO: Metodologia + Etapas numeradas
### EXECUÇÃO E RESULTADOS: Resumo (Total/Novo/Processando/Resolvido), tabela de tickets/alertas, Atenção Prioritária
### RECOMENDAÇÕES: Ação imediata, Próximos passos, Prevenção."""


def get_system_prompt(enable_vsa: bool, include_examples: bool = False) -> str:
    """Get appropriate system prompt based on VSA mode. include_examples=False saves ~50% input tokens.
    Prompt is kept stable (date only, no time) so OpenRouter can cache it; check usage.cached_tokens in responses.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Date only (no time) so prefix is stable for prompt caching across requests in the same day
    data_atual = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")
    suffix = f"\n\nData: {data_atual} (São Paulo)"

    if enable_vsa:
        prompt = VSA_CORE_PROMPT
        if include_examples:
            prompt = prompt + VSA_EXAMPLES_PROMPT
        return prompt + suffix


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - synchronous."""
    # Note: verify_api_key is checked in router dependencies.
    # We can get it from env if needed for report links, 
    # as the header isn't easily accessible here without Depends(verify_api_key).
    from api.middleware.auth import get_api_key
    api_key = get_api_key()
    try:
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

        # === RULE-BASED ROUTER: Zero LLM tokens for known report intents ===
        # Check if message matches a known report pattern (GLPI, Zabbix, Linear, Dashboard)
        intent = _resolve_intent(request.message)
        if intent:
            logger.info("📊 [RULE-ROUTER] Intent detectado: %s (bypass LLM)", intent)
            report_md, success = await _generate_report_by_intent(intent, api_key=api_key)
            if success and report_md:
                return ChatResponse(
                    response=report_md,
                    thread_id=thread_id,
                    model="rule-based",  # Indicates no LLM was used
                )
            # If report generation failed, fall through to LLM
            logger.warning("⚠️ Report generation failed, falling back to LLM")

        # === LLM PATH: Use agent for complex/unknown intents ===
        # Get checkpointer (initialized via lifespan)
        checkpointer = get_async_checkpointer()

        # Create agent with tools (Task 1.1 - Dynamic tools)
        tools = []
        if request.use_tavily:
            tools.append(tavily_search)

        # GLPI tools (Task 1.2)
        if request.enable_glpi:
            tools.extend([glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket])
            logger.info("✅ GLPI tools enabled")

        # Zabbix tools (Task 1.3)
        if request.enable_zabbix:
            tools.extend([zabbix_get_alerts, zabbix_get_host])
            logger.info("✅ Zabbix tools enabled")

        # Linear tools
        if request.enable_linear:
            tools.extend(
                [
                    linear_get_issues,
                    linear_get_issue,
                    linear_create_issue,
                    linear_get_teams,
                    linear_create_project,
                    linear_create_full_project,
                ]
            )
            logger.info("✅ Linear tools enabled")

        # Planning tools
        if request.enable_planning:
            tools.extend(PLANNING_TOOLS)
            logger.info("✅ Planning tools enabled")

        # DeepCode Projects: RAG scoped to project
        if request.project_id:
            tools.append(search_project_knowledge)
            logger.info("✅ Project RAG enabled (project_id=%s)", request.project_id)

        has_tools = bool(tools)
        model_name = _resolve_model_for_request(request, has_tools)

        system_prompt = get_system_prompt(request.enable_vsa) or ""
        if request.project_id:
            system_prompt += (
                f"\n\nCONTEXTO ATIVO: Você está no projeto {request.project_id}. "
                "Use a ferramenta 'search_project_knowledge' para dúvidas sobre este projeto."
            )
            project_context = _fetch_project_context(request.message, request.project_id)
            if project_context:
                system_prompt += f"\n\nCONTEXTO RECUPERADO DO PROJETO:\n{project_context}"

        # Select agent based on VSA mode (Task 1.13: UnifiedAgent)
        if request.enable_vsa:
            agent = UnifiedAgent(
                model_name=model_name,
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=system_prompt,
                enable_itil=False,
                enable_planning=False,
                fast_model_name=_resolve_fast_model(),
            )
            logger.info("🤖 Using UnifiedAgent (ITIL mode)")
        else:
            agent = SimpleAgent(
                model_name=model_name,
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=system_prompt,
            )
            logger.info("🤖 Using SimpleAgent")

        # Invoke agent
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]}, config=config
        )

        # Extract response
        messages = result.get("messages", [])
        response_text = messages[-1].content if messages else "No response generated"

        return ChatResponse(response=response_text, thread_id=thread_id, model=request.model)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Chat endpoint - streaming (SSE)."""
    from fastapi.responses import StreamingResponse
    import json

    # Generate thread_id if not provided
    thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

    # === RULE-BASED ROUTER: Zero LLM tokens for known report intents ===
    from api.middleware.auth import get_api_key
    api_key = get_api_key()
    intent = _resolve_intent(request.message)
    if intent:
        logger.info("📊 [RULE-ROUTER/STREAM] Intent detectado: %s (bypass LLM)", intent)

        async def generate_report_stream():
            """Stream do relatório gerado por código (simula streaming).

            Emits artifact_start / artifact_content / artifact_end SSE events
            so the frontend can render the report in a side panel, followed by
            a compact content event for the chat bubble.
            """
            try:
                # Enviar evento start
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"

                report_md, success = await _generate_report_by_intent(intent, api_key=api_key)

                if success and report_md:
                    # --- Artifact SSE events ---
                    artifact_id = f"art-{uuid.uuid4().hex[:12]}"
                    meta = INTENT_ARTIFACT_META.get(intent, {
                        "title": "Relatório",
                        "artifact_type": "generic_report",
                    })

                    # artifact_start
                    yield f"data: {json.dumps({'type': 'artifact_start', 'thread_id': thread_id, 'artifact': {'artifact_id': artifact_id, 'title': meta['title'], 'artifact_type': meta['artifact_type'], 'intent': intent, 'source': 'rule-based'}}, ensure_ascii=False)}\n\n"

                    # artifact_content in chunks
                    chunk_size = 400
                    for i in range(0, len(report_md), chunk_size):
                        chunk = report_md[i : i + chunk_size]
                        yield f"data: {json.dumps({'type': 'artifact_content', 'thread_id': thread_id, 'artifact_id': artifact_id, 'content': chunk}, ensure_ascii=False)}\n\n"

                    # artifact_end
                    yield f"data: {json.dumps({'type': 'artifact_end', 'thread_id': thread_id, 'artifact_id': artifact_id}, ensure_ascii=False)}\n\n"

                    # Chat bubble summary (compact message that references the artifact)
                    summary = f"Relatório gerado com sucesso."
                    yield f"data: {json.dumps({'type': 'content', 'content': summary, 'thread_id': thread_id, 'model': 'rule-based', 'artifact_id': artifact_id}, ensure_ascii=False)}\n\n"
                else:
                    # Erro: envia como conteúdo normal
                    data = {
                        "type": "content",
                        "content": report_md or "Erro ao gerar relatório",
                        "thread_id": thread_id,
                        "model": "rule-based",
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                # Evento done
                yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"

            except asyncio.CancelledError:
                logger.debug("Report stream cancelled (client disconnected)")
                raise
            except Exception as e:
                logger.exception("Report stream error: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(generate_report_stream(), media_type="text/event-stream")

    # === LLM PATH: Use agent for complex/unknown intents ===
    try:
        # Get checkpointer (initialized via lifespan)
        checkpointer = get_async_checkpointer()

        # Create agent with tools (Task 1.1 - Dynamic tools)
        tools = []
        if request.use_tavily:
            tools.append(tavily_search)

        # GLPI tools (Task 1.2)
        if request.enable_glpi:
            tools.extend([glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket])
            logger.info("✅ GLPI tools enabled (stream)")

        # Zabbix tools (Task 1.3)
        if request.enable_zabbix:
            tools.extend([zabbix_get_alerts, zabbix_get_host])
            logger.info("✅ Zabbix tools enabled (stream)")

        # Linear tools
        if request.enable_linear:
            tools.extend(
                [
                    linear_get_issues,
                    linear_get_issue,
                    linear_create_issue,
                    linear_get_teams,
                    linear_create_project,
                    linear_create_full_project,
                ]
            )
            logger.info("✅ Linear tools enabled (stream)")

        # Planning tools
        if request.enable_planning:
            tools.extend(PLANNING_TOOLS)
            logger.info("✅ Planning tools enabled (stream)")

        # DeepCode Projects: RAG scoped to project
        if request.project_id:
            tools.append(search_project_knowledge)
            logger.info("✅ Project RAG enabled (project_id=%s) [stream]", request.project_id)

        has_tools = bool(tools)
        model_name = _resolve_model_for_request(request, has_tools)

        system_prompt = get_system_prompt(request.enable_vsa) or ""
        if request.project_id:
            system_prompt += (
                f"\n\nCONTEXTO ATIVO: Você está no projeto {request.project_id}. "
                "Use a ferramenta 'search_project_knowledge' para dúvidas sobre este projeto."
            )
            project_context = _fetch_project_context(request.message, request.project_id)
            if project_context:
                system_prompt += f"\n\nCONTEXTO RECUPERADO DO PROJETO:\n{project_context}"

        # Select agent based on VSA mode (Task 1.13: UnifiedAgent)
        if request.enable_vsa:
            agent = UnifiedAgent(
                model_name=model_name,
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=system_prompt,
                enable_itil=False,
                enable_planning=False,
                fast_model_name=_resolve_fast_model(),
            )
            logger.info("🤖 Using UnifiedAgent (ITIL mode) [stream]")
        else:
            agent = SimpleAgent(
                model_name=model_name,
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=system_prompt,
            )
            logger.info("🤖 Using SimpleAgent [stream]")

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        def _content_to_str(content):
            """Normalize chunk content to string (LangChain can send str or list of blocks)."""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, str):
                        parts.append(block)
                    elif isinstance(block, dict) and "text" in block:
                        parts.append(block["text"])
                return "".join(parts)
            return str(content) if content else ""

        async def generate():
            try:
                # Enviar evento "start" imediatamente para o cliente saber que a conexão está viva
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
                logger.info("[STREAM] Sent start event, waiting for LLM...")

                from langchain_core.messages import AIMessage, AIMessageChunk

                # Use stream_mode="messages" to get deltas (tokens) for a smoother experience
                async for chunk, metadata in agent.astream(
                    {"messages": [HumanMessage(content=request.message)]},
                    config=config,
                    stream_mode="messages",
                ):
                    # In 'messages' mode, chunk is typically a message delta (AIMessageChunk)
                    if isinstance(chunk, (AIMessage, AIMessageChunk)) and chunk.content:
                        # Only stream AI content, skipping tool calls and metadata
                        if not hasattr(chunk, "tool_calls") or not chunk.tool_calls:
                            content_str = _content_to_str(chunk.content)
                            if content_str:
                                data = {
                                    "type": "content",
                                    "content": content_str,
                                    "thread_id": thread_id,
                                    "model": request.model,
                                }
                                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                logger.info("[STREAM] Sending done event")
                yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"

            except asyncio.CancelledError:
                # Client disconnected or request cancelled - do not log as error
                logger.debug("Stream cancelled (client disconnected)")
                raise
            except Exception as e:
                logger.error(f"Stream error: {str(e)}", exc_info=True)
                # Try to extract a clean string from the exception
                error_msg = str(e)
                if hasattr(e, "body") and isinstance(e.body, dict):
                    error_msg = e.body.get("message", error_msg)
                elif "API key USD spend limit exceeded" in error_msg:
                    error_msg = "Limite de gastos da chave API do OpenRouter excedido. Verifique suas configurações de 'Spending Limit' no OpenRouter."

                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")
