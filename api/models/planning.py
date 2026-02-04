"""Pydantic models for Planning API (NotebookLM-like functionality)."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Budget Items
# =============================================================================


class BudgetItemBase(BaseModel):
    """Base budget item fields."""

    category: str = Field(
        ..., description="Category: infra, pessoal, licencas, hardware, software, servicos"
    )
    description: Optional[str] = None
    estimated_cost: float = Field(default=0, ge=0)
    actual_cost: float = Field(default=0, ge=0)
    currency: str = "BRL"


class BudgetItemCreate(BudgetItemBase):
    """Create budget item request."""

    stage_id: Optional[UUID] = None


class BudgetItemUpdate(BaseModel):
    """Update budget item request."""

    category: Optional[str] = None
    description: Optional[str] = None
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    actual_cost: Optional[float] = Field(default=None, ge=0)
    stage_id: Optional[UUID] = None


class BudgetItemResponse(BudgetItemBase):
    """Budget item response."""

    id: UUID
    project_id: UUID
    stage_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Stages (Milestones/Phases)
# =============================================================================


class StageBase(BaseModel):
    """Base stage fields."""

    title: str
    description: Optional[str] = None
    order_index: int = 0
    estimated_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class StageCreate(StageBase):
    """Create stage request."""

    pass


class StageUpdate(BaseModel):
    """Update stage request."""

    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    status: Optional[str] = None  # pending, in_progress, completed
    estimated_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class StageResponse(StageBase):
    """Stage response."""

    id: UUID
    project_id: UUID
    status: str = "pending"
    linear_milestone_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Documents
# =============================================================================


class DocumentResponse(BaseModel):
    """Document response."""

    id: UUID
    project_id: UUID
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    content_preview: Optional[str] = Field(None, description="First 500 chars of content")
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    """List of documents response."""

    documents: List[DocumentResponse]
    total: int


# =============================================================================
# Projects
# =============================================================================


class ProjectBase(BaseModel):
    """Base project fields."""

    title: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Create project request."""

    empresa: Optional[str] = None
    client_id: Optional[UUID] = None
    embedding_model: Optional[str] = Field(default="openai", description="Embedding model ID")


class ProjectUpdate(BaseModel):
    """Update project request."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # draft, active, completed, archived
    embedding_model: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Project response."""

    id: UUID
    status: str = "draft"
    empresa: Optional[str] = None
    client_id: Optional[UUID] = None
    embedding_model: str = "openai"
    linear_project_id: Optional[str] = None
    linear_project_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Project detail with stages, documents, and budget."""

    stages: List[StageResponse] = []
    documents: List[DocumentResponse] = []
    budget_items: List[BudgetItemResponse] = []
    total_budget_estimated: float = 0
    total_budget_actual: float = 0


class ProjectListResponse(BaseModel):
    """List of projects response."""

    projects: List[ProjectResponse]
    total: int


# =============================================================================
# Analysis (NotebookLM-like)
# =============================================================================


class AnalyzeDocsRequest(BaseModel):
    """Request to analyze project documents."""

    focus_area: str = Field(
        default="Geral",
        description="Focus area: Geral, Riscos, Cronograma, Custos, Requisitos, Arquitetura",
    )


class SuggestedStage(BaseModel):
    """Suggested stage from analysis."""

    title: str
    description: Optional[str] = None
    estimated_days: Optional[int] = None


class SuggestedBudgetItem(BaseModel):
    """Suggested budget item from analysis."""

    category: str
    description: str
    estimated_cost: float


class AnalyzeDocsResponse(BaseModel):
    """Response from document analysis."""

    executive_summary: str
    critical_points: List[str] = []
    suggested_stages: List[SuggestedStage] = []
    suggested_budget: List[SuggestedBudgetItem] = []
    risks: List[str] = []
    recommendations: List[str] = []
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None


# =============================================================================
# Linear Sync
# =============================================================================


class SyncLinearRequest(BaseModel):
    """Request to sync project with Linear."""

    team_id: str = Field(..., description="Linear team ID")
    create_issues: bool = Field(default=False, description="Also create issues for each stage")


class SyncLinearResponse(BaseModel):
    """Response from Linear sync."""

    success: bool
    project_id: Optional[str] = None
    project_url: Optional[str] = None
    milestones_created: int = 0
    issues_created: int = 0
    message: str
