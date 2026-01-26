"""RAG API routes."""

from fastapi import APIRouter, HTTPException

from api.models.requests import RAGSearchRequest, RAGIngestRequest
from api.models.responses import RAGSearchResponse, RAGIngestResponse
from core.rag.tools import kb_search_client
from core.rag.ingestion import (
    stage_docs_from_dir,
    materialize_chunks_from_staging,
    truncate_kb_tables,
)


router = APIRouter()


@router.post("/search", response_model=RAGSearchResponse)
async def search_kb(request: RAGSearchRequest):
    """Search knowledge base."""
    try:
        results = kb_search_client.invoke({
            "query": request.query,
            "k": request.k,
            "search_type": request.search_type,
            "reranker": request.reranker,
            "empresa": request.empresa,
            "client_id": request.client_id,
            "chunking": request.chunking,
            "use_hyde": request.use_hyde,
            "match_threshold": request.match_threshold,
        })
        
        return RAGSearchResponse(
            results=results,
            query=request.query,
            total=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/ingest", response_model=RAGIngestResponse)
async def ingest_documents(request: RAGIngestRequest):
    """Ingest documents into knowledge base."""
    try:
        # Stage documents
        staged = stage_docs_from_dir(
            request.base_dir,
            empresa=request.empresa,
            client_id=request.client_id
        )
        
        # Materialize chunks
        chunked = materialize_chunks_from_staging(
            strategy=request.strategy,
            empresa=request.empresa,
            client_id=request.client_id,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
        
        return RAGIngestResponse(
            staged=staged,
            chunked=chunked,
            message=f"Staged {staged} documents, created {chunked} chunks"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


@router.get("/stats/{empresa}")
async def get_kb_stats(empresa: str, client_id: str = None):
    """Get knowledge base statistics."""
    try:
        from core.database import get_conn
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Count documents
                cur.execute(
                    "select count(*) from public.kb_docs where lower(empresa) = lower(%s)",
                    (empresa,)
                )
                doc_count = cur.fetchone()[0]
                
                # Count chunks
                cur.execute(
                    "select count(*) from public.kb_chunks where lower(empresa) = lower(%s)",
                    (empresa,)
                )
                chunk_count = cur.fetchone()[0]
                
                return {
                    "empresa": empresa,
                    "documents": doc_count,
                    "chunks": chunk_count,
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

