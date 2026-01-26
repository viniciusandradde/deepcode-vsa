# DeepCode VSA - Codebase Reference

> **Versão:** 1.0 | **Data:** Janeiro 2026 | **Status:** Em Desenvolvimento

---

## 🎯 Visão Geral

O **DeepCode VSA** (Virtual Support Agent) é um agente inteligente CLI em Python que apoia gestores de TI na análise, decisão e governança, conectando-se diretamente a múltiplas APIs (GLPI, Zabbix, Proxmox, Cloud, ERP, etc.).

### Proposta de Valor

> Transformar dados dispersos de APIs em decisões de gestão inteligentes, reduzindo o tempo de diagnóstico e aumentando a maturidade operacional de TI.

---

## 🏗️ Arquitetura

### Componentes Principais

```
┌────────────────────────────────────────────────────────────────────┐
│                         DeepCode VSA                                │
├────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                                                  │
│  │   CLI Layer  │  Typer + Rich                                    │
│  └──────┬───────┘                                                  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Agent Core (LangGraph)                     │ │
│  │  ┌─────────┐    ┌──────────┐    ┌───────────┐               │ │
│  │  │ Planner │───▶│ Executor │───▶│ Reflector │               │ │
│  │  └─────────┘    └──────────┘    └───────────┘               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   API Tool Registry                           │ │
│  │  ┌──────┐ ┌──────┐ ┌─────────┐ ┌───────┐ ┌─────┐           │ │
│  │  │ GLPI │ │Zabbix│ │ Proxmox │ │ Cloud │ │ ERP │  ...      │ │
│  │  └──────┘ └──────┘ └─────────┘ └───────┘ └─────┘           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────┐                                                  │
│  │  LLM Layer   │  OpenRouter (GPT-4, Claude, Llama, etc.)        │
│  └──────────────┘                                                  │
└────────────────────────────────────────────────────────────────────┘
```

### Padrão de Agente: Planner-Executor-Reflector

| Componente | Responsabilidade |
|------------|------------------|
| **Planner** | Decompõe problemas, identifica APIs, define sequência |
| **Executor** | Executa chamadas às APIs, gerencia erros |
| **Reflector** | Valida resultados, solicita re-planejamento, gera síntese |

---

## 📂 Estrutura de Diretórios (Planejada)

```
deepcode-vsa/
├── docs/                      # Documentação
│   ├── PRD.md                 # Product Requirements Document
│   ├── README.md              # Índice de documentação
│   └── adr/                   # Architecture Decision Records
│       ├── ADR-001 → ADR-009  # Decisões de arquitetura
│       └── README.md          # Template e índice
│
├── src/                       # Código fonte (a criar)
│   └── deepcode_vsa/
│       ├── __init__.py
│       ├── cli/               # Interface CLI (Typer + Rich)
│       │   ├── __init__.py
│       │   └── main.py
│       ├── agent/             # Core do agente (LangGraph)
│       │   ├── __init__.py
│       │   ├── graph.py       # Definição do grafo
│       │   ├── nodes/         # Planner, Executor, Reflector
│       │   └── state.py       # Estado do agente
│       ├── integrations/      # Integrações de API
│       │   ├── __init__.py
│       │   ├── base.py        # Classe base APITool
│       │   ├── registry.py    # Tool Registry
│       │   ├── glpi/          # Integração GLPI
│       │   └── zabbix/        # Integração Zabbix
│       ├── llm/               # Camada LLM
│       │   ├── __init__.py
│       │   └── openrouter.py
│       ├── governance/        # Regras de governança
│       │   ├── __init__.py
│       │   └── permissions.py
│       └── methodologies/     # ITIL, GUT, 5W2H
│           ├── __init__.py
│           └── gut.py
│
├── tests/                     # Testes
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── config/                    # Configurações
│   └── example.yaml
│
├── .agent/                    # Antigravity Kit
├── pyproject.toml             # Dependências (Poetry/uv)
└── README.md                  # README principal
```

---

## 🔧 Stack Tecnológico

| Camada | Tecnologia | Propósito |
|--------|------------|-----------|
| **CLI** | Typer + Rich | Interface de linha de comando |
| **Agente** | LangGraph | Orquestração de agente |
| **LLM** | OpenRouter | Gateway para múltiplos LLMs |
| **HTTP** | httpx | Chamadas HTTP assíncronas |
| **Validação** | Pydantic | Modelos de dados |
| **Config** | python-dotenv | Variáveis de ambiente |
| **Testes** | pytest + pytest-asyncio | Framework de testes |
| **Linting** | Ruff | Linter e formatter |
| **Types** | mypy | Type checking |

---

## 🔌 Integrações (API-First)

### Contrato Padrão (APITool)

```python
class APITool(ABC):
    name: str
    description: str
    operations: List[Operation]
    
    async def read(self, operation: str, params: dict) -> ToolResult
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult
```

### Integrações Planejadas

| Fase | Sistemas | Prioridade |
|------|----------|------------|
| **v1.0** | GLPI, Zabbix | Alta |
| **v1.1** | Proxmox, AWS | Média |
| **v1.2** | Azure, GCP, ERP | Média |

---

## 🛡️ Governança

| Operação | Comportamento | Requisitos |
|----------|---------------|------------|
| **READ** | Automático | Credenciais válidas |
| **WRITE** | Confirmação explícita | Dry-run + Aprovação |
| **DELETE** | Bloqueado (v1) | N/A |

---

## 📊 Metodologias Suportadas

- **ITIL v4**: Gestão de Incidentes, Problemas, Mudanças
- **GUT**: Gravidade, Urgência, Tendência
- **5W2H**: Estruturação de análises
- **PDCA**: Melhoria contínua
- **RCA**: Análise de causa raiz (5 Porquês)

---

## 📋 ADRs (Architecture Decision Records)

| ADR | Título | Status |
|-----|--------|--------|
| ADR-001 | CLI Local | ✅ Aprovado |
| ADR-002 | Python | ✅ Aprovado |
| ADR-003 | Agente Inteligente (Planner-Executor-Reflector) | ✅ Aprovado |
| ADR-004 | LangGraph | ✅ Aprovado |
| ADR-005 | API-First (sem MCP) | ✅ Aprovado |
| ADR-006 | API Tool Registry | ✅ Aprovado |
| ADR-007 | Governança (READ/WRITE/DELETE) | ✅ Aprovado |
| ADR-008 | OpenRouter | ✅ Aprovado |
| ADR-009 | Foco em Diagnóstico | ✅ Aprovado |

---

## 🚀 Roadmap

### Fase 1: MVP (v1.0) - Q1 2026

- [ ] CLI funcional
- [ ] Integração GLPI
- [ ] Integração Zabbix
- [ ] Agente LangGraph básico
- [ ] Documentação

### Fase 2: Expansão (v1.x) - Q2 2026

- [ ] Integração Proxmox
- [ ] Integração Cloud (AWS/Azure)
- [ ] Melhorias no Reflector

### Fase 3: Produto (v2.0) - Q3-Q4 2026

- [ ] API HTTP
- [ ] Web UI (opcional)
- [ ] Multi-tenancy

---

## 🔗 Dependências de Arquivos

| Arquivo | Depende de |
|---------|------------|
| `agent/graph.py` | `agent/nodes/*`, `agent/state.py` |
| `agent/nodes/executor.py` | `integrations/registry.py` |
| `integrations/*` | `integrations/base.py` |
| `cli/main.py` | `agent/graph.py` |

---

## 📝 Convenções de Código

- **Python 3.11+** com type hints completas
- **Async/await** para operações I/O
- **Pydantic v2** para validação de dados
- **Ruff** para linting e formatação
- **Docstrings** em formato Google
- **Testes** com pytest e AAA pattern

---

## 🤖 Ferramentas de Desenvolvimento

Este projeto utiliza duas ferramentas complementares para desenvolvimento assistido por IA:

### OpenCode (CLI)

Agente de código open source com TUI para terminal.

```bash
# Instalação
npm i -g opencode-ai@latest
# ou
brew install anomalyco/tap/opencode

# Uso
cd /path/to/deepcode-vsa
opencode
```

**Configuração:** `opencode.json`

| Recurso | Localização |
|---------|-------------|
| Agents | `.opencode/agents/*.md` |
| Skills | `.opencode/skills/*/SKILL.md` |
| Config | `opencode.json` |
| Instructions | `AGENTS.md` |

**Agentes Disponíveis:**

| Agente | Propósito |
|--------|-----------|
| `build` | Desenvolvimento com acesso total |
| `plan` | Análise sem modificações |
| `@vsa-developer` | Especialista DeepCode VSA |
| `@security-auditor` | Auditoria de segurança |

**Skills Disponíveis:**

| Skill | Descrição |
|-------|-----------|
| `vsa-development` | Padrões de desenvolvimento VSA |
| `glpi-integration` | Integração GLPI REST API |
| `zabbix-integration` | Integração Zabbix JSON-RPC |
| `langgraph-patterns` | Padrões LangGraph |

### Antigravity Kit (.agent)

Framework de agentes especializado com skills e workflows.

| Recurso | Localização |
|---------|-------------|
| Rules | `.agent/rules/GEMINI.md` |
| Agents | `.agent/agents/*.md` |
| Skills | `.agent/skills/*/SKILL.md` |
| Workflows | `.agent/workflows/*.md` |

**Comando Principal:** `/vsa`

**Agente Principal:** `@vsa-developer`

### Anthropic Claude Skills (.claude/)

Skills no formato oficial da Anthropic para uso com Claude Code e Claude.ai.

| Recurso | Localização |
|---------|-------------|
| Skills | `.claude/skills/*/SKILL.md` |

**Skills Disponíveis:**

| Skill | Descrição |
|-------|-----------|
| `vsa-development` | Padrões de desenvolvimento VSA |
| `vsa-agent-state` | VSAAgentState e nodes LangGraph |
| `vsa-methodologies` | ITIL, GUT Matrix, RCA, 5W2H |
| `vsa-safety-tools` | Safety checker e Computer Use tools |
| `vsa-cli-patterns` | CLI com Typer e Rich |
| `vsa-audit-compliance` | Audit logging e compliance |
| `vsa-external-integrations` | Linear, Telegram integrations |
| `vsa-llm-config` | LLM híbrido (Llama, DeepSeek, Minimax, Claude) |
| `glpi-integration` | Integração GLPI REST API |
| `zabbix-integration` | Integração Zabbix JSON-RPC |
| `langgraph-agent` | Padrões LangGraph |
| `api-patterns` | Padrões de API Python |
| `python-async` | Padrões async/await Python |

---

## 📁 Estrutura Completa do Projeto

```text
deepcode-vsa/
├── CODEBASE.md                    # Este documento
├── AGENTS.md                      # Instruções para OpenCode
├── opencode.json                  # Configuração OpenCode
│
├── docs/                          # Documentação
│   ├── PRD.md                     # Product Requirements
│   └── adr/                       # Architecture Decisions
│       └── ADR-001 → ADR-009
│
├── .claude/                       # Anthropic Claude Skills ✨
│   └── skills/
│       ├── vsa-development/SKILL.md
│       ├── glpi-integration/SKILL.md
│       ├── zabbix-integration/SKILL.md
│       ├── langgraph-agent/SKILL.md
│       ├── api-patterns/SKILL.md
│       └── python-async/SKILL.md
│
├── .opencode/                     # OpenCode resources
│   ├── agents/
│   │   ├── vsa-developer.md
│   │   └── security-auditor.md
│   └── skills/
│       ├── vsa-development/SKILL.md
│       ├── glpi-integration/SKILL.md
│       ├── zabbix-integration/SKILL.md
│       └── langgraph-patterns/SKILL.md
│
├── .agent/                        # Antigravity Kit
│   ├── ARCHITECTURE.md
│   ├── rules/GEMINI.md
│   ├── agents/vsa-developer.md
│   ├── skills/langgraph-agent/SKILL.md
│   └── workflows/vsa.md
│
├── src/deepcode_vsa/              # Código fonte (a criar)
│   ├── cli/
│   ├── agent/
│   ├── integrations/
│   ├── llm/
│   └── governance/
│
└── tests/                         # Testes
```

---

*Documento gerado para o projeto DeepCode VSA - Janeiro 2026*
