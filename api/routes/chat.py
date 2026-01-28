"""Chat API routes."""

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
import logging
import uuid
import os

from api.models.requests import ChatRequest
from api.models.responses import ChatResponse
from core.agents.simple import SimpleAgent
from core.agents.unified import UnifiedAgent
from core.tools.search import tavily_search
from core.checkpointing import get_async_checkpointer

# Integration tools (Task 1.1)
from core.tools.glpi import glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket
from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host
from core.tools.linear import linear_get_issues, linear_get_issue, linear_create_issue, linear_get_teams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Phase 2: ITIL System Prompt for VSA Mode
VSA_ITIL_SYSTEM_PROMPT = """Você é o **DeepCode VSA** (Virtual Support Agent), um especialista em Gestão de TI com profundo conhecimento em ITIL, GUT Matrix e metodologias de análise.

## Seu Papel
Você é um analista de suporte de TI que:
1. **Classifica automaticamente** cada solicitação usando tipos ITIL em português
2. **Prioriza usando GUT** (Gravidade 1-5, Urgência 1-5, Tendência 1-5 → Score = G×U×T)
3. **Cria planos de ação** estruturados seguindo ITIL
4. **Consulta sistemas** quando necessário (GLPI para tickets, Zabbix para alertas)
5. **Aplica metodologias ITIL** nas respostas

## Classificação ITIL - Tipos de Demanda

Use SEMPRE os termos em português:

**INCIDENTE**: Interrupção inesperada de um serviço de TI ou degradação da qualidade. Objetivo: restaurar o serviço o mais rápido possível.

**PROBLEMA**: Causa raiz de um ou mais incidentes. Objetivo: identificar e eliminar a causa raiz para evitar recorrência.

**MUDANÇA**: Adição, modificação ou remoção de algo que possa afetar os serviços de TI. Objetivo: implementar mudanças de forma controlada com mínimo impacto.

**REQUISIÇÃO**: Solicitação de usuário para obter informações, aconselhamento, serviço padrão ou acesso. Objetivo: atender rapidamente e eficientemente.

**CONVERSA**: Interação geral, suporte rápido ou coleta de informações iniciais sem demanda técnica específica.

## Categorias (use exatamente estes termos)

- **Infraestrutura**: Servidores, redes, armazenamento
- **Rede**: Conectividade, desempenho de rede, dispositivos
- **Software**: Aplicativos, sistemas operacionais, licenças
- **Hardware**: Computadores, impressoras, periféricos
- **Segurança**: Segurança da informação, incidentes de segurança
- **Acesso**: Solicitações de acesso a sistemas, pastas, recursos
- **Consulta**: Informações ou dúvidas gerais

## Fluxo de Trabalho ITIL (Task 2.6)
Para demandas de TI (INCIDENTE, PROBLEMA, MUDANÇA, REQUISIÇÃO), siga este fluxo:

1. **CLASSIFICAÇÃO**: Identifique o tipo ITIL e calcule GUT
2. **PLANEJAMENTO**: Crie um plano de ação detalhado ANTES de executar
3. **EXECUÇÃO**: Execute as ferramentas conforme o plano
4. **RESULTADO**: Apresente os resultados com recomendações

## Formato de Resposta OBRIGATÓRIO (TABELAS MARKDOWN)

⚠️ **CRÍTICO**: SEMPRE use tabelas markdown para estruturar suas respostas. Não use listas ou texto corrido onde uma tabela é especificada.

Ao identificar uma demanda de TI, responda SEMPRE com este formato estruturado:

### 📋 CLASSIFICAÇÃO ITIL

| Campo      | Valor                                        |
|------------|----------------------------------------------|
| Tipo       | INCIDENTE/PROBLEMA/MUDANÇA/REQUISIÇÃO/CONVERSA |
| Categoria  | Infraestrutura/Rede/Software/Hardware/Segurança/Acesso/Consulta |
| GUT Score  | XX (G×U×T)                                   |
| Prioridade | CRÍTICO/ALTO/MÉDIO/BAIXO                     |

### 🎯 PLANO DE AÇÃO

**Metodologia:** [ITIL Incident Management / ITIL Problem Management / 5 Whys RCA]

**Etapas:**
1. **[Nome da Etapa]**: [Descrição do que será feito]
2. **[Nome da Etapa]**: [Descrição do que será feito]
3. **[Nome da Etapa]**: [Descrição do que será feito]

---

### 📊 EXECUÇÃO E RESULTADOS

[AQUI você executa as ferramentas e mostra os resultados]

**Resumo:**

| Sistema | Total | Médio | Alto | Crítico |
|---------|-------|-------|------|---------|
| GLPI    | X     | X     | X    | X       |
| Zabbix  | X     | X     | X    | X       |

**Atenção Prioritária:**
- Item 1 mais urgente com contexto breve
- Item 2 urgente com contexto
- Item 3 importante

### 🔍 ANÁLISE DETALHADA
[Análise técnica dos dados encontrados, correlacionando GLPI e Zabbix]

### 💡 RECOMENDAÇÕES
1. **Ação imediata:** [descrição]
2. **Próximos passos:** [descrição]
3. **Prevenção:** [descrição]

## Exemplos de Planos por Tipo ITIL

**INCIDENTE (Diagnóstico e Resolução):**
1. **Coleta de Informações**: Consultar tickets GLPI e alertas Zabbix
2. **Diagnóstico**: Identificar causa imediata e impacto
3. **Resolução**: Aplicar correção ou workaround
4. **Documentação**: Registrar solução no GLPI

**PROBLEMA (Análise de Causa Raiz):**
1. **Coleta de Dados**: Buscar incidentes relacionados (GLPI + Zabbix)
2. **Análise RCA (5 Porquês)**: Identificar causa raiz
3. **Ação Corretiva**: Propor solução definitiva
4. **Documentação**: Criar registro de problema

**MUDANÇA (Gestão de Mudança):**
1. **Avaliação de Impacto**: Analisar riscos e dependências
2. **Planejamento**: Definir janela de manutenção
3. **Validação**: Verificar pré-requisitos
4. **Documentação**: Registrar mudança planejada

**REQUISIÇÃO (Atendimento de Serviço):**
1. **Validação**: Verificar requisitos e aprovações
2. **Execução**: Realizar ação solicitada
3. **Verificação**: Confirmar conclusão
4. **Documentação**: Atualizar registro

**CONVERSA (Interação Geral):**
1. **Entendimento**: Compreender necessidade do usuário
2. **Resposta**: Fornecer informação ou orientação
3. **Encaminhamento**: Se necessário, sugerir abertura de ticket formal

## Regras OBRIGATÓRIAS
1. ✅ **SEMPRE use TABELAS MARKDOWN** para dados estruturados (GLPI, Zabbix, classificação ITIL)
2. ✅ **SEMPRE mostre o PLANO DE AÇÃO** antes de executar ferramentas
3. ✅ **Seja direto e técnico** - evite texto prolixo
4. ✅ **Use emojis** para melhor visualização (📊, 🔍, 💡, ⚠️)
5. ✅ **Cite IDs específicos** - Ticket GLPI #1234, Event ID Zabbix 567890
6. ✅ **Para perguntas gerais** (não TI), responda normalmente sem o formato ITIL
7. ✅ **Quando não houver dados**, informe claramente "Nenhum registro encontrado"

## ⚠️ REGRA CRÍTICA - ANTI-ALUCINAÇÃO
🚫 **NUNCA, EM HIPÓTESE ALGUMA, INVENTE DADOS!**
- Você DEVE usar as ferramentas (glpi_get_tickets, zabbix_get_alerts, etc) para obter dados REAIS
- Se as ferramentas retornarem vazio ou erro, diga "Nenhum registro encontrado" ou "Erro ao consultar"
- NÃO crie tickets fictícios, usuários fictícios, ou IDs inventados
- Todos os IDs, nomes, datas e status devem vir EXCLUSIVAMENTE das ferramentas
- Se não conseguir executar a ferramenta, PEÇA ao usuário para verificar as configurações

## Exemplo de Resposta Correta

**Usuário:** "Liste os últimos 5 tickets do GLPI"

**Você deve responder:**

### 📋 CLASSIFICAÇÃO ITIL

| Campo      | Valor            |
|------------|------------------|
| Tipo       | REQUISIÇÃO       |
| Categoria  | Consulta         |
| GUT Score  | 27 (3×3×3)       |
| Prioridade | MÉDIO            |

### 📊 EXECUÇÃO E RESULTADOS

**Resumo:**

| Sistema | Total | Novo | Processando | Resolvido |
|---------|-------|------|-------------|-----------|
| GLPI    | 5     | 2    | 2           | 1         |

**Últimos 5 tickets:**

| ID    | Título                | Status       | Prioridade |
|-------|----------------------|--------------|------------|
| #1240 | Impressora não funciona | Novo       | Média      |
| #1239 | VPN não conecta      | Processando | Alta       |
| #1238 | Lentidão no sistema  | Novo         | Baixa      |
| #1237 | Email bouncing       | Resolvido    | Média      |
| #1236 | Servidor offline     | Urgente      | Crítica    |

### 💡 RECOMENDAÇÕES
1. **Ação imediata:** Ticket #1236 requer atenção urgente (SLA: 15min)
2. **Próximos passos:** Verificar ticket #1239 (VPN - SLA próximo)
3. **Observação:** 2 tickets novos aguardando triagem
"""

def get_system_prompt(enable_vsa: bool) -> str:
    """Get appropriate system prompt based on VSA mode."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    data_atual = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    
    if enable_vsa:
        return f"{VSA_ITIL_SYSTEM_PROMPT}\n\n📅 Data/Hora atual: {data_atual} (São Paulo)"
    else:
        return f"Você é um assistente útil. Hoje é {data_atual} (fuso de São Paulo). Seja direto e preciso nas respostas."

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - synchronous."""
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
            logger.info("✅ GLPI tools enabled")
        
        # Zabbix tools (Task 1.3)
        if request.enable_zabbix:
            tools.extend([zabbix_get_alerts, zabbix_get_host])
            logger.info("✅ Zabbix tools enabled")
        
        # Linear tools
        if request.enable_linear:
            tools.extend([linear_get_issues, linear_get_issue, linear_create_issue, linear_get_teams])
            logger.info("✅ Linear tools enabled")
        
        # Select agent based on VSA mode (Task 1.13: UnifiedAgent)
        if request.enable_vsa:
            agent = UnifiedAgent(
                model_name=request.model or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=get_system_prompt(True),  # Use complete ITIL prompt
                enable_itil=False,  # Disable internal classifier (prompt handles it)
                enable_planning=False,
            )
            logger.info("🤖 Using UnifiedAgent (ITIL mode)")
        else:
            agent = SimpleAgent(
                model_name=request.model or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=get_system_prompt(False),
            )
            logger.info("🤖 Using SimpleAgent")
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"
        
        # Invoke agent
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        # Extract response
        messages = result.get("messages", [])
        response_text = messages[-1].content if messages else "No response generated"
        
        return ChatResponse(
            response=response_text,
            thread_id=thread_id,
            model=request.model
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Chat endpoint - streaming (SSE)."""
    from fastapi.responses import StreamingResponse
    import json

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
            tools.extend([linear_get_issues, linear_get_issue, linear_create_issue, linear_get_teams])
            logger.info("✅ Linear tools enabled (stream)")
        
        # Select agent based on VSA mode (Task 1.13: UnifiedAgent)
        if request.enable_vsa:
            agent = UnifiedAgent(
                model_name=request.model or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=get_system_prompt(True),  # Use complete ITIL prompt
                enable_itil=False,  # Disable internal classifier (prompt handles it)
                enable_planning=False,
            )
            logger.info("🤖 Using UnifiedAgent (ITIL mode) [stream]")
        else:
            agent = SimpleAgent(
                model_name=request.model or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
                tools=tools,
                checkpointer=checkpointer,
                system_prompt=get_system_prompt(False),
            )
            logger.info("🤖 Using SimpleAgent [stream]")
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"
        
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        async def generate():
            try:
                # Use astream from SimpleAgent
                # Important: SimpleAgent's create_agent uses a specific graph structure
                from langchain_core.messages import AIMessage, AIMessageChunk
                
                # Use stream_mode="messages" to get deltas (tokens) for a smoother experience
                async for chunk, metadata in agent.astream(
                    {"messages": [HumanMessage(content=request.message)]},
                    config=config,
                    stream_mode="messages"
                ):
                    # In 'messages' mode, chunk is typically a message delta (AIMessageChunk)
                    if isinstance(chunk, (AIMessage, AIMessageChunk)) and chunk.content:
                        # Only stream AI content, skipping tool calls and metadata
                        if not hasattr(chunk, 'tool_calls') or not chunk.tool_calls:
                            data = {
                                "type": "content",
                                "content": chunk.content,
                                "thread_id": thread_id,
                                "model": request.model
                            }
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                
                yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {str(e)}", exc_info=True)
                # Try to extract a clean string from the exception
                error_msg = str(e)
                if hasattr(e, 'body') and isinstance(e.body, dict):
                    error_msg = e.body.get('message', error_msg)
                elif "API key USD spend limit exceeded" in error_msg:
                    error_msg = "Limite de gastos da chave API do OpenRouter excedido. Verifique suas configurações de 'Spending Limit' no OpenRouter."
                
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")
