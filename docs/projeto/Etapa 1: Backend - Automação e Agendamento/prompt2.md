Arquitetura da Solução
Database: Tabela projects com colunas custom_instructions (o prompt exclusivo) e settings.

RAG Engine: Atualizar o ingest para marcar vetores com project_id e o retriever para filtrar por ele.

Agent Core: O UnifiedAgent precisa aceitar um project_context na inicialização para substituir seu System Prompt padrão pelo do projeto.

📝 Prompt 1: Backend - Core do Sistema de Projetos (Python)
Copie e cole este prompt para criar a inteligência do sistema.

Markdown

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


---

### 🎨 Prompt 2: Frontend - "Project Studio" Interface

**Copie e cole este prompt para criar a interface visual.**

```markdown
Atue como um **Product Designer e Frontend Engineer (Next.js)**.

Vamos criar a interface **"Project Studio"** no DeepCode VSA. A experiência deve ser fluida como no Claude Projects.

Implemente as seguintes telas e componentes em `frontend/`:

### 1. Dashboard de Projetos (`src/app/projects/page.tsx`)
- **Visual:** Grid de cartões usando a classe `.glass-panel`.
- **Card do Projeto:**
  - Título, Descrição curta.
  - Badges: "X Arquivos", "Última atividade: 2h atrás".
  - Cor de destaque (Laranja/Azul) baseada na marca.
- **Ação:** Botão "Novo Projeto" que abre um Dialog.

### 2. Configuração de Novo Projeto (Dialog)
- **Nome & Descrição.**
- **Instruções Personalizadas (A "Alma" do Projeto):**
  - Um `Textarea` grande e com destaque.
  - Placeholder: *"Ex: Neste projeto, você é um Arquiteto de Software focado em microsserviços. Sempre responda usando diagramas Mermaid e código Python..."*
  - Dica visual: "Isso define como a IA se comporta neste espaço."

### 3. Workspace do Projeto (`src/app/projects/[id]/page.tsx`)
Crie um layout de 3 colunas (ou Sidebar colapsável à direita):

- **Esquerda (Navegação):** Menu do App.
- **Centro (Chat):**
  - A interface de chat padrão, mas com o contexto do projeto carregado.
  - Header mostrando "Estou usando as instruções de: [Nome do Projeto]".
- **Direita (Knowledge Base & Contexto):**
  - **Aba 1: Instruções:** Mostra (e permite editar) o prompt do sistema atual em *readonly* ou *edit mode*.
  - **Aba 2: Conhecimento (Project Knowledge):**
    - Lista de arquivos ingeridos (PDF, MD, Code).
    - Área de Dropzone para upload de novos arquivos.
    - Ao fazer upload, chamar o endpoint de ingestão passando o `project_id`.

### 4. Estilização
- Use estritamente os tokens de design "Obsidian" (fundo escuro, glows Laranja/Azul).
- Use `framer-motion` para transições suaves entre abas.
- O upload de arquivos deve ter feedback visual de progresso (barra de carregamento neon).
💡 Sugestão de "Prompt Exclusivo" para Testar
Após implementar, crie um projeto chamado "Refatoração Legacy" e use este prompt no campo "Instruções Personalizadas":

"Neste projeto, você atua como um Especialista em Modernização de Legado. Seu tom deve ser crítico mas construtivo. Toda vez que eu lhe mostrar um código, você deve: 1) Identificar Security Smells, 2) Propor refatoração para Clean Code, 3) Não gerar código, apenas explicar a arquitetura. Use a base de conhecimento do projeto (documentação antiga) para validar as regras de negócio."

Isso testará se o sistema está realmente respeitando a "persona" definida para o projeto.
