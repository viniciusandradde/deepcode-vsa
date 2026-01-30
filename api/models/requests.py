"""Request models for API."""

from typing import Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = None
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    use_tavily: Optional[bool] = None
    
    # VSA-specific fields (Task 1.1)
    enable_vsa: bool = False
    enable_glpi: bool = False
    enable_zabbix: bool = False
    enable_linear: bool = False
    enable_planning: bool = False  # Planning/NotebookLM tools
    dry_run: bool = True  # Safe by default


class RAGSearchRequest(BaseModel):
    """RAG search request model."""
    query: str
    k: int = 5
    search_type: str = "hybrid"
    reranker: str = "none"
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    chunking: Optional[str] = None
    use_hyde: bool = False
    match_threshold: Optional[float] = None


class RAGIngestRequest(BaseModel):
    """RAG ingestion request model."""
    base_dir: str = "kb"
    strategy: str = "semantic"
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    chunk_size: int = 800
    chunk_overlap: int = 200


class AgentInvokeRequest(BaseModel):
    """Agent invocation request model."""
    agent_id: str
    input: dict
    config: Optional[dict] = None

