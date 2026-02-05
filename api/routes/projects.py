import logging
from typing import List
import json
from uuid import UUID
import psycopg
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from psycopg.rows import dict_row

from api.models.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectStats
)
from core.database import get_db_url

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_async_conn():
    conn = await psycopg.AsyncConnection.connect(get_db_url(), row_factory=dict_row)
    return conn

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """Cria um novo projeto."""
    try:
        async with await get_async_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO projects (
                        name, description, custom_instructions, settings, metadata
                    ) VALUES (
                        %(name)s, %(description)s, %(custom_instructions)s, %(settings)s::jsonb, %(metadata)s::jsonb
                    ) RETURNING *
                    """,
                    {
                        **project.model_dump(),
                        "settings": json.dumps(project.settings or {}),
                        "metadata": json.dumps(project.metadata or {})
                    }
                )
                new_project = await cur.fetchone()
                
                # Mock stats para retorno imediato
                new_project['created_at'] = new_project['created_at']
                new_project['updated_at'] = new_project['updated_at']
                return ProjectResponse(**new_project)
                
    except Exception as e:
        logger.error(f"Erro ao criar projeto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar projeto: {str(e)}")

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Lista projetos existentes."""
    try:
        async with await get_async_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT * FROM projects 
                    ORDER BY updated_at DESC 
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    {"limit": limit, "offset": offset}
                )
                rows = await cur.fetchall()
                return [ProjectResponse(**row) for row in rows]
                
    except Exception as e:
        logger.error(f"Erro ao listar projetos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar projetos: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    """Obtém detalhes de um projeto."""
    try:
        async with await get_async_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
                project = await cur.fetchone()
                
                if not project:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                return ProjectResponse(**project)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar projeto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar projeto: {str(e)}")

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, update_data: ProjectUpdate):
    """Atualiza um projeto."""
    try:
        # Filtrar campos não nulos
        fields = update_data.model_dump(exclude_unset=True)
        if not fields:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
            
        set_clauses = [f"{k} = %({k})s" for k in fields.keys()]
        set_clauses.append("updated_at = NOW()")
        
        query = f"""
            UPDATE projects 
            SET {', '.join(set_clauses)}
            WHERE id = %(id)s
            RETURNING *
        """
        
        params = fields
        params["id"] = project_id
        
        async with await get_async_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                updated_project = await cur.fetchone()
                
                if not updated_project:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                return ProjectResponse(**updated_project)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar projeto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar projeto: {str(e)}")

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID):
    """Exclui um projeto e todos os seus recursos associados (Cascade)."""
    try:
        async with await get_async_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM projects WHERE id = %s RETURNING id", (project_id,))
                deleted = await cur.fetchone()
                
                if not deleted:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir projeto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir projeto: {str(e)}")


@router.post("/{project_id}/ingest", status_code=200)
async def ingest_project_documents(
    project_id: UUID,
    files: List[UploadFile] = File(...)
):
    """
    Ingere documentos para a base de conhecimento (RAG) do projeto.
    Suporta arquivos de texto e markdown.
    """
    import shutil
    import tempfile
    from pathlib import Path
    
    # Importar lógica de ingestão
    # Nota: Precisamos adaptar stage_docs_from_dir para aceitar um arquivo ou diretório
    # Como o stage_docs_from_dir lê de um diretório, vamos criar um temp dir
    
    # Verificar se projeto existe
    try:
        async with await get_async_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
    except Exception as e:
        logger.error(f"Erro ao verificar projeto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro verificar projeto: {str(e)}")

    try:
        from core.rag.ingestion import stage_docs_from_dir, materialize_chunks_from_staging
        from core.database import get_conn
        
        # Criar diretório temporário para os arquivos
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            processed_files = []
            
            for file in files:
                # Salvar arquivo no diretório temporário
                # Adicionar sufixo .md se for texto plano para ser pego pelo glob
                file_name = file.filename
                if not file_name.endswith(('.md', '.txt')):
                    file_name += ".md"
                    
                file_path = temp_path / file_name
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                processed_files.append(file_name)
                
            # Executar ingestão
            # 1. Staging (apenas para este projeto, usando project_id como um metadado especial?)
            # O sistema atual usa client_id ou empresa. Vamos adaptar ingestion.py ou usar um hack?
            # O melhor é atualizar ingestion.py para suportar project_id no stage_docs_from_dir e nas tabelas
            # Mas como alteramos o schema (kb_docs e kb_chunks tem project_id), podemos atualizar ingestion.py
            # ou fazer a inserção manual aqui se o staging não suportar.
            
            # Vamos fazer a inserção manual na kb_docs e kb_chunks reutilizando funções auxiliares se possível
            # Ou melhor, vamos invocar uma versão modificada do stage_docs_from_dir que suporte project_id.
            # Como não modificamos o ingestion.py ainda para suportar project_id como argumento,
            # vamos fazer a modificação no ingestion.py primeiro.
            
            # PAUSA: Percebi que preciso atualizar core/rag/ingestion.py para aceitar project_id
            # Vou falhar este passo intencionalmente ou fazer um "workaround" chamando SQL direto?
            # Melhor: atualizar ingestion.py. Mas já estou neste tool call.
            # Vou implementar a lógica aqui mesmo usando funções de baixo nível do ingestion ou SQL direto.
            
            # Reutilizando lógica do stage_docs_from_dir mas com project_id
            import hashlib
            import mimetypes
            
            count_staged = 0
            with get_conn() as conn:
                with conn.cursor() as cur:
                    for p in temp_path.rglob("*"):
                        if p.is_file():
                            text = p.read_text(encoding="utf-8", errors="replace")
                            h = hashlib.sha256(text.encode("utf-8")).hexdigest()
                            mime = mimetypes.guess_type(str(p))[0] or "text/plain"
                            
                            # Inserir em kb_docs com project_id
                            cur.execute(
                                """
                                INSERT INTO public.kb_docs (source_path, source_hash, mime_type, content, meta, project_id)
                                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                                ON CONFLICT (source_path, source_hash) DO NOTHING
                                """,
                                (file.filename, h, mime, text, '{}', str(project_id))
                            )
                            count_staged += 1
            
            # 2. Materialize (Chunking + Embedding)
            # Precisamos chamar materialize_chunks_from_staging mas filtrando por project_id
            
            # Vamos reimplementar a lógica de materialização simplificada para projetos aqui
            from core.rag.loaders import split_text
            from core.rag.ingestion import vec_to_literal, embed_texts
            from core.rag.embeddings import EmbeddingFactory
            from json import dumps as json_dumps
            
            # Ler docs do projeto que acabamos de inserir
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, source_path, content FROM public.kb_docs WHERE project_id = %s",
                        (str(project_id),)
                    )
                    docs = cur.fetchall() or []
            
            total_chunks = 0
            rows = []

            # Instanciar embedder se estratégia for semantic
            embedder = EmbeddingFactory.get_model("openai")
            
            # Chunking
            for _id, source_path, content in docs:
                chunks, resolved = split_text(
                    content,
                    strategy="semantic", # Default
                    embedder=embedder,
                    chunk_size=800,
                    chunk_overlap=200
                )
                
                for i, c in enumerate(chunks):
                    rows.append({
                        "doc_path": source_path,
                        "chunk_ix": i,
                        "content": c,
                        "meta": {"chunking": resolved}
                    })
            
            if rows:
                # Embeddings
                vectors = embed_texts([r["content"] for r in rows])
                
                # Upsert chunks
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        for i, r in enumerate(rows):
                            r["embedding"] = vectors[i]
                            vec_lit = vec_to_literal(r["embedding"])
                            
                            cur.execute(
                                """
                                INSERT INTO public.kb_chunks (doc_path, chunk_ix, content, embedding, meta, project_id)
                                VALUES (%s, %s, %s, %s::vector, %s::jsonb, %s)
                                ON CONFLICT (doc_path, chunk_ix)
                                DO UPDATE SET content=excluded.content, embedding=excluded.embedding, meta=excluded.meta,
                                              project_id=excluded.project_id
                                """,
                                (
                                    r["doc_path"],
                                    r["chunk_ix"],
                                    r["content"],
                                    vec_lit,
                                    json_dumps(r.get("meta") or {}),
                                    str(project_id)
                                )
                            )
                            total_chunks += 1
            
            return {
                "message": "Documentos processados com sucesso",
                "files_processed": count_staged,
                "chunks_created": total_chunks,
                "project_id": str(project_id)
            }
            
    except Exception as e:
        logger.error(f"Erro na ingestão RAG: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na processamento: {str(e)}")

