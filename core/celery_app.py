"""Celery application configuration."""

import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# Redis URL do .env
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Criar instância Celery
celery_app = Celery(
    'deepcode_vsa',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['core.tasks']  # Importar tarefas automaticamente
)

# Configurações
celery_app.conf.update(
    # Serialização
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='America/Campo_Grande',
    enable_utc=False,
    
    # Retry e durabilidade
    task_acks_late=True,  # Só marca como "done" após completar
    task_reject_on_worker_lost=True,  # Re-enfileira se worker cair
    task_track_started=True,  # Rastrear quando task inicia
    
    # TTL
    result_expires=3600,  # Resultados expiram em 1h
    
    # Retry defaults
    task_default_retry_delay=60,  # 1min entre retries
    task_max_retries=3,
    
    # Limites
    task_time_limit=600,  # 10min hard limit
    task_soft_time_limit=540,  # 9min soft limit
    
    # Concurrency
    worker_prefetch_multiplier=1,  # Pega 1 task por vez (evita sobrecarga)
    worker_max_tasks_per_child=50,  # Reinicia worker após 50 tasks (memory leak prevention)
    
    # Logs
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Rotas de tasks (opcional, para organização)
celery_app.conf.task_routes = {
    'core.tasks.process_agent_prompt': {'queue': 'agent'},
    'core.tasks.generate_linear_report': {'queue': 'reports'},
    'core.tasks.send_notification': {'queue': 'notifications'},
}

logger.info(f"✅ Celery app configured with broker: {REDIS_URL}")
