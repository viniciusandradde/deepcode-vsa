Proposta Técnica Final: Módulo RAG Avançado (DeepCode Projects)
1. Visão Geral e Objetivo
Transformar o módulo de Planejamento em um assistente de engenharia inteligente ("DeepCode Projects"), similar ao Claude Projects ou NotebookLM. O objetivo é permitir que o usuário faça upload de especificações técnicas (PDF, MD, TXT) e converse com uma IA que possui contexto profundo e exclusivo daquele projeto, utilizando busca híbrida (Keywords + Vetorial) e re-ranking para precisão máxima.

2. Arquitetura da Solução
A solução reaproveita 100% da inteligência já desenvolvida nos arquivos de "Proposta RAG" (loaders.py, tools.py), aplicando-a ao contexto dos projetos.

Ingestão (Escrita): Upload -> Chunking Inteligente (Markdown/Semântico) -> Embedding -> Salvar com project_id.

Recuperação (Leitura): Chat -> Busca Híbrida (Texto + Vetor) -> Filtragem por project_id -> Reranking -> LLM.

3. Implementação Passo a Passo
Passo 1: Atualização do Schema de Banco de Dados
Precisamos garantir que cada "pedaço" de conhecimento (chunk) pertença a um projeto específico para evitar vazamento de contexto entre clientes/projetos.

Arquivo: sql/kb/06_rag_planning.sql

SQL

-- Adicionar coluna project_id na tabela de vetores (kb_chunks)
ALTER TABLE kb_chunks 
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES planning_projects(id) ON DELETE CASCADE;

-- Índice para busca performática dentro de um projeto (Isolamento de Contexto)
CREATE INDEX IF NOT EXISTS idx_kb_chunks_project_id ON kb_chunks(project_id);

-- Opcional: Índice para busca híbrida (Full Text Search) restrita ao projeto
CREATE INDEX IF NOT EXISTS idx_kb_chunks_fts_project 
ON kb_chunks USING gin(to_tsvector('portuguese', content)) 
WHERE project_id IS NOT NULL;
Passo 2: O "Ingestor" Inteligente (Backend)
Vamos adaptar a lógica robusta do seu loaders.py e ingest.py para processar uploads de planejamento em segundo plano.

Arquivo: core/rag/planning_ingestion.py

Python

import logging
from uuid import UUID
from fastapi import UploadFile
from core.database import get_conn
from core.rag.loaders import split_text, load_document_from_bytes # Reusa seu loaders.py
from core.rag.ingestion import embed_texts, vec_to_literal # Reusa seu ingest.py

logger = logging.getLogger(__name__)

def ingest_project_document(project_id: UUID, document_id: UUID, file_content: bytes, filename: str):
    """
    Processa documento de projeto usando estratégia 'markdown' ou 'semantic' do loaders.py.
    """
    try:
        # 1. Estratégia de Chunking baseada na extensão (Melhoria do loaders.py)
        strategy = "markdown" if filename.endswith(".md") else "recursive"
        
        # Extrair texto e quebrar em chunks inteligentes
        text_content = load_document_from_bytes(file_content, filename)
        chunks, _ = split_text(text_content, strategy=strategy, chunk_size=1000, chunk_overlap=200)

        # 2. Gerar Embeddings (Reusa ingest.py)
        vectors = embed_texts(chunks)

        # 3. Salvar no Banco com project_id (Adaptação do upsert_chunks)
        with get_conn() as conn:
            with conn.cursor() as cur:
                from json import dumps
                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    cur.execute(
                        """
                        INSERT INTO kb_chunks 
                        (doc_path, chunk_ix, content, embedding, meta, project_id)
                        VALUES (%s, %s, %s, %s::vector(1536), %s::jsonb, %s)
                        ON CONFLICT (doc_path, chunk_ix) DO NOTHING
                        """,
                        (
                            f"planning/{project_id}/{filename}", # Path virtual único
                            i,
                            chunk,
                            vec_to_literal(vector),
                            dumps({"source": "planning", "doc_id": str(document_id), "file": filename}),
                            str(project_id)
                        )
                    )
        logger.info(f"Documento {filename} ingerido com sucesso no projeto {project_id}")

    except Exception as e:
        logger.error(f"Erro na ingestão RAG do projeto {project_id}: {e}", exc_info=True)
Passo 3: O "Recuperador" Híbrido (Ferramenta do Agente)
Aqui brilha a integração com o tools.py. Vamos criar a ferramenta que o Agente usa para "ler" o projeto.

Arquivo: core/tools/planning_rag.py

Python

from typing import Optional
from langchain_core.tools import tool
from core.rag.tools import kb_search_client # Importa sua ferramenta poderosa do tools.py

@tool
def search_project_knowledge(query: str, project_id: str) -> str:
    """
    PESQUISA AVANÇADA NO PROJETO.
    Use esta ferramenta para responder perguntas sobre requisitos, riscos, arquitetura 
    ou qualquer detalhe técnico contido nos documentos do projeto.
    
    Args:
        query: A pergunta ou termo de busca (ex: "quais os requisitos de auth?", "erro 500").
        project_id: O ID do projeto atual (obrigatório).
    """
    # Reutiliza a lógica Híbrida + Reranking do tools.py
    # Precisamos apenas garantir que tools.py aceite 'project_id' como filtro extra no SQL
    results = kb_search_client(
        query=query,
        project_id=project_id, # Novo parâmetro a ser adicionado no tools.py
        k=7,                   # Traz mais contexto
        search_type="hybrid",  # Garante que ache termos técnicos exatos (ex: "Lib X versão 2")
        reranker="none"        # Pode ativar "cohere" se tiver chave, senão "none"
    )
    
    if not results:
        return "Nenhuma informação relevante encontrada nos documentos deste projeto."

    # Formata para o LLM ler
    context_str = "\n\n".join([
        f"[Doc: {r.get('meta', {}).get('file', 'N/A')}]\n{r['content']}" 
        for r in results
    ])
    return f"Fatos encontrados na documentação do projeto:\n\n{context_str}"
Nota de Adaptação no tools.py: Você precisará adicionar uma pequena cláusula no SQL de query_candidates em tools.py:

Python

# No tools.py
if project_id:
    sql += " AND project_id = %s::uuid"
    params.append(project_id)
Passo 4: Integração na API (User Experience)
1. Rota de Upload (api/routes/planning.py): Modificar para disparar a ingestão em background para não travar o usuário.

Python

@router.post("/projects/{project_id}/documents")
async def upload_doc(..., background_tasks: BackgroundTasks):
    # ... salva o arquivo físico/DB ...
    background_tasks.add_task(
        ingest_project_document, 
        project_id, doc_id, content, filename
    )
    return {"message": "Documento enviado e processando para IA"}
2. Rota de Chat (api/routes/chat.py): Injetar o contexto automaticamente quando o usuário estiver na tela do projeto.

Python

# No chat.py
if request.project_id:
    # Adiciona a ferramenta especializada
    tools.append(search_project_knowledge)
    
    # Instrui o Agente via System Prompt
    system_prompt += f"""
    \n\n--- MODO PROJETO ATIVO ---
    Você está auxiliando no Projeto ID: {request.project_id}.
    Para qualquer dúvida sobre o projeto, OBRIGATORIAMENTE use a ferramenta 
    `search_project_knowledge` passando o project_id='{request.project_id}'.
    """
4. Benefícios Desta Abordagem
Isolamento Total: Dados do Projeto A nunca aparecem nas buscas do Projeto B.

Busca "Google-Quality": Graças à busca híbrida do tools.py, o usuário pode buscar por conceitos ("como é a segurança?") ou termos exatos ("token JWT").

Estrutura de Documentos: O uso de markdown splitter do loaders.py significa que a IA entende que o "Requisito 3" pertence à seção "Módulo Financeiro", mantendo a coerência.

Zero Latência de Upload: O processamento ocorre em background (ingestion.py), mantendo a UI fluida.

Esta é a documentação definitiva para transformar o DeepCode VSA em uma ferramenta de planejamento de engenharia de alto nível.