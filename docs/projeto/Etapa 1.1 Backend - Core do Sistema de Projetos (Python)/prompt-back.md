Esta é uma análise estratégica para elevar o módulo de projetos do DeepCode VSA ao nível dos "Claude Projects".O diferencial do sistema de Projetos do Claude (e do GPTs) reside em três pilares que precisamos replicar e aprimorar:Contexto Isolado (Scoped RAG): A IA só "vê" os documentos daquele projeto específico.Prompt de Sistema Dedicado: O usuário define "Quem é a IA" para aquele projeto (ex: "Você é um Arquiteto Senior Java").Persistência de Estado: O projeto mantém memória de chats passados e artefatos gerados.Abaixo, apresento a Análise de Gap e os Prompts de Implementação.🔍 Análise de Gap: DeepCode vs. Claude ProjectsRecursoDeepCode VSA (Atual)Claude Projects (Meta)Ação NecessáriaDefinição"Plans" ou "Threads" soltas.Container persistente de Config + Arquivos.Criar entidade Project no DB.PromptingPrompt fixo do Agente ou por mensagem.Custom Project Instructions (Prompt do Sistema injetável).Adicionar campo system_prompt no Projeto e injetar no Runtime do Agente.ConhecimentoRAG Global (mistura tudo).Project Knowledge (Arquivos isolados).Adicionar filtro project_id nas queries do Vector DB.InterfaceChat direto.Dashboard de Projeto com abas (Chat, Artefatos, Config).Criar "Project Studio" no Frontend.🧠 Arquitetura da SoluçãoDatabase: Tabela projects com colunas custom_instructions (o prompt exclusivo) e settings.RAG Engine: Atualizar o ingest para marcar vetores com project_id e o retriever para filtrar por ele.Agent Core: O UnifiedAgent precisa aceitar um project_context na inicialização para substituir seu System Prompt padrão pelo do projeto.

Atue como um **Arquiteto de IA e Backend Sênior**.

O objetivo é transformar o módulo de planejamento atual em um **"Project System"** similar ao do Claude. Precisamos que cada projeto tenha seu próprio "cérebro" (Custom Instructions) e "memória" (Scoped RAG).

Implemente as seguintes alterações no Backend (`backend/` e `core/`):

### 1. Modelagem de Dados (`sql/kb/08_projects_schema.sql`)

Crie uma migração SQL para a nova estrutura:

```sql
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    custom_instructions TEXT, -- O Prompt Exclusivo do Projeto
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Vincular Threads a Projetos
ALTER TABLE threads ADD COLUMN project_id UUID REFERENCES projects(id);

-- Vincular Documentos RAG a Projetos (Se sua tabela de docs for diferente, ajuste)
ALTER TABLE rag_documents ADD COLUMN project_id UUID REFERENCES projects(id);

2. Models & API (api/models/projects.py, api/routes/projects.py)
Crie modelos Pydantic: ProjectCreate, ProjectUpdate, ProjectResponse.

Crie um CRUD completo em api/routes/projects.py:

POST /projects: Criar projeto com custom_instructions.

POST /projects/{id}/upload: Endpoint para ingestão de arquivos RAG específicos deste projeto (chamar RagIngestion passando project_id).

GET /projects/{id}: Retornar detalhes + estatísticas de documentos.

3. Atualizar o Agente para Contexto (core/agents/unified.py)
Modifique o UnifiedAgent (ou VSAAgent) para aceitar contexto dinâmico:

Python

class UnifiedAgent:
    def __init__(self, project_id: str = None, ...):
        self.project_id = project_id
        # ...
    
    async def _build_system_prompt(self):
        base_prompt = load_default_prompt()
        
        if self.project_id:
            # Buscar instruções customizadas do banco
            project = await self.db.get_project(self.project_id)
            if project.custom_instructions:
                # O prompt do projeto tem precedência ou é anexado
                base_prompt = f"{base_prompt}\n\n=== PROJECT INSTRUCTIONS ===\n{project.custom_instructions}"
        
        return base_prompt
4. Scoped RAG (core/rag/tools.py)
Atualize a ferramenta de busca (search_knowledge_base ou similar) para filtrar obrigatoriamente pelo projeto atual:

Python

async def search(query: str, project_id: str = None):
    filters = {}
    if project_id:
        filters['project_id'] = project_id # Filtro de Metadados do VectorDB (Chroma/PGVector)
    
    return vector_store.similarity_search(query, filter=filters)
Requisito Crítico: Garanta que o Agente saiba que, se estiver dentro de um projeto, ele deve priorizar a busca no RAG filtrado por aquele ID.
