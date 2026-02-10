"""Request models for API."""

import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class AttachmentRef(BaseModel):
    file_id: Optional[str] = None
    name: Optional[str] = None
    mime: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., max_length=32000)
    thread_id: Optional[str] = None
    model: Optional[str] = None
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    use_tavily: Optional[bool] = None
    project_id: Optional[str] = None  # DeepCode Projects: RAG scoped to this project
    attachments: Optional[List[AttachmentRef]] = None

    # VSA-specific fields (Task 1.1)
    enable_vsa: bool = False
    enable_glpi: bool = False
    enable_zabbix: bool = False
    enable_linear: bool = False
    enable_planning: bool = False  # Planning/NotebookLM tools
    dry_run: bool = True  # Safe by default


class RAGSearchRequest(BaseModel):
    """RAG search request model."""

    query: str = Field(..., max_length=4000)
    k: int = Field(default=5, ge=1, le=100)
    search_type: str = "hybrid"
    reranker: str = "none"
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    chunking: Optional[str] = None
    use_hyde: bool = False
    match_threshold: Optional[float] = None


_SAFE_DIR_PATTERN = re.compile(r"^[a-zA-Z0-9_\-./]+$")


class RAGIngestRequest(BaseModel):
    """RAG ingestion request model."""

    base_dir: str = Field(default="kb", max_length=200)
    strategy: str = "semantic"
    empresa: Optional[str] = None
    client_id: Optional[str] = None
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)

    @field_validator("base_dir")
    @classmethod
    def validate_base_dir(cls, v: str) -> str:
        """Prevent path traversal attacks."""
        if ".." in v or v.startswith("/") or v.startswith("~"):
            raise ValueError("base_dir must be a relative path without '..' or absolute prefix")
        if not _SAFE_DIR_PATTERN.match(v):
            raise ValueError("base_dir contains invalid characters")
        return v


class AgentInvokeRequest(BaseModel):
    """Agent invocation request model."""

    agent_id: str
    input: dict
    config: Optional[dict] = None
