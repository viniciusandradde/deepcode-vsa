"""Automation API routes - Universal Prompt Scheduler."""

import logging
from uuid import uuid4
from typing import List
from fastapi import APIRouter, HTTPException, Query
from api.models.automation import (
    UniversalScheduleRequest,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleConfig
)
from core.scheduler import get_scheduler_service
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


# Get scheduler instance
def get_scheduler():
    """Get scheduler service instance."""
    return get_scheduler_service()


@router.post("/schedule", response_model=ScheduleResponse, status_code=201)
async def create_schedule(request: UniversalScheduleRequest):
    """
    Cria um novo agendamento de prompt.
    
    O prompt será executado pelo UnifiedAgent na frequência especificada
    e o resultado será enviado via canal de notificação configurado.
    """
    try:
        # Gerar ID único
        job_id = f"schedule-{uuid4()}"
        
        # Converter config para dict
        channel_config = {
            "channel": request.config.channel,
            "target_id": request.config.target_id,
            **(request.config.credentials or {})
        }
        
        # Adicionar job ao scheduler
        job_info = get_scheduler().add_prompt_job(
            job_id=job_id,
            name=request.name,
            prompt=request.prompt,
            cron=request.cron,
            channel_config=channel_config
        )
        
        logger.info(f"✅ Agendamento criado: {request.name} ({job_id})")
        
        return ScheduleResponse(
            id=job_info["id"],
            name=request.name,
            prompt=request.prompt,
            cron=request.cron,
            config=request.config,
            enabled=request.enabled,
            next_run=job_info["next_run"],
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao criar agendamento: {str(e)}"
        )


@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules():
    """
    Lista todos os agendamentos ativos.
    
    Retorna informações sobre jobs configurados, incluindo
    próxima data de execução.
    """
    try:
        jobs = get_scheduler().list_jobs()
        
        # Converter para ScheduleResponse
        # Nota: Não temos acesso ao prompt completo aqui (apenas metadata do APScheduler)
        schedules = []
        for job in jobs:
            schedules.append(
                ScheduleResponse(
                    id=job["id"],
                    name=job["name"],
                    prompt="[Ver detalhes no job]",  # Prompt não fica em memória
                    cron=job["trigger"],
                    config=ScheduleConfig(
                        channel="telegram",  # Placeholder
                        target_id=""
                    ),
                    enabled=True,
                    next_run=job["next_run"],
                    created_at=datetime.now()
                )
            )
        
        logger.info(f"📋 Listados {len(schedules)} agendamentos")
        
        return ScheduleListResponse(
            schedules=schedules,
            total=len(schedules)
        )
        
    except Exception as e:
        logger.error(f"❌ Error listing schedules: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar agendamentos: {str(e)}"
        )


@router.get("/schedule/{job_id}", response_model=ScheduleResponse)
async def get_schedule(job_id: str):
    """
    Obtém detalhes de um agendamento específico.
    """
    try:
        job = get_scheduler().get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Agendamento não encontrado"
            )
        
        return ScheduleResponse(
            id=job["id"],
            name=job["name"],
            prompt="[Ver detalhes no job]",
            cron=job["trigger"],
            config=ScheduleConfig(channel="telegram", target_id=""),
            enabled=True,
            next_run=job["next_run"],
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar agendamento: {str(e)}"
        )


@router.delete("/schedule/{job_id}")
async def delete_schedule(job_id: str):
    """
    Remove um agendamento.
    
    O job será permanentemente removido do scheduler.
    """
    success = get_scheduler().remove_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )
    
    logger.info(f"🗑️ Agendamento removido: {job_id}")
    
    return {
        "message": "Agendamento removido com sucesso",
        "job_id": job_id
    }


@router.post("/schedule/{job_id}/pause")
async def pause_schedule(job_id: str):
    """
    Pausa um agendamento.
    
    O job não será executado até ser resumido.
    """
    success = get_scheduler().pause_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )
    
    logger.info(f"⏸️ Agendamento pausado: {job_id}")
    
    return {
        "message": "Agendamento pausado",
        "job_id": job_id
    }


@router.post("/schedule/{job_id}/resume")
async def resume_schedule(job_id: str):
    """
    Resume um agendamento pausado.
    
    O job voltará a ser executado conforme o CRON configurado.
    """
    success = get_scheduler().resume_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )
    
    logger.info(f"▶️ Agendamento resumido: {job_id}")
    
    return {
        "message": "Agendamento resumido",
        "job_id": job_id
    }
