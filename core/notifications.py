"""Serviço unificado de notificações multi-canal."""

import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class NotificationService:
    """Serviço unificado para envio de notificações via múltiplos canais."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_telegram(self, token: str, chat_id: str, message: str) -> bool:
        """
        Envia mensagem via Telegram Bot API.
        
        Args:
            token: Bot token do Telegram
            chat_id: ID do chat
            message: Mensagem a enviar (suporta Markdown)
        
        Returns:
            True se enviado com sucesso
        """
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            logger.info(f"✅ Telegram message sent to chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
            return False
    
    async def send_teams(self, webhook_url: str, title: str, message: str) -> bool:
        """
        Envia mensagem via Microsoft Teams Webhook.
        
        Args:
            webhook_url: URL do webhook do Teams
            title: Título da mensagem
            message: Corpo da mensagem
        
        Returns:
            True se enviado com sucesso
        """
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "F97316",  # Brand Orange
                "title": title,
                "text": message
            }
            response = await self.client.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Teams message sent")
            return True
        except Exception as e:
            logger.error(f"❌ Teams send error: {e}")
            return False
    
    async def send_whatsapp(
        self, 
        api_url: str, 
        token: str, 
        to_number: str, 
        message: str
    ) -> bool:
        """
        Envia mensagem via WhatsApp Business API.
        
        Args:
            api_url: URL da API do WhatsApp Business
            token: Access token
            to_number: Número de telefone (formato internacional)
            message: Mensagem a enviar
        
        Returns:
            True se enviado com sucesso
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message}
            }
            response = await self.client.post(api_url, json=data, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ WhatsApp message sent to {to_number}")
            return True
        except Exception as e:
            logger.error(f"❌ WhatsApp send error: {e}")
            return False
    
    async def send(
        self, 
        channel: str, 
        config: Dict[str, Any], 
        message: str, 
        title: str = "DeepCode VSA"
    ) -> bool:
        """
        Roteador unificado de canais.
        
        Args:
            channel: Canal de notificação ('telegram', 'teams', 'whatsapp')
            config: Configuração do canal (target_id, credentials)
            message: Mensagem a enviar
            title: Título da mensagem (usado apenas em alguns canais)
        
        Returns:
            True se enviado com sucesso
        """
        try:
            if channel == "telegram":
                return await self.send_telegram(
                    token=config.get("token", ""),
                    chat_id=config["target_id"],
                    message=message
                )
            elif channel == "teams":
                return await self.send_teams(
                    webhook_url=config["target_id"],
                    title=title,
                    message=message
                )
            elif channel == "whatsapp":
                return await self.send_whatsapp(
                    api_url=config.get("api_url", ""),
                    token=config.get("token", ""),
                    to_number=config["target_id"],
                    message=message
                )
            else:
                logger.error(f"❌ Unknown channel: {channel}")
                return False
        except Exception as e:
            logger.error(f"❌ Send error for channel '{channel}': {e}")
            return False
    
    async def close(self):
        """Fecha conexões HTTP."""
        await self.client.aclose()


# Instância global
notification_service = NotificationService()
