# Como Testar as Integrações - Hospital Evangélico

**Status:** ✅ Credenciais configuradas
**Ambiente:** Produção - Hospital Evangélico
**Data:** Janeiro 2026

---

## 🚀 Início Rápido (5 minutos)

### 1. Verificar Credenciais

As seguintes credenciais já estão configuradas no `.env`:

```bash
✅ GLPI - https://glpi.hospitalevangelico.com.br
✅ Zabbix - https://zabbix.hospitalevangelico.com.br
✅ Linear.app - Organização conectada
```

### 2. Testar Todas as Integrações

```bash
# Instalar dependências (se ainda não instalou)
pip install -r requirements.txt

# Testar todas as integrações
python scripts/test_integrations.py --all

# Ou testar individualmente
python scripts/test_integrations.py --glpi
python scripts/test_integrations.py --zabbix
python scripts/test_integrations.py --linear
```

### 3. Output Esperado

```
==============================================================
🚀 DeepCode VSA - Integration Tests
Hospital Evangélico - Ambiente de Produção
==============================================================

============================================================
🔍 Testando GLPI Integration
============================================================
📡 Base URL: https://glpi.hospitalevangelico.com.br/glpi/apirest.php
🔑 App Token: hmj96ml658...

1️⃣ Inicializando sessão...
✅ Sessão iniciada: 1234567890abcdef...

2️⃣ Buscando últimos 5 tickets...
✅ Encontrados 5 tickets

📋 Exemplos de tickets:
   • #1240: Impressora não funciona (Status: 2)
   • #1239: VPN não conecta (Status: 1)
   • #1238: Lentidão no sistema (Status: 2)

✅ GLPI Integration: OK

============================================================
🔍 Testando Zabbix Integration
============================================================
📡 Base URL: https://zabbix.hospitalevangelico.com.br
🔑 API Token: a4419b657411...

1️⃣ Buscando problemas ativos...
✅ Encontrados 3 problemas

⚠️ Exemplos de problemas:
   • Event #12345: web-01: CPU usage > 90% (Severity: 4)
   • Event #12346: db-01: Disk space low (Severity: 3)
   • Event #12347: mail-01: SMTP service down (Severity: 5)

✅ Zabbix Integration: OK

============================================================
🔍 Testando Linear Integration
============================================================
🔑 API Key: lin_api_VZJYnVszyf...

1️⃣ Buscando teams...
✅ Encontrados 2 teams

👥 Teams disponíveis:
   • INFRA: Infrastructure (ID: abc12345...)
   • DEV: Development (ID: def67890...)

2️⃣ Buscando últimas 5 issues...
✅ Encontradas 5 issues

📋 Exemplos de issues:
   • INFRA-220: Investigate web-01 performance (State: In Progress)
   • DEV-105: Optimize dashboard queries (State: Backlog)
   • INFRA-215: Renew SSL certificates (State: Todo)

✅ Linear Integration: OK

============================================================
📊 Resumo dos Testes
============================================================
GLPI............................................ ✅ OK
Zabbix.......................................... ✅ OK
Linear.......................................... ✅ OK
============================================================

🎉 Todas as integrações funcionando corretamente!
```

---

## ⚠️ Possíveis Problemas

### GLPI: User Token Missing

**Sintoma:**
```
❌ Falha na autenticação: ERROR_GLPI_LOGIN
```

**Solução:**
1. Acesse: https://glpi.hospitalevangelico.com.br
2. Login com seu usuário
3. Vá em: Meu Perfil → Configurações Remotas → Tokens de API
4. Gere um novo token
5. Adicione ao `.env`:
   ```bash
   GLPI_USER_TOKEN=seu_token_aqui
   ```

### Zabbix: IP Bloqueado

**Sintoma:**
```
❌ HTTP Error: 403
```

**Solução:**
Verifique se o IP do servidor está na whitelist do Zabbix.

### Linear: API Key Inválida

**Sintoma:**
```
❌ GraphQL Error: Invalid API key
```

**Solução:**
1. Verifique se copiou a key completa
2. Gere nova key em: https://linear.app/settings/api

---

## 📊 Testar no Chat (Próximo Passo)

Depois que as integrações estiverem funcionando, teste no chat:

### 1. Iniciar Backend

```bash
# Terminal 1: Backend API
uvicorn api.main:app --reload --port 8000
```

### 2. Iniciar Frontend

```bash
# Terminal 2: Frontend Next.js
cd frontend
npm run dev
```

### 3. Testar no Chat

Acesse: http://localhost:3000

```
👤 "Liste os últimos 5 tickets do GLPI"
👤 "Quais alertas críticos no Zabbix?"
👤 "Mostre os teams do Linear"
👤 "Liste issues do time de infraestrutura"
```

### 4. Testar Criação (Dry-Run)

```
👤 "Crie um ticket de teste no GLPI sobre servidor web01"

🤖 VSA Agent:
📋 PREVIEW - Ticket GLPI (DRY-RUN)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: Teste - Servidor web01
Tipo: Incident
Prioridade: 3 (Normal)

Descrição: Ticket de teste criado pelo VSA Agent

⚠️ MODO DRY-RUN ATIVO
Este ticket NÃO será criado automaticamente.

Para confirmar criação, responda: "criar" ou "confirmar"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔐 Segurança

**⚠️ IMPORTANTE:** Você está usando credenciais de **PRODUÇÃO**!

### Regras de Ouro

1. ✅ **Dry-run está ATIVO por padrão** - operações WRITE são simuladas
2. ✅ **Arquivo .env está no .gitignore** - não será commitado
3. ⚠️ **Nunca compartilhe credenciais** em chat ou email
4. ⚠️ **Revise todas as operações** antes de confirmar

### Modo Seguro

O sistema está configurado para máxima segurança:

```python
# core/config.py
dry_run: bool = True  # Sempre True por padrão
```

Todas as operações WRITE exigem:
1. Preview da operação
2. Confirmação explícita do usuário
3. Log de auditoria

**Veja mais:** `docs/SEGURANCA-CREDENCIAIS.md`

---

## 📚 Documentação Adicional

- **PRD Revisado:** `docs/PRD-REVISADO.md`
- **Exemplos Linear:** `docs/EXEMPLOS-LINEAR-INTEGRACAO.md`
- **Integração Metodologias:** `docs/INTEGRACAO-METODOLOGIAS-CHAT.md`
- **Segurança:** `docs/SEGURANCA-CREDENCIAIS.md`
- **CLAUDE.md:** Referência rápida para desenvolvimento

---

## ✅ Checklist de Validação

Depois de rodar os testes, confirme:

- [ ] ✅ GLPI: Sessão iniciada com sucesso
- [ ] ✅ GLPI: Tickets listados corretamente
- [ ] ✅ Zabbix: Problemas/alertas retornados
- [ ] ✅ Zabbix: Hosts encontrados
- [ ] ✅ Linear: Teams listados
- [ ] ✅ Linear: Issues retornadas
- [ ] ✅ Nenhum erro de autenticação
- [ ] ✅ Credenciais válidas

Se todos os itens estão ✅, você está pronto para:
1. Integrar as tools no chat
2. Testar fluxos ITIL completos
3. Aplicar metodologias (GUT, RCA, 5W2H)

---

## 🆘 Suporte

**Problemas?**

1. Revise o output dos testes
2. Verifique `.env` tem todas as variáveis
3. Confirme conectividade de rede
4. Consulte `docs/SEGURANCA-CREDENCIAIS.md`

**Contato:**
- Equipe DeepCode VSA
- TI Hospital Evangélico

---

**Última atualização:** Janeiro 2026
**Status:** ✅ Pronto para uso
