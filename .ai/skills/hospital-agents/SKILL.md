# Skill: Agentes Hospitalares com LangChain

## Descrição
Define como criar, configurar e implementar agentes de IA especializados para diferentes áreas hospitalares usando LangChain 1.0 + LangGraph.

## Contexto
- **Framework:** LangChain 1.0 + LangGraph
- **LLM:** OpenAI GPT-4 (principal) / Claude (alternativo)
- **Tools:** Acesso Wareline (read-only), ZigChat API, Redis cache
- **Canais:** WhatsApp (ZigChat), Dashboard, API REST

## Regras Obrigatórias

1. **NUNCA** diagnosticar ou prescrever medicação
2. **NUNCA** expor dados sensíveis de paciente (LGPD)
3. **SEMPRE** ter fallback para humano
4. **SEMPRE** registrar todas as interações
5. Em caso de dúvida na classificação de risco → classificar como MAIOR
6. Cada agente deve ter system prompt específico e tools definidos
7. Limite de tokens por resposta: 500 (conciso para WhatsApp)

## Arquitetura de Agentes

```
┌─────────────────────────────────────────────────┐
│              ROUTER PRINCIPAL                     │
│  (classifica intenção → despacha para agente)    │
└──────────────────────┬──────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ Agentes      │ │ Agentes  │ │ Agentes      │
│ Paciente     │ │ Clínicos │ │ Gestão       │
├──────────────┤ ├──────────┤ ├──────────────┤
│ • Atendim.   │ │ • Triag. │ │ • Financeiro │
│ • Agendamento│ │ • Enferm.│ │ • RH         │
│ • Ouvidoria  │ │ • Médico │ │ • Superint.  │
│ • Info Pac.  │ │ • CCIH   │ │              │
└──────────────┘ └──────────┘ └──────────────┘
       │               │               │
       └───────────────┼───────────────┘
                       ▼
              ┌──────────────────┐
              │   TOOLS COMUNS   │
              │  • query_wareline│
              │  • send_whatsapp │
              │  • check_cache   │
              │  • log_interaction│
              │  • escalate_human│
              └──────────────────┘
```

## Padrão Base de Agente

```python
# agents/base_agent.py
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

class BaseHospitalAgent:
    """Classe base para todos os agentes hospitalares."""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list,
        model: str = "gpt-4",
        temperature: float = 0.1,  # Baixa para consistência
        max_tokens: int = 500,     # Conciso para WhatsApp
    ):
        self.name = name
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = AgentExecutor(
            agent=self._create_agent(tools),
            tools=tools,
            verbose=False,  # True apenas em dev
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
    
    async def process(self, message: str, session: dict) -> str:
        """Processa mensagem do paciente/usuário."""
        try:
            result = await self.agent.ainvoke({
                "input": message,
                "chat_history": session.get("historico", []),
            })
            return result["output"]
        except Exception as e:
            # Fallback: resposta genérica + escalar para humano
            return (
                "Desculpe, não consegui processar sua solicitação. "
                "Vou transferir você para um atendente. Um momento, por favor."
            )
```

## Tools Comuns (Compartilhados entre Agentes)

```python
# agents/tools/common_tools.py
from langchain.tools import tool

@tool
async def consultar_paciente(cpf: str) -> str:
    """Busca dados básicos do paciente no Wareline pelo CPF.
    Retorna apenas dados não sensíveis (iniciais do nome, convênio ativo).
    """
    # Implementação com mascaramento LGPD
    pass

@tool
async def verificar_agendamentos(paciente_id: str, periodo: str) -> str:
    """Verifica agendamentos de consultas e exames do paciente.
    Retorna: data, hora, especialidade, médico, status.
    """
    pass

@tool
async def consultar_leitos_disponiveis(setor: str) -> str:
    """Verifica disponibilidade de leitos por setor.
    Retorna: quantidade disponível, setor, tipo.
    """
    pass

@tool
async def verificar_medico_plantao(especialidade: str) -> str:
    """Consulta qual médico está de plantão por especialidade.
    Retorna: nome do médico, especialidade, horário do plantão.
    """
    pass

@tool
async def registrar_protocolo(tipo: str, descricao: str) -> str:
    """Registra protocolo de atendimento.
    Retorna: número do protocolo gerado.
    """
    pass

@tool
async def escalar_para_humano(motivo: str, contexto: str) -> str:
    """Transfere o atendimento para atendente humano.
    Salva contexto da conversa para continuidade.
    """
    pass
```

## Lista de Agentes do Projeto

| # | Agente | Arquivo | Canal Principal | Prioridade |
|---|--------|---------|-----------------|------------|
| 1 | Atendimento ao Cliente | `agent-atendimento.md` | WhatsApp | 🔴 Alta |
| 2 | Agendamentos | `agent-agendamentos.md` | WhatsApp | 🔴 Alta |
| 3 | Triagem | `agent-triagem.md` | WhatsApp | 🔴 Alta |
| 4 | Informações ao Paciente | `agent-informacoes.md` | WhatsApp | 🟡 Média |
| 5 | Ouvidoria | `agent-ouvidoria.md` | WhatsApp | 🟡 Média |
| 6 | Financeiro/Faturamento | `agent-financeiro.md` | Dashboard/API | 🟡 Média |
| 7 | RH | `agent-rh.md` | WhatsApp | 🟢 Baixa |
| 8 | Superintendência | `agent-superintendencia.md` | Dashboard | 🟢 Baixa |

> Definições detalhadas de cada agente estão em `.ai/agents/`

## Anti-Padrões (NÃO FAZER)

- ❌ Agente diagnosticando doenças
- ❌ Agente prescrevendo medicação
- ❌ Agente acessando prontuário completo via WhatsApp
- ❌ Loops infinitos de agente (max_iterations=5)
- ❌ Temperature alta (> 0.3) para agentes de saúde
- ❌ Resposta longa no WhatsApp (> 500 tokens)
- ❌ Agente tomando decisão médica sem humano

## Métricas de Performance

| Métrica | Meta | Como Medir |
|---------|------|------------|
| Tempo de resposta | < 5 seg | Timer no webhook handler |
| Taxa de resolução | > 70% | Atendimentos sem escalação |
| Satisfação | > 4.0/5 | Pesquisa pós-atendimento |
| Escalação correta | > 95% | Revisão manual semanal |
| Uptime | > 99.5% | Monitoramento Prometheus |
