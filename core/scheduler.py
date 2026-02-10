"""Scheduler service usando APScheduler com persistência PostgreSQL."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from datetime import datetime
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerService:
    """Serviço de agendamento com persistência PostgreSQL usando AsyncIO."""

    def __init__(self):
        # JobStore no PostgreSQL
        jobstores = {"default": SQLAlchemyJobStore(url=settings.database.connection_string)}

        # Executors
        executors = {
            "default": ThreadPoolExecutor(10),
        }

        # Job defaults
        job_defaults = {
            "coalesce": True,  # Combinar execuções perdidas
            "max_instances": 1,  # Apenas 1 instância por job
            "misfire_grace_time": 60,  # Tolerar 60s de atraso
        }

        # AsyncIOScheduler para melhor integração com FastAPI
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="America/Campo_Grande",  # Timezone de Campo Grande/MS
        )

    def start(self):
        """Inicia o scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler iniciado")
            self._ensure_file_cleanup_job()
        else:
            logger.warning("⚠️ Scheduler já está rodando")

    def _ensure_file_cleanup_job(self) -> None:
        """Registra job diário de limpeza de arquivos expirados."""
        job_id = "cleanup_expired_files"
        if self.scheduler.get_job(job_id):
            return
        from core.jobs import job_cleanup_expired_files

        trigger = CronTrigger.from_crontab("0 2 * * *", timezone="America/Campo_Grande")
        self.scheduler.add_job(
            job_cleanup_expired_files,
            trigger=trigger,
            id=job_id,
            name="Limpeza de arquivos expirados",
            replace_existing=True,
        )
        logger.info("📦 Job de limpeza de arquivos agendado (02:00)")

    def shutdown(self, wait: bool = True):
        """
        Desliga o scheduler.

        Args:
            wait: Se True, aguarda jobs em execução finalizarem
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("🛑 Scheduler desligado")

    def add_prompt_job(
        self, job_id: str, name: str, prompt: str, cron: str, channel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adiciona job de execução de prompt.

        Args:
            job_id: ID único do job
            name: Nome do agendamento
            prompt: Prompt para o agente
            cron: Expressão CRON
            channel_config: Configuração de notificação

        Returns:
            Dict com id, name e next_run
        """
        from core.jobs import job_run_agent_prompt_sync

        # Criar trigger CRON
        trigger = CronTrigger.from_crontab(cron, timezone="America/Campo_Grande")

        # Adicionar job
        job = self.scheduler.add_job(
            job_run_agent_prompt_sync,
            trigger=trigger,
            args=[prompt, channel_config, name],
            id=job_id,
            name=name,
            replace_existing=True,
        )

        next_run = None
        try:
            next_run = (
                job.next_run_time
                if hasattr(job, "next_run_time")
                else job.trigger.get_next_fire_time(None, datetime.now())
            )
        except Exception:
            pass

        logger.info(f"✅ Job '{name}' agendado: {cron} (próxima execução: {next_run})")

        return {"id": job.id, "name": job.name, "next_run": next_run}

    def remove_job(self, job_id: str) -> bool:
        """
        Remove um job.

        Args:
            job_id: ID do job

        Returns:
            True se removido com sucesso
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"🗑️ Job '{job_id}' removido")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao remover job '{job_id}': {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """
        Pausa um job.

        Args:
            job_id: ID do job

        Returns:
            True se pausado com sucesso
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"⏸️ Job '{job_id}' pausado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao pausar job '{job_id}': {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume um job pausado.

        Args:
            job_id: ID do job

        Returns:
            True se resumido com sucesso
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"▶️ Job '{job_id}' resumido")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao resumir job '{job_id}': {e}")
            return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        Lista todos os jobs.

        Returns:
            Lista de dicts com informações dos jobs
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = None
            try:
                next_run = job.next_run_time if hasattr(job, "next_run_time") else None
            except Exception:
                pass

            jobs.append(
                {"id": job.id, "name": job.name, "next_run": next_run, "trigger": str(job.trigger)}
            )
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um job.

        Args:
            job_id: ID do job

        Returns:
            Dict com informações do job ou None se não existir
        """
        job = self.scheduler.get_job(job_id)
        if not job:
            return None

        next_run = None
        try:
            next_run = job.next_run_time if hasattr(job, "next_run_time") else None
        except Exception:
            pass

        return {"id": job.id, "name": job.name, "next_run": next_run, "trigger": str(job.trigger)}


# Inst Global singleton
_scheduler_instance: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """
    Get or create the global scheduler service instance (singleton).

    Returns:
        SchedulerService: The global scheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        logger.info("Creating new SchedulerService instance...")
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
