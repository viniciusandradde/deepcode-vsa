"""Job executors para agendamentos do APScheduler."""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def job_run_agent_prompt_sync(prompt: str, channel_config: Dict[str, Any], job_name: str):
    """
    Job executor para APScheduler.
    
    Em vez de executar diretamente, enfileira no Celery para garantir:
    - Durabilidade (se worker cair, task continua na fila)
    - Retry automático
    - Não bloqueia o scheduler
    
    Args:
        prompt: Prompt para o agente processar
        channel_config: Configuração de notificação
        job_name: Nome do job para logging
    """
    try:
        logger.info(f"[{job_name}] Enfileirando task no Celery...")
        
        # Injetar contexto temporal
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_prompt = f"""Data/Hora Atual: {timestamp}
Tarefa Agendada: {job_name}

Instrução:
{prompt}
"""
        
        # Importar task (lazy import para evitar circular)
        from core.tasks import process_agent_prompt
        
        # Enfileirar no Celery
        task = process_agent_prompt.apply_async(
            args=[final_prompt],
            kwargs={"notification_config": channel_config},
            queue='agent'
        )
        
        logger.info(f"[{job_name}] ✅ Task enfileirada: {task.id}")
        
    except Exception as e:
        logger.error(f"[{job_name}] ❌ Erro ao enfileirar: {e}", exc_info=True)
