import logging
import asyncio
from asgiref.sync import async_to_sync
from celery import Task
from core.celery_app import celery_app
from core.agents.unified import UnifiedAgent
from core.reports.linear import LinearReportGenerator
from core.integrations.linear_client import LinearClient
from core.notifications import notification_service

logger = logging.getLogger(__name__)

class BaseTask(Task):
    """Classe base para capturar exceções e logs."""
    abstract = True
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"❌ Tarefa {task_id} falhou: {exc}")
        # Opcional: Enviar alerta para o canal de Ops no Teams/Slack

@celery_app.task(bind=True, base=BaseTask, max_retries=3, default_retry_delay=10)
def task_process_agent_prompt(self, prompt: str, context: dict):
    """
    Processa um prompt complexo via Agente.
    Usa 'async_to_sync' para rodar o código assíncrono do LangChain.
    """
    logger.info(f"🔄 Processando prompt: {prompt[:30]}...")

    async def _run_agent():
        # Instancia o agente (assumindo que ele pega configs do env)
        agent = UnifiedAgent(model="gemini-2.5-flash-preview-09-2025")
        result = await agent.run(input_text=prompt)
        return result.output if hasattr(result, 'output') else str(result)

    try:
        result = async_to_sync(_run_agent)()
        
        # Se tiver configuração de notificação no contexto, envia
        if context.get('notify_channel'):
            async_to_sync(notification_service.send_telegram)(
                bot_token=context['credentials']['telegram_token'],
                chat_id=context['target_id'],
                message=f"🤖 **Resultado do Processamento:**\n\n{result}"
            )
        return result

    except Exception as e:
        logger.warning(f"Erro na tentativa {self.request.retries}: {e}")
        # Tenta novamente em caso de erro (ex: API da OpenAI caiu)
        raise self.retry(exc=e)

@celery_app.task(bind=True, base=BaseTask)
def task_generate_linear_report(self, team_id: str, credentials: dict):
    """
    Gera relatório pesado do Linear em Background.
    """
    logger.info(f"📊 Gerando relatório Linear para time {team_id}")

    async def _run_report():
        client = LinearClient(api_key=credentials['linear_api_key'])
        issues = await client.get_team_issues(team_id)
        generator = LinearReportGenerator(client)
        return generator.generate_status_matrix(issues)

    result = async_to_sync(_run_report)()
    return result
