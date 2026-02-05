"""Queue management routes."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentPromptRequest(BaseModel):
    """Request para enfileirar processamento de prompt."""
    prompt: str = Field(..., min_length=10)
    context: Optional[dict] = None
    notification: Optional[dict] = None
    priority: int = Field(default=5, ge=0, le=10)


class LinearReportRequest(BaseModel):
    """Request para enfileirar geração de relatório."""
    project_id: str
    format: str = Field(default="markdown")
    notification: Optional[dict] = None


@router.post("/agent/enqueue")
async def enqueue_agent_prompt(request: AgentPromptRequest):
    """
    Enfileira processamento de prompt pelo UnifiedAgent.
    
    Retorna task_id para acompanhamento.
    """
    try:
        from core.tasks import process_agent_prompt
        
        task = process_agent_prompt.apply_async(
            args=[request.prompt],
            kwargs={
                "context": request.context,
                "notification_config": request.notification
            },
            priority=request.priority,
            queue='agent'
        )
        
        logger.info(f"✅ Task enfileirada: {task.id}")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Prompt enfileirado com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao enfileirar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/linear/enqueue")
async def enqueue_linear_report(request: LinearReportRequest):
    """
    Enfileira geração de relatório do Linear.
    
    Retorna task_id para acompanhamento.
    """
    try:
        from core.tasks import generate_linear_report
        
        task = generate_linear_report.apply_async(
            args=[request.project_id],
            kwargs={
                "format": request.format,
                "notification_config": request.notification
            },
            queue='reports'
        )
        
        logger.info(f"✅ Relatório enfileirado: {task.id}")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "project_id": request.project_id
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao enfileirar relatório: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Obtém status de uma task.
    
    Estados possíveis:
    - PENDING: Na fila
    - STARTED: Em execução
    - SUCCESS: Concluída
    - FAILURE: Falhou
    - RETRY: Tentando novamente
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.state,
            "info": result.info
        }
        
        if result.ready():
            if result.successful():
                response["result"] = result.result
            elif result.failed():
                response["error"] = str(result.info)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancela uma task pendente ou em execução.
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"🗑️ Task cancelada: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelada com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao cancelar task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_queue_stats():
    """
    Retorna estatísticas das filas.
    """
    try:
        inspector = celery_app.control.inspect()
        
        stats = {
            "active": inspector.active() or {},
            "scheduled": inspector.scheduled() or {},
            "reserved": inspector.reserved() or {},
            "stats": inspector.stats() or {}
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
