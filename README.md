# 🤖 DeepCode VSA

**Virtual Support Agent for IT Management**

Agente CLI inteligente para gestão de TI que conecta múltiplas APIs (GLPI, Zabbix) e aplica metodologias consolidadas (ITIL, GUT, RCA, 5W2H).

## ✨ Features

- 🧠 **LangGraph 1.0** - Arquitetura Planner-Executor-Reflector
- 📊 **Metodologias** - ITIL, GUT Matrix, RCA (5 Whys), 5W2H
- 🔌 **Integrações** - GLPI, Zabbix (extensível)
- 🎯 **LLM Híbrido** - 4 modelos via OpenRouter (custo otimizado)
- 🔒 **Governança** - Dry-run, audit logging, safety checks
- 💾 **Persistência** - PostgreSQL para histórico de sessões

## 🚀 Quick Start

### Instalação

```bash
# Usando uv (recomendado)
uv sync

# Ou pip
pip install -e .
```

### Configuração

```bash
# Copiar template de variáveis
cp .env.example .env

# Editar com suas credenciais
vim .env
```

### Uso

```bash
# Ver status das integrações
uv run vsa status

# Analisar com GUT Matrix
uv run vsa analyze "priorizar tickets críticos" --method gut

# Diagnosticar com RCA
uv run vsa diagnose "servidor web01 caindo frequentemente" --method rca

# Query livre
uv run vsa query "quantos tickets P1 abertos?"
```

## 📁 Estrutura

```
src/deepcode_vsa/
├── cli/            # CLI Typer + Rich
├── agent/          # LangGraph Agent
│   ├── state.py    # VSAAgentState
│   ├── graph.py    # StateGraph
│   └── nodes/      # Classifier, Planner, Executor, Analyzer
├── integrations/   # API Tools
│   ├── glpi/       # GLPI REST API
│   └── zabbix/     # Zabbix JSON-RPC
├── methodologies/  # ITIL, GUT, RCA, 5W2H
├── llm/            # OpenRouter client (híbrido)
├── governance/     # Safety, Audit
└── config/         # Settings (Pydantic)
```

## 🎛️ Modelos LLM

| Tier | Modelo | Uso |
|------|--------|-----|
| FAST | Llama 3.3 70B | Classificação, GUT |
| SMART | DeepSeek V3 | RCA, Planejamento |
| CREATIVE | Minimax M2 | Relatórios |
| PREMIUM | Claude 3.5 | Fallback |

## 📚 Documentação

- [PRD](docs/PRD.md) - Requisitos do produto
- [ADRs](docs/adr/) - Decisões de arquitetura
- [Skills](.claude/skills/) - Padrões de código

## 🛠️ Desenvolvimento

```bash
# Instalar dependências de dev
uv sync --all-extras

# Rodar testes
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run mypy src/
```

## 📄 License

MIT
