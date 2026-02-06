# Skill: Workflows n8n para Automação Hospitalar

## Descrição
Define padrões para criar e manter workflows n8n que orquestram processos hospitalares, especialmente roteamento de WhatsApp e automações internas.

## Contexto
- **n8n:** Self-hosted em Proxmox
- **Uso principal:** Roteamento de webhooks ZigChat, automações de relatórios, alertas
- **Integra com:** ZigChat, FastAPI, Redis, PostgreSQL (Wareline)

## Regras Obrigatórias

1. Todo workflow deve ter Error Trigger configurado
2. Nomear workflows com prefixo: `VSA_<modulo>_<acao>`
3. Credenciais NUNCA hardcoded, usar n8n Credentials
4. Timeout de webhook: máximo 10 segundos
5. Sempre ter nó de logging para auditoria

## Workflows Principais

### 1. VSA_WhatsApp_Router
```
Webhook ZigChat
    │
    ├── Switch (por menu selecionado)
    │   ├── 1 → HTTP Request → FastAPI /agents/atendimento
    │   ├── 2 → HTTP Request → FastAPI /agents/agendamentos
    │   ├── 3 → HTTP Request → FastAPI /agents/exames
    │   ├── 4 → HTTP Request → FastAPI /agents/tesouraria
    │   ├── 5 → HTTP Request → FastAPI /agents/orcamentos
    │   ├── 6 → HTTP Request → FastAPI /agents/rh
    │   ├── 7 → HTTP Request → FastAPI /agents/ouvidoria
    │   └── 8 → HTTP Request → FastAPI /agents/informacoes
    │
    └── Resposta → ZigChat API (enviar mensagem)
```

### 2. VSA_Relatorios_Diarios
```
Cron (06:00 diário)
    │
    ├── HTTP Request → FastAPI /reports/ocupacao
    ├── HTTP Request → FastAPI /reports/internacoes
    ├── HTTP Request → FastAPI /reports/agendamentos
    │
    ├── Merge resultados
    │
    └── Enviar → Email/Slack para gestores
```

### 3. VSA_Alertas_Criticos
```
Webhook (trigger interno)
    │
    ├── Switch (tipo de alerta)
    │   ├── leito_critico → Notificar Superintendência
    │   ├── paciente_urgente → Notificar Plantão
    │   └── sistema_down → Notificar TI (Vinícius)
    │
    └── Log → banco de alertas
```

## Padrão de Nomeação

```
VSA_<Modulo>_<Acao>_<Versao>

Exemplos:
VSA_WhatsApp_Router_v1
VSA_Relatorios_Diarios_v2
VSA_Alertas_Criticos_v1
VSA_Backup_Redis_v1
```

## Exportação e Versionamento

- Exportar workflows como JSON em `n8n/` no repositório
- Commitar com prefixo: `[n8n] feat: novo workflow de alertas`
- Documentar variáveis de ambiente necessárias

## Anti-Padrões

- ❌ Lógica de negócio complexa dentro do n8n (usar FastAPI)
- ❌ Credentials hardcoded nos nós
- ❌ Workflow sem Error Trigger
- ❌ Timeout infinito em webhooks
- ❌ Loops sem limite de iterações
