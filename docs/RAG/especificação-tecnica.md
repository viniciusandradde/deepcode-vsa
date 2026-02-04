Especificação Técnica: DeepCode Projects (RAG Module)
1. Visão Executiva
O objetivo é evoluir o módulo de Planejamento para permitir a ingestão de documentos técnicos (PDF, MD, TXT) que se tornam o "cérebro" de um projeto específico. O sistema utilizará Busca Híbrida (Vetorial + Palavra-chave) e Chunking Inteligente para garantir que o Agente de IA responda com precisão técnica sobre requisitos, arquitetura e riscos, sem vazamento de contexto entre projetos.

2. Arquitetura de Dados
Precisamos estender a tabela de vetores existente para suportar multi-tenancy por projeto. Isso permite filtrar buscas estritamente pelo escopo do projeto atual.

Arquivo: sql/kb/06_rag_planning.sql

SQL

-- 1. Adicionar isolamento por projeto na tabela de vetores
ALTER TABLE kb_chunks 
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES planning_projects(id) ON DELETE CASCADE;

-- 2. Índice para performance de busca filtrada (Critical Path)
CREATE INDEX IF NOT EXISTS idx_kb_chunks_project_id ON kb_chunks(project_id);

-- 3. Índice para Busca Híbrida (Full Text Search) dentro do projeto
-- Permite encontrar termos exatos como "Erro 500" ou "API v2"
CREATE INDEX IF NOT EXISTS idx_kb_chunks_fts_project 
ON kb_chunks USING gin(to_tsvector('portuguese', content)) 
WHERE project_id IS NOT NULL;
3. Pipeline de Ingestão (Write Path)
O pipeline reutilizará a lógica avançada de loaders.py e ingest.py. A execução será assíncrona (BackgroundTasks) para não bloquear a interface do usuário.

Arquivo: core/rag/planning_ingestion.py (Novo)

Python

import logging
from uuid import UUID
from fastapi import BackgroundTasks
from core.database import get_conn
from core.rag.loaders import load_document_from_bytes, split_text  #
from core.rag.ingestion import embed_texts, vec_to_literal        #
from json import dumps

logger = logging.getLogger(__name__)

async def ingest_project_document_task(
    project_id: UUID, 
    document_id: UUID, 
    content_bytes: bytes, 
    filename: str
):
    """
    Processa o documento em background:
    1. Detecta estratégia (Markdown para .md, Recursiva para outros)
    2. Gera Chunks + Embeddings
    3. Salva com project_id para isolamento
    """
    try:
        logger.info(f"Iniciando ingestão RAG: {filename} (Proj: {project_id})")
        
        # 1. Carregar Texto
        text = load_document_from_bytes(content_bytes, filename)
        
        # 2. Chunking Inteligente
        # Usa 'markdown' se for .md para preservar hierarquia de seções (# Título)
        strategy = "markdown" if filename.lower().endswith(".md") else "fixed"
        chunks, _ = split_text(text, strategy=strategy, chunk_size=1000, chunk_overlap=200)
        
        if not chunks:
            logger.warning(f"Nenhum chunk gerado para {filename}")
            return

        # 3. Vetorização (Batch)
        vectors = embed_texts(chunks)
        
        # 4. Persistência Isolada
        rows = []
        for i, (chunk_text, vec) in enumerate(zip(chunks, vectors)):
            rows.append({
                "doc_path": f"planning/{project_id}/{filename}",
                "chunk_ix": i,
                "content": chunk_text,
                "embedding": vec,
                "meta": {"source": "planning", "doc_id": str(document_id), "file": filename}
            })
            
        _upsert_planning_chunks(rows, project_id)
        logger.info(f"Sucesso: {len(rows)} chunks indexados para {filename}")

    except Exception as e:
        logger.error(f"Falha na ingestão do documento {document_id}: {e}", exc_info=True)

def _upsert_planning_chunks(rows, project_id):
    """Insere chunks vinculados ao project_id."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO kb_chunks 
                    (doc_path, chunk_ix, content, embedding, meta, project_id)
                    VALUES (%s, %s, %s, %s::vector(1536), %s::jsonb, %s)
                    ON CONFLICT (doc_path, chunk_ix) 
                    DO UPDATE SET content=excluded.content, embedding=excluded.embedding
                    """,
                    (
                        r["doc_path"], r["chunk_ix"], r["content"], 
                        vec_to_literal(r["embedding"]), dumps(r["meta"]), str(project_id)
                    )
                )
4. Motor de Busca Híbrida (Read Path)
O "cérebro" da busca. Adaptamos o kb_search_client do arquivo tools.py para aceitar o filtro de projeto. A busca híbrida é crucial para encontrar termos técnicos específicos que a busca vetorial pura pode perder.

Modificação Necessária: core/rag/tools.py

Python

# Atualizar a assinatura da função query_candidates
def query_candidates(
    query: str,
    k: int,
    search_type: str,
    client_id: Optional[str] = None,
    empresa: Optional[str] = None,
    project_id: Optional[str] = None,  # <--- NOVO PARÂMETRO
    # ... outros params ...
) -> List[Dict[str, Any]]:
    
    # ... (código existente) ...
    
    # Adicionar lógica SQL para filtrar por project_id
    if project_id:
        # Garante isolamento total: busca apenas chunks deste projeto
        sql += " AND project_id = %s::uuid"
        params.append(project_id)
    
    # ... (restante da lógica de Hybrid Search / Reranking existente em tools.py)
5. Ferramenta do Agente (Integration)
Esta é a ponte entre o LLM e o banco de dados. O Agente usará esta ferramenta para "ler" o projeto.

Arquivo: core/tools/planning_rag.py

Python

from langchain_core.tools import tool
from core.rag.tools import kb_search_client  # Ferramenta poderosa do tools.py

@tool
def search_project_knowledge(query: str, project_id: str) -> str:
    """
    Consulta a base de conhecimento do PROJETO ATUAL.
    Use para responder perguntas sobre especificações, riscos, arquitetura 
    ou detalhes técnicos contidos nos arquivos do projeto.
    
    Args:
        query: Pergunta ou termos de busca (ex: "requisitos de autenticação").
        project_id: ID do projeto (UUID).
    """
    try:
        # Aciona o motor de busca híbrida configurado em tools.py
        results = kb_search_client(
            query=query,
            project_id=project_id,  # Passa o contexto isolado
            k=7,                    # Recupera mais contexto para síntese
            search_type="hybrid",   # Combina Keyword + Vector
            reranker="none"         # 'cohere' se disponível, senão 'none'
        )
        
        if not results:
            return "Nenhuma informação encontrada nos documentos do projeto."
            
        # Formata resposta para o LLM
        context = "\n\n".join([
            f"[Fonte: {r['meta'].get('file')}]\n{r['content']}" 
            for r in results
        ])
        return f"Contexto recuperado do projeto:\n{context}"
        
    except Exception as e:
        return f"Erro na busca: {str(e)}"
6. Fluxo de Integração (API & Chat)
6.1 Upload Endpoint (api/routes/planning.py)
Aciona o processamento em background.

Python

@router.post("/projects/{project_id}/documents")
async def upload_document(
    project_id: UUID, 
    file: UploadFile, 
    bg_tasks: BackgroundTasks  # Injeção de dependência FastAPI
):
    content = await file.read()
    # ... (salva metadados no DB planning_documents como hoje) ...
    
    # Dispara ingestão assíncrona
    bg_tasks.add_task(
        ingest_project_document_task,
        project_id=project_id,
        document_id=doc_id,
        content_bytes=content,
        filename=file.filename
    )
    return {"status": "processing", "message": "Documento em análise pela IA"}
6.2 Chat Route (api/routes/chat.py)
Injeta contexto automaticamente quando o usuário está na tela do projeto.

Python

# No endpoint de chat:
if request.project_id:
    # 1. Habilita a ferramenta especializada
    tools.append(search_project_knowledge)
    
    # 2. Instrui o System Prompt (DeepCode VSA)
    agent_prompt += f"""
    \nCONTEXTO ATIVO: Você está no projeto {request.project_id}.
    Para dúvidas sobre este projeto, use EXCLUSIVAMENTE a ferramenta 'search_project_knowledge'.
    """
Conclusão
Esta implementação transforma o DeepCode VSA em um assistente de engenharia context-aware. Ao reutilizar loaders.py (chunking markdown) e tools.py (busca híbrida), garantimos alta precisão na recuperação de dados técnicos complexos, mantendo a arquitetura limpa e performática.