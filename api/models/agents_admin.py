"""Pydantic models for multi-agent admin CRUD."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Connector ---

class ConnectorOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: str = "integration"
    config_schema: dict = Field(default_factory=dict)
    is_system: bool = True
    is_active: bool = True

    class Config:
        from_attributes = True


# --- Skill ---

class SkillOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: str = "methodology"
    prompt_fragment: Optional[str] = None
    is_system: bool = True
    is_active: bool = True

    class Config:
        from_attributes = True


# --- Knowledge Domain ---

class DomainCreate(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: Optional[str] = None
    color: str = "#6366f1"


class DomainUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeDomainOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    color: str = "#6366f1"
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# --- Agent ---

class AgentCreate(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: Optional[str] = None
    avatar: Optional[str] = None
    system_prompt: Optional[str] = None
    agent_type: str = "simple"
    model_override: Optional[str] = None
    connector_slugs: list[str] = Field(default_factory=list)
    skill_slugs: list[str] = Field(default_factory=list)
    domain_ids: list[UUID] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    avatar: Optional[str] = None
    system_prompt: Optional[str] = None
    agent_type: Optional[str] = None
    model_override: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    connector_slugs: Optional[list[str]] = None
    skill_slugs: Optional[list[str]] = None
    domain_ids: Optional[list[UUID]] = None


class AgentConnectorOut(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = None
    enabled: bool = True
    config: dict = Field(default_factory=dict)


class AgentSkillOut(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = None
    enabled: bool = True


class AgentDomainOut(BaseModel):
    id: UUID
    name: str
    slug: str
    color: str
    access_level: str = "read"


class AgentOut(BaseModel):
    id: UUID
    org_id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    system_prompt: Optional[str] = None
    agent_type: str = "simple"
    model_override: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    connectors: list[AgentConnectorOut] = Field(default_factory=list)
    skills: list[AgentSkillOut] = Field(default_factory=list)
    domains: list[AgentDomainOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AgentListItem(BaseModel):
    """Lightweight agent for list views."""
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    agent_type: str = "simple"
    is_default: bool = False
    is_active: bool = True
    connector_count: int = 0
    skill_count: int = 0
    domain_count: int = 0
