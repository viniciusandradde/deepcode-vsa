# Stack Template - Agente de IA + RAG

Template completo para desenvolvimento de agentes de IA com capacidades RAG (Retrieval-Augmented Generation).

**Status:** ✅ **Completo e Funcional** | **Versão:** 1.0.0 | **Última Atualização:** 2025-01-27

## Características

- **Agentes de IA**: Implementações simples e workflow-based usando LangChain 1.0 e LangGraph
  - ✅ `SimpleAgent` - Agente básico com `create_agent`
  - ✅ `WorkflowAgent` - Agente multi-intent completo
- **RAG Completo**: Pipeline de ingestão, busca híbrida (vector + text + RRF), reranking opcional
  - ✅ 3 estratégias de chunking (fixed, markdown, semantic)
  - ✅ HyDE (Hypothetical Document Embeddings)
  - ✅ Reranking com Cohere (opcional)
  - ✅ Multi-tenancy completo
- **API FastAPI**: Endpoints REST para chat, RAG e gerenciamento de agentes
  - ✅ Chat síncrono e streaming
  - ✅ Busca e ingestão RAG
  - ✅ Gerenciamento de agentes
- **PostgreSQL + pgvector**: Armazenamento de embeddings e busca semântica
  - ✅ Schema completo com índices otimizados
  - ✅ Funções SQL nativas para melhor performance
- **Configuração Dinâmica**: Middleware para troca dinâmica de modelos e ferramentas
- **Frontend Next.js**: Interface completa com chat avançado, gerenciamento de sessões e configuração dinâmica

## Estrutura

```
template/
├── core/              # Componentes principais
│   ├── agents/        # Implementações de agentes
│   ├── rag/           # Pipeline RAG completo
│   ├── tools/         # Ferramentas reutilizáveis
│   └── middleware/    # Middlewares
├── backend/           # Backend LangGraph
├── api/               # API FastAPI
├── scripts/           # Scripts de ingestão e teste
└── docs/              # Documentação

sql/kb/                # Schema PostgreSQL para RAG
```

## 🚀 Início Rápido

**Para iniciar rapidamente (5 minutos):** Veja [INICIO_RAPIDO.md](INICIO_RAPIDO.md)

**Para guia completo passo a passo:** Veja [COMO_INICIAR.md](COMO_INICIAR.md)

## Instalação

1. Instale as dependências Python:
```bash
cd template
pip install -r requirements.txt
```

2. Configure variáveis de ambiente (`.env`):
```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_agent_db
DB_USER=postgres
DB_PASSWORD=secret

# APIs
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
COHERE_API_KEY=...  # Opcional para reranking

# Checkpointing
USE_POSTGRES_CHECKPOINT=true
```

3. Configure o banco de dados:
```bash
# Execute os scripts SQL em ordem
psql -U postgres -d ai_agent_db -f sql/kb/01_init.sql
psql -U postgres -d ai_agent_db -f sql/kb/02_indexes.sql
psql -U postgres -d ai_agent_db -f sql/kb/03_functions.sql
```

## Uso Rápido

### Agente Simples

```python
from core.agents.simple import create_simple_agent
from core.tools.search import tavily_search

agent = create_simple_agent(
    model_name="google/gemini-2.5-flash",
    tools=[tavily_search],
    system_prompt="Você é um assistente útil."
)

result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Olá!"}]
})
```

### RAG Search

```python
from core.rag.tools import kb_search_client

results = kb_search_client.invoke({
    "query": "Como funciona o sistema?",
    "k": 5,
    "search_type": "hybrid",
    "empresa": "Minha Empresa"
})
```

### API FastAPI

```bash
cd template
uvicorn api.main:app --reload
```

Acesse `http://localhost:8000/docs` para ver a documentação interativa.

## Documentação

### Guias Principais
- [INICIO_RAPIDO.md](INICIO_RAPIDO.md) - Início ultra-rápido (5 min) ⚡
- [COMO_INICIAR.md](COMO_INICIAR.md) - Guia completo de inicialização 📖
- [QUICK_START.md](docs/QUICK_START.md) - Guia rápido de uso
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Arquitetura detalhada
- [AGENT_GUIDE.md](docs/AGENT_GUIDE.md) - Guia de desenvolvimento de agentes
- [RAG_GUIDE.md](docs/RAG_GUIDE.md) - Guia completo de RAG
- [ADICIONAR_MODELOS.md](docs/ADICIONAR_MODELOS.md) - Como adicionar modelos ao sistema 🤖
- [STATUS.md](docs/STATUS.md) - Status atual da implementação

### Documentos de Referência
- [docs/INDEX.md](docs/INDEX.md) - Índice completo de documentação
- [README_STATUS.md](README_STATUS.md) - Resumo executivo do status
- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças
- [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Checklist completo

## Status da Implementação

✅ **Template Completo e Funcional**

- ✅ Core Agents (BaseAgent, SimpleAgent, WorkflowAgent)
- ✅ RAG Pipeline completo (ingestão, busca híbrida, HyDE, reranking)
- ✅ API FastAPI com endpoints REST e streaming
- ✅ Backend LangGraph configurado
- ✅ Frontend Next.js básico configurado
- ✅ Scripts de ingestão e teste
- ✅ Schema PostgreSQL completo
- ✅ Documentação completa

Veja [docs/STATUS.md](docs/STATUS.md) para detalhes completos.

## Licença

MIT

