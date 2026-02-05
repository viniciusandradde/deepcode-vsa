# Exemplos de Integração Linear.app no Fluxo ITIL

**Documento:** Casos de Uso Linear + VSA
**Objetivo:** Demonstrar como Linear.app se integra às metodologias ITIL/GUT no chat VSA
**Data:** Janeiro 2026

---

## Sumário

1. [Visão Geral do Linear no VSA](#1-visão-geral)
2. [Caso de Uso 1: Change Management](#2-change-management)
3. [Caso de Uso 2: Problem Management com Dev](#3-problem-management-com-dev)
4. [Caso de Uso 3: Incident com Escalação](#4-incident-com-escalação)
5. [Caso de Uso 4: Correlação Tripla](#5-correlação-tripla-glpi-zabbix-linear)
6. [Configuração e Setup](#6-configuração-e-setup)

---

## 1. Visão Geral

### Por que Linear.app no VSA?

**Linear.app** é uma ferramenta moderna de gestão de projetos/issues especialmente popular entre equipes de desenvolvimento. Integrá-la ao VSA permite:

1. **Ponte entre TI e Dev**: Conectar problemas de infraestrutura com tasks de desenvolvimento
2. **Change Management Moderno**: Usar Linear para rastrear mudanças planejadas
3. **Melhor UX**: Interface mais moderna que GLPI para algumas equipes
4. **Transparência**: Stakeholders acompanham issues sem acessar múltiplos sistemas

### Arquitetura de Integração

```
┌────────────────────────────────────────────────────────────┐
│                    VSA Agent (Chat)                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ GLPI         │  │ Zabbix       │  │ Linear       │    │
│  │ (ITSM)       │  │ (Monitoring) │  │ (Projects)   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │             │
│         └─────────────────┴──────────────────┘             │
│                          │                                 │
│                   Correlação e                             │
│                  Orquestração                              │
└────────────────────────────────────────────────────────────┘

Exemplo de fluxo:
1. Alerta Zabbix detecta problema
2. VSA cria ticket GLPI (registro ITSM)
3. VSA cria issue Linear (tarefa para dev)
4. Correlaciona os 3 items automaticamente
```

---

## 2. Change Management

### Cenário

Equipe de TI precisa planejar uma mudança importante (upgrade de servidor) e rastrear todas as tarefas necessárias.

### Fluxo de Conversação

```
👤 Usuário: "Preciso planejar o upgrade do servidor de banco de dados para PostgreSQL 16"

🤖 VSA Agent:

🔍 Classificação ITIL: CHANGE
📊 Prioridade GUT: 75 (Gravidade: 3, Urgência: 5, Tendência: 5)

📋 Plano de Change Management (ITIL):

1️⃣ PLANEJAMENTO
   - Avaliar impacto
   - Definir janela de manutenção
   - Criar plano de rollback

2️⃣ APROVAÇÃO
   - Validação de stakeholders
   - Aprovação de change board

3️⃣ IMPLEMENTAÇÃO
   - Backup completo
   - Upgrade incremental
   - Validação de serviços

4️⃣ REVISÃO
   - Documentação
   - Lições aprendidas

🔧 Próxima Ação: Criar estrutura de rastreamento

Deseja que eu:
✅ Crie um ticket GLPI de Change Request?
✅ Crie issues no Linear para cada etapa?

👤 Usuário: "Sim, crie ambos"

🤖 VSA Agent:

📋 PREVIEW - Change Request GLPI (DRY-RUN)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: [CHANGE] Upgrade PostgreSQL 15 → 16
Tipo: Change Request
Prioridade: Alta
Impacto: Alto (produção)
Urgência: Média

Descrição:
Upgrade planejado do servidor de banco de dados
principal de PostgreSQL 15 para PostgreSQL 16.

Justificativa:
- Melhorias de performance
- Patches de segurança
- Features necessárias para novas aplicações

Janela sugerida: Domingo 02:00-06:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PREVIEW - Issues Linear (DRY-RUN)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Issue 1: [INFRA] Avaliar impacto do upgrade PG16
   Team: Infrastructure
   Priority: High
   Labels: change-management, database, planning

   Description:
   - Listar aplicações dependentes
   - Verificar compatibilidade de queries
   - Estimar tempo de downtime
   - Criar matriz de impacto

🔹 Issue 2: [INFRA] Criar plano de backup e rollback
   Team: Infrastructure
   Priority: Urgent
   Labels: change-management, database, backup
   Blocked by: Issue 1

   Description:
   - Backup full do PostgreSQL 15
   - Testar restore em ambiente de staging
   - Documentar procedimento de rollback
   - Definir critérios de go/no-go

🔹 Issue 3: [DEV] Validar queries e features PG16
   Team: Development
   Priority: High
   Labels: change-management, database, testing

   Description:
   - Revisar queries críticas
   - Testar novos recursos do PG16
   - Atualizar ORMs se necessário
   - Validar performance

🔹 Issue 4: [INFRA] Executar upgrade em staging
   Team: Infrastructure
   Priority: High
   Labels: change-management, database, staging
   Blocked by: Issues 1, 2, 3

   Description:
   - Realizar upgrade em ambiente de staging
   - Executar suite de testes
   - Monitorar performance
   - Documentar problemas encontrados

🔹 Issue 5: [INFRA] Upgrade produção + Validação
   Team: Infrastructure
   Priority: Urgent
   Labels: change-management, database, production
   Blocked by: Issue 4

   Description:
   - Executar backup pré-upgrade
   - Realizar upgrade em produção
   - Validar serviços críticos
   - Monitorar 24h pós-upgrade
   - Criar relatório final

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total de Issues: 5
Estimativa: 3-4 semanas
Dependencies: 4 bloqueios configurados

✅ Confirmar criação? (Digite 'sim' ou 'não')

👤 Usuário: "Sim, criar"

🤖 VSA Agent:

✅ CRIADO!

📋 Change Request GLPI
   ID: #1450
   URL: https://glpi.example.com/ticket/1450

📋 Linear Issues
   🔹 INFRA-234: Avaliar impacto
      URL: https://linear.app/team/INFRA-234

   🔹 INFRA-235: Plano de backup
      URL: https://linear.app/team/INFRA-235

   🔹 DEV-112: Validar queries
      URL: https://linear.app/team/DEV-112

   🔹 INFRA-236: Upgrade staging
      URL: https://linear.app/team/INFRA-236

   🔹 INFRA-237: Upgrade produção
      URL: https://linear.app/team/INFRA-237

🔗 VINCULAÇÃO:
   Adicionei referência ao ticket GLPI #1450 em todas
   as issues Linear para rastreabilidade completa.

📊 PRÓXIMOS PASSOS:
   1. Assign das issues para os responsáveis
   2. Definir datas/milestones no Linear
   3. Agendar reunião de kick-off
   4. Iniciar INFRA-234 (avaliação de impacto)

Deseja que eu configure notificações automáticas para
atualizações destas issues?
```

---

## 3. Problem Management com Dev

### Cenário

Problema recorrente que requer investigação técnica do time de desenvolvimento.

### Fluxo de Conversação

```
👤 Usuário: "Nosso sistema de relatórios fica lento toda vez que geramos
relatórios mensais. Preciso entender por que e resolver definitivamente."

🤖 VSA Agent:

🔍 Classificação ITIL: PROBLEM
📊 Prioridade GUT: 100 (Gravidade: 4, Urgência: 5, Tendência: 5)

🔎 Executando diagnóstico...

1️⃣ Consultando histórico Zabbix (últimos 3 meses)...
   ✓ Padrão identificado:
     - Todo dia 1º do mês, CPU spike 90%+ (18:00-20:00)
     - Query PostgreSQL lentas detectadas
     - Timeout em 15% das requisições

2️⃣ Consultando tickets GLPI...
   ✓ 9 tickets relacionados nos últimos 3 meses
     - Todos reportados entre dia 1-3 do mês
     - Keyword: "relatório mensal lento/não carrega"

3️⃣ Consultando issues Linear...
   ✓ 2 issues antigas relacionadas (já fechadas):
     - DEV-089: "Otimizar query de relatórios" (fechada 6 meses atrás)
     - DEV-045: "Cache de relatórios" (fechada 8 meses atrás)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 ROOT CAUSE ANALYSIS (5 Whys)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ Por que relatórios mensais ficam lentos?
↳ 💬 Query SQL processa milhões de registros sem otimização

❓ Por que a query não está otimizada?
↳ 💬 Foi otimizada antes (DEV-089) mas regrediu

❓ Por que houve regressão?
↳ 💬 Novos filtros adicionados sem considerar performance

❓ Por que filtros foram adicionados sem análise?
↳ 💬 Falta de process de code review para queries críticas

❓ Por que não há process de review?
↳ 💬 Não existe guideline documentada para queries SQL

✅ CAUSA RAIZ IDENTIFICADA:
Ausência de guidelines + code review para queries SQL críticas,
resultando em regressões de performance em features existentes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ANÁLISE 5W2H
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT (O que?)
→ Lentidão recorrente em relatórios mensais

WHY (Por que?)
→ Queries SQL não otimizadas + ausência de code review

WHERE (Onde?)
→ Módulo de relatórios (reports service)

WHEN (Quando?)
→ Todo dia 1º do mês, horário de pico (18:00-20:00)

WHO (Quem?)
→ Impacta gestores (~50 usuários) + equipe de BI

HOW (Como resolver?)
→ 1. Re-otimizar queries críticas
→ 2. Implementar cache inteligente
→ 3. Criar SQL guidelines
→ 4. Estabelecer code review obrigatório

HOW MUCH (Quanto custa?)
→ Impacto atual: 2h inatividade/mês + frustração
→ Investimento: 2 sprints de dev (40h)
→ Benefício: Eliminação completa do problema

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 PROPOSTA DE SOLUÇÃO:

Criar estrutura completa de rastreamento:

📋 GLPI:
   - Ticket de Problem Management (registro ITSM)
   - Vincular 9 tickets históricos como relacionados

📋 Linear (Time Dev):
   - Epic: "Performance de Relatórios Mensais"
   - Issues detalhadas por solução proposta
   - Milestone: "Q1 2026 - Performance"

Deseja que eu crie esta estrutura?

👤 Usuário: "Sim"

🤖 VSA Agent:

✅ ESTRUTURA CRIADA!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 GLPI Problem Management
   ID: #1451
   Título: [PROBLEM] Lentidão Recorrente - Relatórios Mensais
   Status: Em Análise
   Prioridade: Alta
   URL: https://glpi.example.com/ticket/1451

   Vinculados: 9 tickets históricos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Linear Epic + Issues

📦 EPIC: Performance Relatórios Mensais
   Team: Development
   Priority: High
   Milestone: Q1 2026
   URL: https://linear.app/team/epic/PERF-01

   Issues incluídas:

   🔸 DEV-113: Analisar e documentar queries lentas
      Priority: Urgent
      Estimate: 5 points
      Description:
      - Executar EXPLAIN ANALYZE em queries críticas
      - Identificar missing indexes
      - Documentar bottlenecks
      - Baseline de performance atual

   🔸 DEV-114: Otimizar queries de agregação
      Priority: High
      Estimate: 8 points
      Blocked by: DEV-113
      Description:
      - Adicionar indexes compostos necessários
      - Reescrever queries ineficientes
      - Implementar materialised views se aplicável
      - Validar em staging com dados reais

   🔸 DEV-115: Implementar cache de relatórios
      Priority: High
      Estimate: 13 points
      Blocked by: DEV-114
      Description:
      - Cache Redis para relatórios comuns
      - Invalidação automática quando dados mudam
      - TTL configurável por tipo de relatório
      - Métricas de hit rate

   🔸 DEV-116: Criar SQL Performance Guidelines
      Priority: Medium
      Estimate: 5 points
      Description:
      - Documentar boas práticas SQL
      - Checklist de code review para queries
      - Exemplos de otimizações comuns
      - Integrar ao processo de PR review

   🔸 DEV-117: Setup de performance monitoring
      Priority: Medium
      Estimate: 8 points
      Description:
      - Query performance monitoring (pg_stat_statements)
      - Alertas para queries lentas
      - Dashboard de performance SQL
      - Logs estruturados para debugging

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ESTIMATIVAS:
   Total Points: 39
   Sprints: 2 (assumindo 20 points/sprint)
   Prazo: ~4 semanas

🔗 RASTREABILIDADE:
   ✓ Ticket GLPI #1451 linkado em todas issues Linear
   ✓ Issues Linear referenciadas no ticket GLPI
   ✓ 9 tickets históricos vinculados ao problem

📈 MÉTRICAS DE SUCESSO:
   - Tempo de geração de relatório: < 5s (baseline: 45s)
   - Zero timeouts em relatórios mensais
   - Query performance < 1s (baseline: 15s)
   - Hit rate de cache > 80%

🎯 PRÓXIMOS PASSOS:
   1. Assign DEV-113 para senior dev
   2. Priorizar no próximo sprint planning
   3. Configurar alertas no Zabbix para queries lentas
   4. Agendar review com time de BI

Deseja que eu configure monitoramento proativo para este problema?
```

---

## 4. Incident com Escalação

### Cenário

Incident crítico que requer escalação rápida para time de desenvolvimento.

### Fluxo de Conversação

```
👤 Usuário: "Sistema de pagamentos está retornando erro 500
para todos os usuários!"

🤖 VSA Agent:

🔴 INCIDENT CRÍTICO DETECTADO!

🔍 Classificação ITIL: INCIDENT
📊 Prioridade GUT: 125 (Gravidade: 5, Urgência: 5, Tendência: 5)
⏰ SLA: 15 minutos para resposta inicial

🚨 Executando diagnóstico emergencial...

1️⃣ Zabbix (últimos 5min):
   ⚠️ CRITICAL: payment-api-01 - HTTP 500 errors (100%)
   ⚠️ WARNING: payment-api-01 - Response time 15s (normal: 200ms)
   ⚠️ INFO: Database connections: 98/100 (quase saturado)

2️⃣ GLPI (últimos 15min):
   🎫 15 tickets novos com keyword "pagamento/erro"
   🎫 Tickets abertos entre 14:30-14:45 (cluster)

3️⃣ Linear:
   ✓ Última release: DEPLOY-456 (hoje, 14:20)
   ✓ Issue relacionada: DEV-234 "Refactor payment flow"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CORRELAÇÃO TEMPORAL SUSPEITA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

14:20 → Deploy DEPLOY-456 (DEV-234) em produção
14:30 → Primeiros erros 500 no payment-api
14:32 → Primeiros tickets de usuários
14:35 → Saturação de DB connections
14:45 → Você reportou o problema (agora)

📊 Probabilidade de relação: 95%
🎯 Causa provável: Deploy recente introduziu bug

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 AÇÃO IMEDIATA RECOMENDADA:

1️⃣ ROLLBACK do deploy DEPLOY-456
   - Tempo estimado: 5 minutos
   - Risco: Baixo (reverter para versão estável)
   - Impacto: Restauração imediata do serviço

2️⃣ ESCALAÇÃO para time Dev
   - Investigar bug em DEV-234
   - Criar hotfix se necessário
   - Re-deploy após validação

Deseja que eu:
✅ Crie ticket GLPI de incident?
✅ Crie issue Linear URGENTE para o dev team?
✅ Notifique on-call engineers?

👤 Usuário: "Sim, criar tudo e notificar"

🤖 VSA Agent:

⚡ AÇÕES EXECUTADAS!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 GLPI Incident
   ID: #1452
   Título: [INCIDENT-CRITICAL] Payment API - HTTP 500
   Prioridade: Crítica
   SLA: 15min
   Status: Em Atendimento
   Assignee: NOC Team
   URL: https://glpi.example.com/ticket/1452

   Vinculados: 15 tickets de usuários

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Linear Issue (URGENTE)
   ID: DEV-118
   Title: 🔴 [P0] Payment API returning 500 - ROLLBACK NEEDED
   Team: Development
   Priority: Urgent (P0)
   Labels: incident, production, payment, rollback
   Assignee: @on-call-dev
   URL: https://linear.app/team/DEV-118

   Description:
   ```
   🔴 PRODUCTION INCIDENT - IMMEDIATE ACTION REQUIRED

   TIMELINE:
   14:20 - Deploy DEPLOY-456 (DEV-234 refactor)
   14:30 - HTTP 500 errors started (100% of requests)
   14:45 - Reported by IT team

   IMPACT:
   - 100% of payment requests failing
   - 15 user tickets in 15 minutes
   - Revenue loss: ~$500/minute
   - DB connection pool near saturation (98/100)

   ROOT CAUSE (suspected):
   Recent deploy DEPLOY-456 introduced regression

   IMMEDIATE ACTION:
   1. ROLLBACK DEPLOY-456 to previous stable version
   2. Validate payment flow is working
   3. Investigate regression in DEV-234

   EVIDENCE:
   - Zabbix Alert: payment-api-01 HTTP 500
   - GLPI Ticket: #1452 (incident tracking)
   - Related Issue: DEV-234 (payment refactor)

   CONTACTS:
   - NOC Team: monitoring rollback
   - GLPI Ticket: #1452
   ```

   Related Issues:
   - DEV-234 (root cause suspect)
   - DEPLOY-456 (deployment)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 NOTIFICAÇÕES ENVIADAS:

   ✅ @on-call-dev (Linear mention)
   ✅ dev-team Slack channel (via webhook)
   ✅ noc-team (GLPI assignment)
   ✅ incident-response group (email)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ MONITORAMENTO ATIVO:

Iniciando monitoramento contínuo do incident...

14:46 → Aguardando resposta do on-call dev...
14:48 → @john-dev respondeu: "On it, rolling back now"
14:50 → Zabbix: Errors diminuindo (80% → 50% → 20%)
14:52 → Zabbix: ✅ HTTP 200 restored (100% success rate)
14:52 → @john-dev: "Rollback complete, service restored"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ INCIDENT RESOLVIDO!

⏱️ Tempo total: 7 minutos (SLA: 15min ✅)

📊 PRÓXIMAS AÇÕES (Post-Incident):

1️⃣ Post-Mortem (criado automaticamente):
   📋 Linear Issue: DEV-119 "Post-Mortem: Payment 500 Incident"

   Tópicos:
   - Timeline detalhada
   - Root cause analysis (DEV-234)
   - Lições aprendidas
   - Action items para prevenção

2️⃣ Correção do bug:
   📋 Linear Issue: DEV-120 "Fix: Payment flow regression"
   Priority: High
   Blocked by: DEV-119 (post-mortem)

3️⃣ Melhorias de processo:
   - Adicionar smoke tests ao deployment pipeline
   - Configurar canary deployment para payment API
   - Alertas mais granulares no Zabbix

Deseja que eu gere o relatório executivo do incident?
```

---

## 5. Correlação Tripla (GLPI + Zabbix + Linear)

### Cenário

Análise completa correlacionando dados de todos os três sistemas.

### Fluxo de Conversação

```
👤 Usuário: "Mostre todos os problemas ativos relacionados
à infraestrutura web e suas tasks de resolução"

🤖 VSA Agent:

🔍 Correlacionando dados de GLPI + Zabbix + Linear...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MAPA DE CORRELAÇÃO - Infraestrutura Web
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 CLUSTER 1: Servidor web-01 (Alta Prioridade)

   ⚠️ Zabbix Alerts:
      - web-01: CPU 95% (14:30) [CRITICAL]
      - web-01: Memory 90% (14:32) [WARNING]
      - web-01: Disk I/O high (14:35) [WARNING]

   🎫 GLPI Tickets:
      - #1440: "Site muito lento" (14:35, Status: Novo)
      - #1441: "Timeout ao acessar dashboard" (14:38, Status: Novo)
      - #1445: "Erro 503 intermitente" (14:40, Status: Processando)

   📋 Linear Issues:
      - INFRA-220: "Investigate web-01 performance"
        Status: In Progress
        Assignee: @maria-ops
        Labels: incident, performance

      - DEV-105: "Optimize slow dashboard queries"
        Status: Backlog
        Assignee: @paulo-dev
        Labels: performance, database
        Related: Cause identified for web-01 load

   📈 Correlação: 98%
   🎯 Causa raiz: Queries lentas no dashboard (DEV-105)
   💡 Status: Em resolução ativa

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 CLUSTER 2: Servidor web-02 (Média Prioridade)

   ⚠️ Zabbix Alerts:
      - web-02: SSL certificate expiring (7 days) [WARNING]

   🎫 GLPI Tickets:
      - Nenhum ticket relacionado

   📋 Linear Issues:
      - INFRA-215: "Renew SSL certificates (monthly routine)"
        Status: Todo
        Assignee: @carlos-ops
        Due: 2026-01-30
        Labels: maintenance, security

   📈 Correlação: 60% (preventiva)
   🎯 Tipo: Manutenção planejada
   💡 Status: Agendado

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 CLUSTER 3: Load Balancer (Baixa Prioridade)

   ⚠️ Zabbix Alerts:
      - Nenhum alerta ativo

   🎫 GLPI Tickets:
      - #1430: "Request: Add health check endpoint"
        (Status: Aguardando Dev)

   📋 Linear Issues:
      - DEV-098: "Implement /health endpoint for LB"
        Status: In Progress
        Assignee: @ana-dev
        Sprint: Sprint 5
        Labels: feature, infrastructure

   📈 Correlação: 85%
   🎯 Tipo: Feature Request
   💡 Status: Em desenvolvimento

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESUMO EXECUTIVO:

✅ Issues Totais: 11
   - Zabbix Alerts: 4
   - GLPI Tickets: 5
   - Linear Issues: 5 (3 in progress, 2 backlog)

🔴 Crítico: 1 cluster (web-01)
🟡 Médio: 1 cluster (web-02)
🟢 Baixo: 1 cluster (load balancer)

🎯 AÇÕES PRIORITÁRIAS:

1️⃣ URGENTE (web-01):
   ✓ INFRA-220 já está sendo trabalhada (@maria-ops)
   ⚠️ DEV-105 precisa ser priorizada (queries lentas)
   💡 Recomendação: Mover DEV-105 para "In Progress"

2️⃣ PLANEJADO (web-02):
   ✓ INFRA-215 agendado para próxima semana
   💡 Nenhuma ação adicional necessária

3️⃣ DESENVOLVIMENTO (LB):
   ✓ DEV-098 no sprint atual
   💡 Considerar review antes do fim do sprint

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 INSIGHTS ADICIONAIS:

📈 Tendência: Problemas de performance aumentaram 40%
    nas últimas 2 semanas (correlação Zabbix + GLPI)

🔗 Padrão: 80% dos incidents têm tasks relacionadas no Linear,
    indicando boa integração Dev ↔ Ops

⚠️ Gap: web-02 não tem tickets GLPI mas tem alerta Zabbix
    → Oportunidade de criar ticket preventivo?

Deseja que eu:
✅ Priorize DEV-105 automaticamente?
✅ Crie ticket GLPI preventivo para web-02?
✅ Gere relatório PDF desta análise?
```

---

## 6. Configuração e Setup

### 6.1 Variáveis de Ambiente

Adicione ao `.env`:

```bash
# Linear.app API
LINEAR_ENABLED=true
LINEAR_API_KEY=lin_api_your_key_here

# Opcional: Team IDs padrão
LINEAR_DEFAULT_TEAM_ID=your-team-uuid
LINEAR_INFRA_TEAM_ID=infra-team-uuid
LINEAR_DEV_TEAM_ID=dev-team-uuid
```

### 6.2 Obter API Key do Linear

1. Acesse: https://linear.app/settings/api
2. Clique em "Create new API key"
3. Nome: "DeepCode VSA Integration"
4. Permissões: Read + Write
5. Copie a key gerada (começa com `lin_api_`)

### 6.3 Encontrar Team IDs

```python
# Via chat VSA
"Liste os teams do Linear"

# Ou via Python direto
from core.tools.linear import linear_get_teams
result = await linear_get_teams()
print(result)

# Output:
# {
#   "teams": [
#     {"id": "abc-123", "name": "Infrastructure", "key": "INFRA"},
#     {"id": "def-456", "name": "Development", "key": "DEV"},
#     ...
#   ]
# }
```

### 6.4 Configurar Webhooks (Opcional)

Para notificações bidirecionais:

**Linear → VSA:**
1. Linear Settings → Webhooks
2. Create webhook
3. URL: `https://your-vsa.com/api/v1/webhooks/linear`
4. Events: Issue created, Issue updated, Issue status changed

**VSA → Linear:**
Já configurado automaticamente via `linear_add_comment`

### 6.5 Integração no Chat

**Adicionar ao endpoint de chat:**

```python
# api/routes/chat.py

from core.tools.linear import (
    linear_get_issues,
    linear_get_issue,
    linear_create_issue,
    linear_get_teams,
    linear_add_comment
)

# No endpoint /chat
tools = []
if request.enable_linear:
    tools.extend([
        linear_get_issues,
        linear_get_issue,
        linear_create_issue,
        linear_get_teams,
        linear_add_comment,
    ])

agent = VSAAgent(
    model_name=request.model,
    tools=tools,
    dry_run=True,
)
```

**Toggle no frontend:**

```tsx
// frontend/src/components/app/SettingsPanel.tsx

<div className="flex items-center gap-2">
  <Checkbox
    id="linear"
    checked={enableLinear}
    onCheckedChange={setEnableLinear}
  />
  <label htmlFor="linear" className="text-sm">
    Habilitar Linear.app Tools
  </label>
</div>
```

---

## 7. Boas Práticas

### 7.1 Quando Usar Linear vs GLPI

| Critério | GLPI | Linear |
|----------|------|--------|
| **Incident Management** | ✅ Preferencial | Escalação para dev |
| **Problem Management** | ✅ Registro oficial | Issues técnicas |
| **Change Management** | ✅ Aprovação formal | Tasks de implementação |
| **Service Request** | ✅ Workflow ITSM | Não aplicável |
| **Development Tasks** | ❌ Não recomendado | ✅ Preferencial |
| **Bug Tracking** | Pode usar | ✅ Preferencial |
| **Feature Requests** | Pode usar | ✅ Preferencial |

### 7.2 Estratégia de Dual Tracking

Para máxima rastreabilidade:

1. **GLPI**: Registro oficial ITSM (auditoria, SLA)
2. **Linear**: Execução técnica (tasks, sprints)
3. **Vinculação**: Sempre referenciar GLPI ticket no Linear issue

**Exemplo:**
```
GLPI Ticket #1450: [CHANGE] Upgrade PostgreSQL
  ↓ (referenciado em)
Linear Issue INFRA-234: Avaliar impacto upgrade PG16
Linear Issue INFRA-235: Plano de backup
Linear Issue DEV-112: Validar queries PG16
...
```

### 7.3 Labels Padronizadas

Criar labels consistentes no Linear:

- `itil-incident` - Originado de incident ITIL
- `itil-problem` - Originado de problem management
- `itil-change` - Originado de change request
- `glpi-{ticket_id}` - Vinculado ao ticket GLPI
- `zabbix-alert` - Originado de alerta Zabbix
- `vsa-created` - Criado automaticamente pelo VSA

---

## Conclusão

A integração do Linear.app no fluxo VSA cria uma **ponte poderosa entre TI e Desenvolvimento**, permitindo:

✅ **Rastreabilidade completa**: GLPI (ITSM) → Linear (Execution) → Zabbix (Monitoring)
✅ **Colaboração Dev/Ops**: Problemas de infra viram tasks de dev naturalmente
✅ **Modernização gradual**: Times podem migrar do GLPI para Linear progressivamente
✅ **Melhor UX**: Interface moderna do Linear atrai adoção
✅ **Metodologias preservadas**: ITIL aplicada, mas execução no Linear

**Próximos passos:**
1. Configurar API key do Linear
2. Testar criação de issues via chat
3. Estabelecer workflow de correlação
4. Treinar equipe nos novos fluxos

---

**Documento elaborado por:** Equipe DeepCode VSA
**Última atualização:** Janeiro 2026
