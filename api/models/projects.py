from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nome do projeto")
    description: Optional[str] = Field(None, description="Descrição do projeto")
    custom_instructions: Optional[str] = Field(None, description="Prompt do sistema específico para este projeto")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Configurações extras (model, temperature, etc)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados arbitrários")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    custom_instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectStats(BaseModel):
    threads_count: int
    documents_count: int
    last_activity: Optional[datetime]
