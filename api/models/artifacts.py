"""Artifact models for report extraction and export."""

from typing import Literal
from pydantic import BaseModel, Field


ArtifactType = Literal[
    "glpi_report",
    "zabbix_report",
    "linear_report",
    "dashboard",
    "itil_classification",
    "rca_analysis",
    "fivew2h_analysis",
    "generic_report",
]


class ArtifactMetadata(BaseModel):
    """Metadata emitted in artifact_start SSE event."""

    artifact_id: str
    title: str
    artifact_type: ArtifactType
    intent: str
    source: Literal["rule-based", "llm"] = "rule-based"


class ExportRequest(BaseModel):
    """Request body for the /api/v1/export endpoint."""

    content: str = Field(..., max_length=500_000)
    title: str = Field(..., max_length=200)
    format: Literal["pdf", "md", "docx"] = "md"
