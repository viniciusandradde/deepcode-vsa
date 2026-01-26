# DeepCode VSA - Documentação

**Agente Inteligente CLI para Gestão de TI**

---

## Visão Geral

O DeepCode VSA é um agente inteligente em CLI (Linux, Python) que apoia gestores de TI na análise, decisão e governança, conectando-se diretamente a múltiplas APIs (GLPI, Zabbix, Proxmox, Cloud, ERP, etc.).

### Características Principais

- **API-First**: Integração direta com sistemas de TI
- **Agente Inteligente**: Planner → Executor → Reflector
- **Governança**: READ automático, WRITE controlado
- **Metodologias**: ITIL, GUT, 5W2H, PDCA

---

## Índice de Documentação

### Produto

| Documento | Descrição |
|-----------|-----------|
| [PRD - Product Requirements Document](./PRD.md) | Requisitos completos do produto |

### Arquitetura

| ADR | Título | Status |
|-----|--------|--------|
| [ADR-001](./adr/ADR-001-cli-local.md) | CLI Local | Aprovado |
| [ADR-002](./adr/ADR-002-python.md) | Python | Aprovado |
| [ADR-003](./adr/ADR-003-agente-inteligente.md) | Agente Inteligente | Aprovado |
| [ADR-004](./adr/ADR-004-langgraph.md) | LangGraph | Aprovado |
| [ADR-005](./adr/ADR-005-api-first.md) | API-First | Aprovado |
| [ADR-006](./adr/ADR-006-api-registry.md) | API Registry | Aprovado |
| [ADR-007](./adr/ADR-007-governanca.md) | Governança | Aprovado |
| [ADR-008](./adr/ADR-008-openrouter.md) | OpenRouter | Aprovado |
| [ADR-009](./adr/ADR-009-foco-diagnostico.md) | Foco em Diagnóstico | Aprovado |

---

## Arquitetura de Alto Nível

```
┌────────────────────────────────────────────────────────────────────┐
│                         DeepCode VSA                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
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
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

| Camada | Tecnologia | Propósito |
|--------|------------|-----------|
| CLI | Typer + Rich | Interface de linha de comando |
| Agente | LangGraph | Orquestração de agente |
| LLM | OpenRouter | Gateway para múltiplos LLMs |
| HTTP | httpx | Chamadas HTTP assíncronas |
| Validação | Pydantic | Modelos de dados |
| Config | python-dotenv | Variáveis de ambiente |

---

## Integrações Suportadas

### v1.0 (Inicial)

| Sistema | Tipo | Operações |
|---------|------|-----------|
| GLPI | ITSM | READ, WRITE |
| Zabbix | Monitoramento | READ |

### Roadmap

| Versão | Sistemas |
|--------|----------|
| v1.1 | Proxmox, AWS |
| v1.2 | Azure, GCP |
| v2.0 | Custom APIs |

---

## Modelo de Governança

| Operação | Comportamento | Requisitos |
|----------|---------------|------------|
| **READ** | Automático | Credenciais válidas |
| **WRITE** | Controlado | Dry-run + Confirmação |
| **DELETE** | Bloqueado | N/A (v1) |

---

## Metodologias Suportadas

- **ITIL v4**: Gestão de Incidentes, Problemas, Mudanças
- **GUT**: Gravidade, Urgência, Tendência
- **5W2H**: Estruturação de análises
- **PDCA**: Melhoria contínua
- **RCA**: Análise de causa raiz (5 Porquês)

---

## Quick Start

```bash
# Instalação
pip install deepcode-vsa

# Configuração
export OPENROUTER_API_KEY="your-key"
export GLPI_URL="https://glpi.empresa.com"
export GLPI_APP_TOKEN="your-token"

# Uso
deepcode-vsa analyze "avaliar riscos operacionais"
```

---

## Contribuição

Para contribuir com a documentação:

1. Fork o repositório
2. Crie uma branch para sua alteração
3. Submeta um Pull Request

### Padrões de Documentação

- ADRs seguem o template em [adr/README.md](./adr/README.md)
- Markdown com formatação GitHub-flavored
- Diagramas em ASCII quando possível

---

## Contato

- **Projeto**: DeepCode VSA
- **Versão**: 1.0 (em desenvolvimento)
- **Data**: Janeiro 2026

---

*Documentação mantida pela equipe DeepCode VSA*
