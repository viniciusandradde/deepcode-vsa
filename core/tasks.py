"""Celery tasks for async processing."""

import logging
import asyncio
from typing import Dict, Any, Optional
from celery import Task
from core.celery_app import celery_app

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base task que suporta async functions."""
    
    def __call__(self, *args, **kwargs):
        """Wrapper para executar funções async."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run(*args, **kwargs))
        finally:
            loop.close()
    
    async def run(self, *args, **kwargs):
        """Override this method in subclasses."""
        raise NotImplementedError()


@celery_app.task(
    name='core.tasks.process_agent_prompt',
    bind=True,
    base=AsyncTask,
    max_retries=3,
    default_retry_delay=60
)
async def process_agent_prompt(
    self,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    notification_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Processa um prompt usando o UnifiedAgent.
    
    Args:
        prompt: Instrução para o agente
        context: Contexto adicional (opcional)
        notification_config: Config para enviar notificação ao terminar
    
    Returns:
        Dict com resultado e metadata
    """
    try:
        logger.info(f"[Task {self.request.id}] Processando prompt: {prompt[:100]}...")
        
        # Importar aqui para evitar import circular
        from core.agents.unified import UnifiedAgent
        from core.notifications import notification_service
        
        # Criar agente
        agent = UnifiedAgent(
            model_name="openai/gpt-4-turbo",
            tools=[],
            enable_itil=True,
            enable_planning=True,
        )
        
        # Executar
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": prompt}],
            **(context or {})
        })
        
        # Extrair resposta
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            final_message = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        else:
            final_message = "Agente não retornou resposta"
        
        logger.info(f"[Task {self.request.id}] ✅ Processamento concluído")
        
        # Enviar notificação se configurado
        if notification_config:
            await notification_service.send(
                channel=notification_config['channel'],
                config=notification_config,
                message=final_message,
                title=f"Task {self.request.id[:8]}"
            )
        
        return {
            "success": True,
            "response": final_message,
            "task_id": self.request.id,
            "retries": self.request.retries
        }
        
    except Exception as exc:
        logger.error(f"[Task {self.request.id}] ❌ Erro: {exc}", exc_info=True)
        
        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name='core.tasks.generate_linear_report',
    bind=True,
    base=AsyncTask,
    max_retries=2
)
async def generate_linear_report(
    self,
    project_id: str,
    format: str = 'markdown',
    notification_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Gera relatório do Linear.app.
    
    Args:
        project_id: ID do projeto Linear
        format: Formato do relatório ('markdown', 'pdf', etc.)
        notification_config: Config de notificação
    
    Returns:
        Dict com relatório e metadata
    """
    try:
        logger.info(f"[Task {self.request.id}] Gerando relatório Linear: {project_id}")
        
        from core.reports.linear import LinearReportGenerator
        from core.notifications import notification_service
        
        generator = LinearReportGenerator()
        report = await generator.generate_report(project_id, format=format)
        
        logger.info(f"[Task {self.request.id}] ✅ Relatório gerado")
        
        # Notificar
        if notification_config:
            await notification_service.send(
                channel=notification_config['channel'],
                config=notification_config,
                message=f"📊 Relatório do projeto {project_id}\n\n{report[:500]}...",
                title="Relatório Linear"
            )
        
        return {
            "success": True,
            "report": report,
            "project_id": project_id,
            "task_id": self.request.id
        }
        
    except Exception as exc:
        logger.error(f"[Task {self.request.id}] ❌ Erro: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(
    name='core.tasks.send_notification',
    bind=True,
    max_retries=5,
    default_retry_delay=30
)
def send_notification(
    self,
    channel: str,
    config: Dict[str, Any],
    message: str,
    title: str = "DeepCode VSA"
) -> Dict[str, Any]:
    """
    Envia notificação (task síncrona dedicada).
    
    Args:
        channel: Canal de notificação
        config: Configuração do canal
        message: Mensagem a enviar
        title: Título da notificação
    
    Returns:
        Dict com status
    """
    try:
        logger.info(f"[Task {self.request.id}] Enviando notificação via {channel}")
        
        from core.notifications import notification_service
        
        # Executar async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                notification_service.send(channel, config, message, title)
            )
        finally:
            loop.close()
        
        if success:
            logger.info(f"[Task {self.request.id}] ✅ Notificação enviada")
            return {"success": True, "channel": channel, "task_id": self.request.id}
        else:
            raise Exception(f"Falha ao enviar via {channel}")
            
    except Exception as exc:
        logger.error(f"[Task {self.request.id}] ❌ Erro: {exc}")
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
