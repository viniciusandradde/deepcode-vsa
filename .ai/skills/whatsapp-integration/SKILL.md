# Skill: Integração WhatsApp Hospitalar (ZigChat + Evolution API)

## Descrição
Define como implementar integrações WhatsApp para atendimento hospitalar usando ZigChat como sistema principal e Evolution API como fallback.

## Contexto
- **Hospital:** Mackenzie Hospital Evangélico de Dourados
- **Sistema de Chat:** ZigChat (webhook-based)
- **Fallback:** Evolution API v2
- **Orquestração:** n8n (para roteamento) + LangChain (para agentes)
- **Backend:** FastAPI

## Menu do Hospital (ZigChat)
```
1. Atendimento ao Cliente
2. Agendamentos (consultas e exames)
3. Exames (acesso a resultados/laudos)
4. Tesouraria
5. Orçamentos
6. Recrutamento e Seleção
7. Ouvidoria
8. Informações ao Paciente
```

## Regras Obrigatórias

1. **NUNCA** expor dados de paciente sem mascaramento (LGPD)
2. **SEMPRE** logar interações na tabela/registro de `whatsapp_logs`
3. **Timeout** máximo de resposta ao paciente: 5 segundos
4. Se IA não souber responder → **escalar para humano** via ZigChat
5. **NUNCA** enviar dados de prontuário via WhatsApp
6. **SEMPRE** confirmar dados com paciente antes de qualquer ação
7. **SEMPRE** fornecer protocolo de atendimento

## Arquitetura do Fluxo

```
Paciente (WhatsApp)
    │
    ▼
ZigChat (gerencia atendimento)
    │
    ├── Menu selecionado
    │
    ▼
Webhook → POST /webhook/zigchat (nosso servidor)
    │
    ├── n8n (roteamento inicial) OU
    ├── FastAPI direto (rota específica)
    │
    ▼
Router identifica menu → despacha para agente correto
    │
    ▼
Agente LangChain processa
    │
    ├── Consulta Wareline (se necessário)
    ├── Consulta base de conhecimento
    │
    ▼
Resposta via API ZigChat → POST /mensagem/enviar
    │
    ▼
Paciente recebe no WhatsApp
```

## Payload do Webhook (ZigChat → Nosso Servidor)

```json
{
  "nanoid": "{{nanoid}}",
  "mensagem": "{{mensagem}}",
  "conexao": "{{conexao}}",
  "atendimentoId": "{{atendimentoId}}",
  "empresaId": "{{empresaId}}",
  "empresaNome": "{{empresaNome}}",
  "tipo": "{{tipo}}",
  "arquivo": "{{arquivo}}",
  "isGroupMessage": "{{isGroupMessage}}",
  "cliente": {
    "id": "{{cliente.id}}",
    "nome": "{{cliente.nome}}",
    "telefone": "{{cliente.telefone}}",
    "email": "{{cliente.email}}"
  },
  "context": "{{context}}"
}
```

## Roteamento por Menu

```python
# api/webhook_router.py
MENU_MAP = {
    "1": {"agent": "atendimento_cliente", "queue": "high"},
    "2": {"agent": "agendamentos", "queue": "high"},
    "3": {"agent": "exames", "queue": "medium"},
    "4": {"agent": "tesouraria", "queue": "medium"},
    "5": {"agent": "orcamentos", "queue": "medium"},
    "6": {"agent": "rh", "queue": "low"},
    "7": {"agent": "ouvidoria", "queue": "high"},
    "8": {"agent": "informacoes", "queue": "high"},
}

async def route_message(payload: dict):
    """Roteia mensagem para agente correto."""
    menu = detect_menu_selection(payload["mensagem"])
    
    if menu and menu in MENU_MAP:
        config = MENU_MAP[menu]
        return await dispatch_to_agent(
            agent_name=config["agent"],
            payload=payload,
            priority=config["queue"]
        )
    
    # Mensagem livre (sem menu) → classificar intenção
    intent = await classify_intent(payload["mensagem"])
    return await dispatch_to_agent(
        agent_name=intent_to_agent(intent),
        payload=payload
    )
```

## Enviar Resposta via API ZigChat

```python
# services/zigchat_service.py
import httpx

class ZigChatService:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def send_message(self, telefone: str, mensagem: str):
        """Envia mensagem de texto para paciente."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_url}/mensagem/enviar",
                headers=self.headers,
                json={
                    "mensagens": [{"mensagem": mensagem}],
                    "telefone": telefone
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def send_menu(self, telefone: str, titulo: str, opcoes: list):
        """Envia menu interativo."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_url}/mensagem/menuEnviar",
                headers=self.headers,
                json={
                    "telefone": telefone,
                    "titulo": titulo,
                    "opcoes": opcoes
                }
            )
            return response.json()
    
    async def send_file(self, telefone: str, mensagem: str, arquivo_url: str):
        """Envia arquivo (PDF de laudo, etc)."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_url}/mensagem/enviar",
                headers=self.headers,
                json={
                    "mensagens": [{
                        "mensagem": mensagem,
                        "arquivo": arquivo_url
                    }],
                    "telefone": telefone
                }
            )
            return response.json()
    
    async def transfer_to_human(self, atendimento_id: str, setor: str):
        """Transfere atendimento para humano no ZigChat."""
        # Salvar contexto da conversa antes de transferir
        # O atendente humano verá todo o histórico
        pass
```

## Gerenciamento de Sessão/Contexto

```python
# services/session_manager.py
class WhatsAppSessionManager:
    """Gerencia contexto de conversa por paciente."""
    
    def __init__(self, redis):
        self.redis = redis
        self.SESSION_TTL = 3600  # 1 hora
    
    async def get_session(self, telefone: str) -> dict:
        key = f"whatsapp:session:{telefone}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return {
            "telefone": telefone,
            "menu_atual": None,
            "agente_atual": None,
            "historico": [],
            "dados_coletados": {},
            "tentativas_ia": 0
        }
    
    async def update_session(self, telefone: str, session: dict):
        key = f"whatsapp:session:{telefone}"
        await self.redis.set(key, json.dumps(session), ex=self.SESSION_TTL)
    
    async def add_to_history(self, telefone: str, role: str, message: str):
        session = await self.get_session(telefone)
        session["historico"].append({
            "role": role,  # "paciente" ou "agente"
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        # Manter apenas últimas 20 mensagens
        session["historico"] = session["historico"][-20:]
        await self.update_session(telefone, session)
```

## Escalação para Humano

```python
async def should_escalate(session: dict, response: str) -> bool:
    """Decide se deve escalar para atendente humano."""
    # Escalar se:
    return any([
        session["tentativas_ia"] >= 3,          # 3 tentativas sem sucesso
        "urgente" in response.lower(),           # Detecção de urgência
        "emergência" in response.lower(),        # Emergência
        session.get("paciente_insatisfeito"),     # Paciente insatisfeito
        "falar com humano" in response.lower(),  # Pedido explícito
    ])
```

## Anti-Padrões (NÃO FAZER)

- ❌ Polling na API do ZigChat (usar webhooks SEMPRE)
- ❌ Enviar dados de prontuário via WhatsApp
- ❌ Armazenar tokens ZigChat em código (usar .env)
- ❌ Responder sem protocolo de atendimento
- ❌ Ignorar timeout (paciente esperando > 5s)
- ❌ Não logar interações (compliance)
- ❌ Diagnosticar ou prescrever via agente (NUNCA)

## Tipos de Mídia Suportados

| Tipo | Recebe (Webhook) | Envia (API) |
|------|-------------------|-------------|
| Texto | ✅ | ✅ |
| Áudio | ✅ (transcrever com Whisper) | ✅ |
| Imagem | ✅ (analisar com Vision) | ✅ |
| Documento | ✅ (PDF, etc) | ✅ |
| Menu/Botões | - | ✅ |
| Template | - | ✅ |
