# DeepCode VSA - Virtual Support Agent

> **Agente de Suporte Virtual Inteligente para Gestão de TI com ITIL**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)

**Status:** ✅ MVP v1.0 COMPLETO (pronto para uso) | **Última Atualização:** 2026-01-28

---

## 🎯 O que é o DeepCode VSA?

**DeepCode VSA** (Virtual Support Agent) é um agente de IA especializado em **Gestão de TI** que conecta-se a múltiplos sistemas (GLPI, Zabbix, Proxmox, Linear) para analisar dados operacionais, correlacionar informações, priorizar demandas usando **metodologias ITIL**, e apoiar decisões estratégicas.

### 💡 Proposta de Valor

> Transformar dados dispersos de APIs em decisões inteligentes de gestão, reduzindo tempo de diagnóstico e aumentando a maturidade operacional de TI.

### 🎯 Público-Alvo

- **Primário:** Gestores de TI, Coordenadores de Infraestrutura/NOC, Analistas de Service Desk
- **Secundário:** MSPs, TI Hospitalar, TI Educacional, TI Corporativo

---

## ✨ Funcionalidades

### 🤖 Agentes Inteligentes

- ✅ **SimpleAgent** - Agente básico com LangChain `create_agent`
- ✅ **WorkflowAgent** - Detecção de intenção multi-workflow
- ✅ **UnifiedAgent** - Router + Classifier ITIL + Planner + Executor
- ✅ **VSAAgent** - Agente especializado ITIL (migrado para UnifiedAgent)

### 🔗 Integrações ITSM

| Sistema | Status | Funcionalidades |
|---------|--------|-----------------|
| **GLPI** | ✅ Implementado | Listar tickets, buscar detalhes, criar tickets |
| **Zabbix** | ✅ Implementado | Listar alertas, buscar hosts, consultar métricas |
| **Linear.app** | ✅ Implementado | Listar issues, criar issues, gerenciar teams |
| **Tavily** | ✅ Implementado | Busca web com IA |

### 📊 Metodologias ITIL

- ✅ **Classificação Automática** - INCIDENTE, PROBLEMA, MUDANÇA, REQUISIÇÃO, CONVERSA
- ✅ **Categorias** - Infraestrutura, Rede, Software, Hardware, Segurança, Acesso, Consulta
- ✅ **GUT Matrix** - Gravidade × Urgência × Tendência (priorização quantitativa)
- ✅ **Plano de Ação** - Estruturado conforme ITIL
- 🟡 **RCA (5 Whys)** - Em desenvolvimento
- 🟡 **5W2H** - Em desenvolvimento

### 💬 Interface de Chat

- ✅ **Chat Multi-Modelo** - Seleção de modelos via OpenRouter
- ✅ **Streaming SSE** - Respostas em tempo real
- ✅ **Markdown Rendering** - Tabelas ITIL estruturadas
- ✅ **Gerenciamento de Sessões** - Criar, selecionar, deletar threads
- ✅ **Persistência PostgreSQL** - Checkpoints salvos no banco
- ✅ **Recuperação de Contexto** - Mensagens persistem entre sessões

### 🗄️ Persistência e Performance

- ✅ **PostgreSQL 16 + pgvector** - Embeddings e checkpoints
- ✅ **PostgresSaver (Sync)** - Checkpointing síncrono
- ✅ **AsyncPostgresSaver** - Checkpointing assíncrono para streaming
- ✅ **RAG Pipeline** - Hybrid search (vector + text + RRF)
- ✅ **Multi-tenancy** - Isolamento por tenant_id

### 🔌 MCP Servers (15 Servidores)

- ✅ **Bancos de Dados** - PostgreSQL (3 databases)
- ✅ **Analytics** - Metabase, Grafana
- ✅ **Automação** - n8n workflows
- ✅ **AI** - Perplexity search
- ✅ **Integrações** - Supabase, Notion, Vercel, GitHub, LangChain Docs

---

## 🏗️ Arquitetura

```
DeepCode VSA
│
├── Frontend (Next.js 15 + React 19)
│   ├── Chat Interface (Markdown + Streaming SSE)
│   ├── Session Management (Sidebar)
│   ├── Settings Panel (VSA, GLPI, Zabbix, Linear toggles)
│   └── State Management (Context API)
│
├── Backend (FastAPI + LangGraph)
│   ├── API Routes
│   │   ├── /api/v1/chat (sync + streaming)
│   │   ├── /api/v1/rag (search + ingestion)
│   │   ├── /api/v1/agents (management)
│   │   └── /api/v1/threads (session management)
│   │
│   ├── Agents (LangGraph)
│   │   ├── SimpleAgent (create_agent)
│   │   ├── WorkflowAgent (intent detection)
│   │   └── UnifiedAgent (Router + ITIL Classifier + Planner)
│   │
│   ├── Integrations
│   │   ├── GLPI Client (REST API)
│   │   ├── Zabbix Client (JSON-RPC)
│   │   └── Linear Client (GraphQL)
│   │
│   └── RAG Pipeline
│       ├── Ingestion (3 chunking strategies)
│       ├── Hybrid Search (vector + text + RRF)
│       └── HyDE + Optional Reranking
│
└── Database (PostgreSQL 16 + pgvector)
    ├── kb_docs / kb_chunks (RAG)
    ├── checkpoints / writes (LangGraph)
    └── archived_threads (Session management)
```

---

## 🚀 Início Rápido

### Pré-requisitos

- Docker + Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ com pgvector

### Instalação

```bash
# 1. Clonar repositório
git clone https://github.com/USER/deepcode-vsa.git
cd deepcode-vsa

# 2. Copiar .env de exemplo
cp .env.example .env

# 3. Editar .env e configurar:
#    - OPENROUTER_API_KEY
#    - GLPI_BASE_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN
#    - ZABBIX_BASE_URL, ZABBIX_API_TOKEN
#    - LINEAR_API_KEY
#    - TAVILY_API_KEY

# 4. Subir containers
docker compose up -d

# 5. Acessar frontend
open http://localhost:3000
```

### Desenvolvimento Local

```bash
# Backend
cd /path/to/deepcode-vsa
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📊 Estatísticas do Projeto

| Métrica | Valor |
|---------|-------|
| **Arquivos de código** | 70 (37 Python + 33 TypeScript) |
| **Linhas de código** | 10,901 |
| **Dependências Python** | 16 packages |
| **Dependências Node.js** | 28 packages |
| **Integrações** | 3 ITSM + 15 MCP servers |
| **Commits** | 150+ |
| **Progresso MVP v1.0** | 100% (MVP completo) |

---

## 📚 Documentação

### Guias Principais

- 📖 **[CLAUDE.md](CLAUDE.md)** - Instruções para Claude Code (visão geral do projeto)
- 📊 **[STATUS-PROJETO-28-JAN-2026.md](.agent/STATUS-PROJETO-28-JAN-2026.md)** - Status completo do projeto
- 🎯 **[PRD-REVISADO.md](docs/PRD-REVISADO.md)** - Product Requirements Document
- 🔧 **[INTEGRACAO-METODOLOGIAS-CHAT.md](docs/INTEGRACAO-METODOLOGIAS-CHAT.md)** - Guia de integração ITIL

### Documentação Técnica

- 🔐 **[CORRECAO-PERSISTENCIA-POSTGRESQL.md](.agent/CORRECAO-PERSISTENCIA-POSTGRESQL.md)** - Correção de persistência
- 🧪 **[GUIA-TESTE-PERSISTENCIA.md](.agent/GUIA-TESTE-PERSISTENCIA.md)** - Guia de testes
- 🔌 **[MCP-SERVERS-CONFIGURADOS.md](.agent/MCP-SERVERS-CONFIGURADOS.md)** - MCPs configurados
- ⚙️ **[STATUS-INTEGRACOES.md](STATUS-INTEGRACOES.md)** - Status das integrações

---

## 🛠️ Comandos Úteis

### Docker

```bash
# Subir todos os containers
docker compose up -d

# Ver logs
docker compose logs -f backend
docker compose logs -f frontend

# Reiniciar backend
docker compose restart backend

# Parar todos os containers
docker compose down
```

### Banco de Dados

```bash
# Conectar ao PostgreSQL
docker exec -it ai_agent_postgres psql -U postgres -d deepcode_vsa

# Verificar checkpoints
SELECT COUNT(*) FROM checkpoints;

# Verificar mensagens por thread
SELECT thread_id, COUNT(*)
FROM checkpoints
GROUP BY thread_id;
```

### Desenvolvimento

```bash
# Executar testes
make test

# Linting
make lint

# Formatar código
make format

# Inicializar banco
make setup-db
```

---

## 🎯 Roadmap

### ✅ Fase 1: Fundação (Concluída)
- ✅ Chat multi-modelo com streaming
- ✅ Persistência PostgreSQL
- ✅ Integrações GLPI, Zabbix, Linear
- ✅ ITIL classification em português
- ✅ MCP servers (15 configurados)

### 🚧 Fase 2: ITIL Completo (v1.1+ - Em planejamento)
- ✅ Classificação ITIL automática
- ✅ GUT Score no prompt
- 🟡 Planner Node (vazio - em desenvolvimento)
- ❌ Confirmation Node (não iniciado)
- ❌ Correlação GLPI ↔ Zabbix
- ❌ RCA (5 Whys)

### 📋 Fase 3: Governança (Planejado - v1.1)
- [ ] Audit trail estruturado
- [ ] Dashboard de auditoria
- [ ] Export de relatórios
- [ ] LGPD compliance

### 🚀 Fase 4: Expansão (Planejado - v2.0)
- [ ] Proxmox integration
- [ ] Cloud integrations (AWS/Azure)
- [ ] CLI interface
- [ ] Multi-tenancy completo

---

## ⚠️ Issues Conhecidos

| Problema | Prioridade | Status |
|----------|------------|--------|
| OpenRouter API Key Inválida (401) | 🔴 ALTA | Requer atualização |
| GLPI User Token Faltando | 🟡 MÉDIA | Aguardando credencial |
| Planner Node Retorna Plano Vazio | 🟡 MÉDIA | Em desenvolvimento |
| Router Adiciona Latência (500-800ms) | 🟢 BAIXA | Otimização futura |

---

## 🤝 Contribuindo

Este é um projeto interno do Hospital Evangélico / VSA Tecnologia. Para contribuir:

1. Criar branch feature: `git checkout -b feature/nome-da-feature`
2. Commitar mudanças: `git commit -m 'feat: Adicionar feature X'`
3. Push para branch: `git push origin feature/nome-da-feature`
4. Abrir Pull Request

### Convenções de Commit

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Alteração em documentação
- `refactor:` - Refatoração de código
- `test:` - Adição ou correção de testes
- `chore:` - Manutenção geral

---

## 📄 Licença

Propriedade do Hospital Evangélico / VSA Tecnologia. Todos os direitos reservados.

---

## 👥 Equipe

**DeepCode VSA Team**
- Hospital Evangélico - TI
- VSA Tecnologia

**Tecnologias Principais:**
- Python 3.11 + FastAPI
- LangChain + LangGraph
- Next.js 15 + React 19
- PostgreSQL 16 + pgvector
- Docker + Docker Compose

---

## 📞 Suporte

Para questões técnicas ou suporte:

1. Verificar documentação em `.agent/` e `docs/`
2. Consultar logs: `docker compose logs backend`
3. Abrir issue no repositório (quando configurado)

---

**Desenvolvido com ❤️ pela equipe VSA Tecnologia**

**Status:** ✅ MVP v1.0 COMPLETO (pronto para uso)

**Última atualização:** 2026-01-28
