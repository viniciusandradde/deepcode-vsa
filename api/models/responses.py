"""Response models for API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    thread_id: str
    model: Optional[str] = None


class RAGSearchResponse(BaseModel):
    """RAG search response model."""
    results: List[Dict[str, Any]]
    query: str
    total: int


class RAGIngestResponse(BaseModel):
    """RAG ingestion response model."""
    staged: int
    chunked: int
    message: str


class AgentResponse(BaseModel):
    """Agent response model."""
    output: Dict[str, Any]
    agent_id: str

