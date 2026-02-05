"""Automation API models."""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, List
from datetime import datetime
from croniter import croniter


class ScheduleConfig(BaseModel):
    """Configuração do canal de notificação."""
    
    channel: str = Field(..., description="Canal: 'telegram', 'teams', 'whatsapp'")
    target_id: str = Field(..., description="Chat ID ou Webhook URL")
    credentials: Optional[Dict[str, str]] = None
    
    @field_validator('channel')
    @classmethod
    def validate_channel(cls, v: str) -> str:
        """Valida canal suportado."""
        allowed = {'telegram', 'teams', 'whatsapp'}
        if v.lower() not in allowed:
            raise ValueError(f"Canal deve ser um de: {', '.join(allowed)}")
        return v.lower()


class UniversalScheduleRequest(BaseModel):
    """Requisição para criar agendamento universal."""
    
    name: str = Field(..., description="Nome do agendamento", min_length=1, max_length=200)
    prompt: str = Field(..., description="Instrução completa para o agente", min_length=10)
    cron: str = Field(..., description="Expressão CRON (ex: '0 8 * * 1')")
    config: ScheduleConfig
    enabled: bool = Field(default=True)
    
    @field_validator('cron')
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Valida sintaxe CRON."""
        try:
            croniter(v)
        except Exception as e:
            raise ValueError(f"Expressão CRON inválida: {e}")
        return v


class ScheduleResponse(BaseModel):
    """Resposta com dados do agendamento."""
    
    id: str
    name: str
    prompt: str
    cron: str
    config: ScheduleConfig
    enabled: bool
    next_run: Optional[datetime] = None
    created_at: datetime


class ScheduleListResponse(BaseModel):
    """Lista de agendamentos."""
    
    schedules: List[ScheduleResponse]
    total: int
