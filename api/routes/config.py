"""Configuration endpoints."""

from fastapi import APIRouter

from core.rag.embeddings import EmbeddingFactory


router = APIRouter()


@router.get("/rag-models")
async def list_rag_models():
    """List available RAG embedding models."""
    return EmbeddingFactory.list_models()
