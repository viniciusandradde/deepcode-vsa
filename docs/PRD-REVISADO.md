# DeepCode VSA - PRD Revisado (v1.1)

**Versão:** 1.1 - Revisão Baseada em Template Estável
**Data:** Janeiro 2026
**Status:** Em Revisão
**Produto:** DeepCode VSA (Chat-First + API)
**Mudança Principal:** Pivô de CLI-First para **Chat-First** baseado no template estável existente

---

## Sumário Executivo

Após análise profunda do código base, identificamos que:

1. ✅ **Sistema de Chat está estável e funcional** (Frontend Next.js + Backend FastAPI)
2. ✅ **Integrações GLPI e Zabbix estão implementadas** (clients + tools LangChain)
3. ✅ **SimpleAgent e WorkflowAgent funcionam** com streaming SSE
4. ❌ **CLI não está implementado** (`deepcode_vsa/cli/` não existe)
5. ❌ **VSAAgent não está integrado ao sistema de chat**
6. ❌ **Metodologias ITIL/GUT não aplicadas no fluxo de chat**

**Proposta:** Pivotar de CLI-First para **Chat-First**, usando a interface web estável como produto principal e aplicando as metodologias de gestão de TI gradualmente no sistema de chat existente.

---

## 1. Nova Visão do Produto

### O que muda?

| Aspecto | PRD Original | PRD Revisado |
|---------|--------------|--------------|
| **Interface Principal** | CLI com comandos `deepcode-vsa` | **Chat Web** com interface Next.js |
| **Interface Secundária** | API REST | API REST (mesma) |
| **Prioridade** | Desenvolver CLI do zero | **Usar chat existente** e evoluir |
| **Timeline** | v1.0 CLI em Q1 | **v1.0 Chat inteligente** em Q1 |

### Por que pivotar?

1. **Time-to-Market**: Chat está funcional, CLI precisa ser desenvolvido do zero
2. **User Experience**: Interface web é mais acessível que CLI para gestores de TI
3. **Demonstração**: Chat visual facilita demonstração de capacidades
4. **Reuso**: Template Next.js + FastAPI já está estável e testado

---

## 2. Arquitetura Real (Como Está Implementado)

### Stack Existente e Funcional

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  ChatPane    │  │   Sidebar    │  │  Settings    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └─────────────────┴──────────────────┘                   │
│                          │                                       │
│                   useGenesisUI (Context API)                     │
│                 ┌─────────┴─────────┐                           │
│         localStorage         API calls                           │
└─────────────────┼─────────────┼─────────────────────────────────┘
                  │             │
                  │             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI + LangChain)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Routes: /api/v1/chat, /api/v1/chat/stream                │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────────┐  │
│  │                   AGENTS                                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │SimpleAgent   │  │WorkflowAgent │  │  VSAAgent    │    │  │
│  │  │(Funcional)   │  │(Funcional)   │  │(Implementado)│    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────────┐  │
│  │                   TOOLS (LangChain)                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │ GLPI Tools   │  │Zabbix Tools  │  │Tavily Search │    │  │
│  │  │✅ Criado     │  │✅ Criado     │  │✅ Funcional  │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────────┐  │
│  │              INTEGRATIONS (Clients)                        │  │
│  │  ┌──────────────┐  ┌──────────────┐                       │  │
│  │  │ GLPIClient   │  │ZabbixClient  │                       │  │
│  │  │✅ REST API   │  │✅ JSON-RPC   │                       │  │
│  │  └──────────────┘  └──────────────┘                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes Implementados

| Componente | Status | Arquivo | Funcionalidade |
|------------|--------|---------|----------------|
| **ChatPane** | ✅ Funcional | `frontend/src/components/app/ChatPane.tsx` | Interface de chat com streaming |
| **useGenesisUI** | ✅ Funcional | `frontend/src/state/useGenesisUI.tsx` | State management (sessions, messages) |
| **SimpleAgent** | ✅ Funcional | `core/agents/simple.py` | Agente básico com tools |
| **WorkflowAgent** | ✅ Funcional | `core/agents/workflow.py` | Agente com intent classification |
| **VSAAgent** | 🟡 Implementado | `core/agents/vsa.py` | Agente ITIL (não integrado) |
| **GLPIClient** | ✅ Funcional | `core/integrations/glpi_client.py` | Cliente REST GLPI |
| **ZabbixClient** | ✅ Funcional | `core/integrations/zabbix_client.py` | Cliente JSON-RPC Zabbix |
| **LinearClient** | ✅ Funcional | `core/integrations/linear_client.py` | Cliente GraphQL Linear.app |
| **GLPI Tools** | ✅ Criado | `core/tools/glpi.py` | 3 tools LangChain |
| **Zabbix Tools** | ✅ Criado | `core/tools/zabbix.py` | 2 tools LangChain |
| **Linear Tools** | ✅ Criado | `core/tools/linear.py` | 5 tools LangChain |
| **/chat endpoint** | ✅ Funcional | `api/routes/chat.py` | Chat sync + streaming |

---

## 3. Roadmap Revisado - Integração Gradual

### Fase 1: Chat Básico com Integrações (Q1 2026 - 4 semanas)

**Objetivo:** Permitir que usuários consultem GLPI e Zabbix via chat natural

#### Semana 1-2: Integração de Tools ao Chat
- [ ] **Task 1.1**: Modificar `api/routes/chat.py` para aceitar tools dinâmicos
- [ ] **Task 1.2**: Criar toggle no frontend para ativar GLPI tools
- [ ] **Task 1.3**: Criar toggle no frontend para ativar Zabbix tools
- [ ] **Task 1.4**: Testar consultas: "Liste os últimos 5 tickets do GLPI"
- [ ] **Task 1.5**: Testar consultas: "Quais alertas críticos no Zabbix?"

**Entregável:** Chat consegue consultar GLPI e Zabbix quando solicitado

#### Semana 3-4: Detecção Inteligente de Intent
- [ ] **Task 1.6**: Adaptar `WorkflowAgent` para detectar intents de gestão de TI
  - `consulta_glpi`: "mostre chamados", "quais tickets"
  - `consulta_zabbix`: "alertas", "problemas de monitoramento"
  - `consulta_correlacao`: "relacione alertas com tickets"
  - `conversa_geral`: chat normal
- [ ] **Task 1.7**: Implementar roteamento automático de tools baseado em intent
- [ ] **Task 1.8**: Adicionar contexto visual no frontend (badge "Consultando GLPI...")

**Entregável:** Chat detecta automaticamente quando usar GLPI/Zabbix tools

---

### Fase 2: Metodologias ITIL no Chat (Q1 2026 - 4 semanas)

**Objetivo:** Aplicar classificação ITIL e priorização GUT nas conversas

#### Semana 5-6: Classificação ITIL Automática
- [ ] **Task 2.1**: Integrar VSAAgent como opção de agente no chat
- [ ] **Task 2.2**: Implementar node `Classifier` no fluxo de chat
  - Detectar: Incident, Problem, Change, Request, Chat
- [ ] **Task 2.3**: Exibir classificação ITIL no frontend (badge visual)
- [ ] **Task 2.4**: Calcular GUT score automaticamente
- [ ] **Task 2.5**: Exibir GUT score no chat (ex: "🔴 Criticidade: Alta (GUT: 125)")

**Entregável:** Chat classifica automaticamente solicitações em categorias ITIL

#### Semana 7-8: Planner com Metodologias
- [ ] **Task 2.6**: Implementar node `Planner` para criar planos de ação
  - Para Incident: diagnóstico → resolução → documentação
  - Para Problem: RCA (5 Whys) → ação corretiva
- [ ] **Task 2.7**: Exibir plano de ação no chat antes de executar
- [ ] **Task 2.8**: Solicitar confirmação do usuário para planos WRITE
- [ ] **Task 2.9**: Implementar execução passo-a-passo com feedback visual

**Entregável:** Chat cria planos ITIL e solicita aprovação antes de executar

---

### Fase 3: Correlação e Análise (Q2 2026 - 4 semanas)

**Objetivo:** Correlacionar dados de múltiplas fontes e gerar insights

#### Semana 9-10: Correlação GLPI ↔ Zabbix
- [ ] **Task 3.1**: Implementar função de correlação por hostname
  - Buscar alertas Zabbix para hosts mencionados em tickets GLPI
- [ ] **Task 3.2**: Implementar análise temporal
  - "O ticket GLPI #1234 foi aberto 2 minutos após alerta Zabbix no mesmo servidor"
- [ ] **Task 3.3**: Criar visualização de linha do tempo no frontend
- [ ] **Task 3.4**: Adicionar node `Analyzer` ao VSAAgent

**Entregável:** Chat correlaciona automaticamente tickets com alertas

#### Semana 11-12: Reflector e Insights
- [ ] **Task 3.5**: Implementar node `Reflector` para validação
  - Verificar se objetivos foram atingidos
  - Sugerir ações adicionais
- [ ] **Task 3.6**: Implementar node `Integrator` para síntese executiva
- [ ] **Task 3.7**: Gerar relatórios estruturados (formato 5W2H)
- [ ] **Task 3.8**: Adicionar exportação de análise em JSON/Markdown

**Entregável:** Chat gera análises executivas com metodologias aplicadas

---

### Fase 4: Governança e Auditoria (Q2 2026 - 2 semanas)

**Objetivo:** Implementar audit trail e governança completa

#### Semana 13-14: Audit Trail Completo
- [ ] **Task 4.1**: Implementar log estruturado de todas operações
- [ ] **Task 4.2**: Salvar audit trail em banco (PostgreSQL)
- [ ] **Task 4.3**: Criar endpoint `/api/v1/audit` para consultar logs
- [ ] **Task 4.4**: Adicionar painel de auditoria no frontend
- [ ] **Task 4.5**: Implementar exportação de logs (LGPD compliance)
- [ ] **Task 4.6**: Adicionar explicabilidade em todas decisões do agente

**Entregável:** Sistema completo de auditoria e governança

---

## 4. Funcionalidades Principais Revisadas

### 4.1 Chat Inteligente com Gestão de TI

Interface web conversacional que entende comandos em linguagem natural:

```
Usuário: "Quais tickets GLPI estão próximos do SLA?"

VSA Agent:
🔍 Classificação: INCIDENT
📊 Prioridade: ALTA (GUT: 125)

Consultando GLPI...
✓ Encontrados 3 tickets críticos:
  #1234 - Servidor web01 offline (SLA: 2h restantes)
  #1235 - Banco de dados lento (SLA: 1h restante)
  #1236 - Email não funciona (SLA: 30min restantes)

💡 Recomendação: Priorizar ticket #1236 (menor tempo SLA)
```

### 4.2 Correlação Automática

```
Usuário: "Relacionar alertas Zabbix com tickets GLPI abertos hoje"

VSA Agent:
🔗 Correlacionando dados...

Análise de Correlação:
┌────────────────────────────────────────────────────┐
│ Ticket GLPI #1234: Servidor web01 offline         │
│ ↓                                                  │
│ ⚠️ Alerta Zabbix: web01 - CPU 100% (10:30)       │
│ ⚠️ Alerta Zabbix: web01 - Memory critical (10:32) │
│                                                    │
│ 📈 Timeline:                                       │
│   10:30 - Alerta CPU                              │
│   10:32 - Alerta Memory                           │
│   10:35 - Ticket GLPI aberto                      │
│                                                    │
│ 💡 Análise RCA (5 Whys):                          │
│   Por que web01 offline? → CPU/Memory saturados   │
│   Por que saturados? → Processo com memory leak   │
│   ...                                             │
└────────────────────────────────────────────────────┘

Quer que eu crie um ticket de Problem Management para análise de causa raiz?
```

### 4.3 Criação Controlada com Dry-Run

```
Usuário: "Abrir ticket crítico para servidor web01"

VSA Agent:
📋 Preview do Ticket (DRY-RUN):
┌────────────────────────────────────────────────────┐
│ Título: Servidor web01 - Análise de Causa Raiz    │
│ Tipo: PROBLEM                                      │
│ Urgência: 5 (Muito Alta)                          │
│ Prioridade: 5 (Muito Alta)                        │
│ GUT Score: 125                                     │
│                                                    │
│ Descrição:                                         │
│ Baseado em análise de correlação entre alertas    │
│ Zabbix e tickets GLPI, identificamos pattern de   │
│ memory leak no servidor web01.                    │
│                                                    │
│ Evidências:                                        │
│ - Alerta Zabbix CPU 100% (10:30)                  │
│ - Alerta Zabbix Memory critical (10:32)           │
│ - Ticket GLPI #1234 (10:35)                       │
└────────────────────────────────────────────────────┘

✅ Confirmar criação? (Digite 'sim' ou 'não')
```

---

## 5. Requisitos Funcionais Revisados

### Prioridade ALTA (v1.0 - Q1 2026)

| ID | Requisito | Status Atual | Ação Necessária |
|----|-----------|--------------|-----------------|
| **FR-01** | Chat web funcional | ✅ Completo | Manter |
| **FR-02** | Streaming de respostas | ✅ Completo | Manter |
| **FR-03** | Consultar GLPI via chat | 🟡 Tools criados | Integrar ao chat |
| **FR-04** | Consultar Zabbix via chat | 🟡 Tools criados | Integrar ao chat |
| **FR-05** | Detecção automática de intent | ❌ Não implementado | Adaptar WorkflowAgent |
| **FR-06** | Classificação ITIL | 🟡 VSAAgent criado | Integrar ao chat |
| **FR-07** | Cálculo GUT score | 🟡 VSAAgent criado | Integrar ao chat |
| **FR-08** | Dry-run para WRITE | ✅ Implementado | Testar em chat |
| **FR-09** | Multi-sessão persistente | ✅ Completo | Manter |

### Prioridade MÉDIA (v1.1 - Q2 2026)

| ID | Requisito | Implementação |
|----|-----------|---------------|
| **FR-10** | Correlação GLPI ↔ Zabbix | Fase 3 |
| **FR-11** | Planner com ITIL | Fase 2 |
| **FR-12** | RCA (5 Whys) | Fase 3 |
| **FR-13** | Audit trail completo | Fase 4 |
| **FR-14** | Exportação de análises | Fase 3 |

---

## 6. Requisitos Não Funcionais

| ID | Categoria | Requisito Revisado |
|----|-----------|-------------------|
| **NFR-01** | Interface | **Chat web como interface principal** (não CLI) |
| **NFR-02** | Execução | Servidor web (FastAPI + Next.js) |
| **NFR-03** | Arquitetura | Modularidade mantida |
| **NFR-04** | Extensibilidade | Plugin system de tools |
| **NFR-05** | Segurança | Credenciais via env vars |
| **NFR-06** | Custo | LLM híbrido (OpenRouter) |
| **NFR-07** | Performance | < 30s para consultas simples |
| **NFR-08** | UX | Feedback visual de progresso |

---

## 7. Migração de Integrações (Plano Gradual)

### Integração 1: GLPI (Semana 1-2)

**Tools Disponíveis:**
- ✅ `glpi_get_tickets` - Listar tickets
- ✅ `glpi_get_ticket_details` - Detalhes de ticket
- ✅ `glpi_create_ticket` - Criar ticket (com dry_run)

**Ações:**
1. Adicionar GLPI tools ao SimpleAgent no endpoint `/chat`
2. Criar toggle "Habilitar GLPI" no frontend
3. Testar queries: "liste tickets", "detalhes do ticket 123", "criar ticket"
4. Documentar exemplos de uso

### Integração 2: Zabbix (Semana 1-2)

**Tools Disponíveis:**
- ✅ `zabbix_get_alerts` - Listar alertas/problemas
- ✅ `zabbix_get_host` - Detalhes de host

**Ações:**
1. Adicionar Zabbix tools ao SimpleAgent no endpoint `/chat`
2. Criar toggle "Habilitar Zabbix" no frontend
3. Testar queries: "alertas críticos", "status do servidor web01"
4. Documentar exemplos de uso

### Integração 2.5: Linear.app (Semana 2-3) **NOVO**

**Tools Disponíveis:**
- ✅ `linear_get_issues` - Listar issues
- ✅ `linear_get_issue` - Detalhes de issue
- ✅ `linear_create_issue` - Criar issue (com dry_run)
- ✅ `linear_get_teams` - Listar teams
- ✅ `linear_add_comment` - Adicionar comentário

**Ações:**
1. Adicionar Linear tools ao SimpleAgent no endpoint `/chat`
2. Criar toggle "Habilitar Linear" no frontend
3. Testar queries: "liste issues do Linear", "criar issue no time de infra"
4. Integrar com fluxo ITIL: criar issues Linear para Change Management
5. Documentar exemplos de uso

**Casos de Uso:**
- **Alternativa moderna ao GLPI**: Para equipes que preferem Linear
- **Change Management**: Criar issues para mudanças planejadas
- **Incident Tracking**: Rastrear incidents em paralelo ao GLPI
- **Desenvolvimento**: Vincular problemas de TI com tasks de dev

### Integração 3: Correlação Multi-Sistema (Semana 9-10)

**Tool Novo:**
- ❌ `correlate_multi_system` - Correlacionar GLPI + Zabbix + Linear

**Ações:**
1. Criar novo tool de correlação em `core/tools/correlation.py`
2. Implementar busca por hostname/keywords em todos sistemas
3. Implementar análise temporal (timeline cross-system)
4. Vincular: Alerta Zabbix → Ticket GLPI → Issue Linear
5. Adicionar ao VSAAgent
6. Criar visualização no frontend

**Exemplo de Correlação:**
```
Alerta Zabbix (servidor web01)
  ↓
Ticket GLPI #1234 (usuário reporta)
  ↓
Issue Linear ENG-456 (time dev investiga código)
```

### Integração 4: Proxmox (Fase 2 - Q2 2026)

**Status:** Não implementado

**Ações:**
1. Criar `core/integrations/proxmox_client.py`
2. Criar tools: `proxmox_get_vms`, `proxmox_get_vm_status`
3. Integrar ao chat
4. Permitir correlação: "VMs no host onde tem alerta Zabbix"

---

## 8. Exemplos de Uso no Chat

### Exemplo 1: Consulta Simples GLPI

```
👤 Usuário: Liste os últimos 5 tickets abertos

🤖 VSA:
🔍 Intent detectado: consulta_glpi
📊 Consultando GLPI...

Últimos 5 tickets:
1. #1240 - Impressora não funciona (Novo) - Prioridade: Média
2. #1239 - VPN não conecta (Processando) - Prioridade: Alta
3. #1238 - Lentidão no sistema (Novo) - Prioridade: Baixa
4. #1237 - Email bouncing (Resolvido) - Prioridade: Média
5. #1236 - Servidor offline (Urgente) - Prioridade: Crítica

💡 Ticket #1236 requer atenção imediata (SLA: 15min restantes)
```

### Exemplo 2: Análise com Metodologia ITIL

```
👤 Usuário: O servidor web01 está com problemas, preciso entender o que está acontecendo

🤖 VSA:
🔍 Classificação ITIL: PROBLEM
📊 Prioridade GUT: 125 (Gravidade: 5, Urgência: 5, Tendência: 5)

📋 Plano de Investigação (5W2H):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT (O que?): Investigar instabilidade em web01
WHY (Por que?): Impacta serviço crítico de produção
WHERE (Onde?): Servidor web01 (datacenter principal)
WHEN (Quando?): Iniciado hoje às 10:30
WHO (Quem?): Equipe de infraestrutura
HOW (Como?): Análise de logs + correlação de alertas
HOW MUCH (Quanto?): Impacto estimado em 500 usuários
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔎 Executando diagnóstico...

1️⃣ Consultando alertas Zabbix...
   ✓ 3 alertas encontrados em web01:
     - CPU: 98% (10:30)
     - Memory: 95% (10:32)
     - Disk I/O: Alto (10:33)

2️⃣ Consultando tickets GLPI...
   ✓ Ticket #1234 aberto às 10:35

3️⃣ Correlacionando dados...
   ⚠️ Timeline sugere causa raiz: processo consumindo recursos

🧠 RCA (5 Porquês):
   Q1: Por que web01 está offline?
   A1: CPU e memória saturadas

   Q2: Por que CPU/memória saturadas?
   A2: Processo httpd consumindo recursos excessivos

   Q3: Por que httpd está consumindo recursos?
   A3: [Análise adicional necessária]

💡 Recomendações:
   1. Investigar logs do Apache (httpd)
   2. Verificar requisições suspeitas
   3. Considerar restart controlado do serviço
   4. Criar ticket de Problem Management para análise profunda

Deseja que eu crie o ticket de Problem Management?
```

### Exemplo 3: Criação de Ticket com Dry-Run

```
👤 Usuário: Sim, crie o ticket de problem management

🤖 VSA:
📋 PREVIEW - Ticket de Problem Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: [PROBLEM] Análise de Causa Raiz - web01 Instabilidade
Categoria: Problem Management
Urgência: 5 (Muito Alta)
Prioridade: 5 (Crítica)
GUT Score: 125

Descrição:
Baseado em correlação automática entre alertas Zabbix e
tickets GLPI, identificamos padrão de consumo excessivo de
recursos no servidor web01.

Evidências:
- Alerta Zabbix: CPU 98% às 10:30
- Alerta Zabbix: Memory 95% às 10:32
- Alerta Zabbix: Disk I/O Alto às 10:33
- Ticket GLPI #1234 (usuário reportou) às 10:35

Análise RCA Inicial:
Processo httpd consumindo recursos de forma anômala.
Investigação adicional necessária para identificar causa raiz.

Próximos Passos:
1. Análise de logs Apache
2. Verificação de requisições suspeitas
3. Análise de performance de aplicações web
4. Implementação de medidas preventivas

Metodologia: ITIL Problem Management + 5 Whys RCA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ MODO DRY-RUN ATIVO
Este ticket NÃO será criado automaticamente.

Para confirmar criação no GLPI, responda:
✅ "criar" ou "confirmar"
❌ "cancelar" ou "não"
```

---

## 9. Métricas de Sucesso Revisadas

### KPIs v1.0 (Q1 2026)

| Métrica | Baseline | Meta v1.0 | Medição |
|---------|----------|-----------|---------|
| **Taxa de adoção** | 0% | 80% dos analistas | Analytics |
| **Consultas GLPI via chat** | 0 | 100+/dia | Logs |
| **Consultas Zabbix via chat** | 0 | 50+/dia | Logs |
| **Tempo de diagnóstico** | 45 min | 30 min | Comparação manual |
| **Classificação ITIL automática** | 0% | 90% acurácia | Validação humana |
| **Uptime do sistema** | N/A | 99% | Monitoramento |

### Critérios de Sucesso v1.0

- [ ] ✅ Chat consegue consultar GLPI e Zabbix sem erros
- [ ] ✅ Intent detection funciona com 85%+ de acurácia
- [ ] ✅ Classificação ITIL automática implementada
- [ ] ✅ GUT score calculado corretamente
- [ ] ✅ Dry-run funciona para todas operações WRITE
- [ ] ✅ Feedback positivo de 70%+ dos usuários beta

---

## 10. Comparação: PRD Original vs Revisado

| Aspecto | PRD Original (v1.0) | PRD Revisado (v1.1) |
|---------|---------------------|---------------------|
| **Interface Principal** | CLI `deepcode-vsa` | Chat Web Next.js |
| **Status da Interface** | ❌ Não existe | ✅ Funcional |
| **Timeline** | Q1 2026 (4 meses) | Q1 2026 (3 meses) |
| **Esforço de Dev** | Alto (criar do zero) | Médio (integrar existente) |
| **Primeira Release** | CLI + integrações | Chat + integrações |
| **Integração GLPI** | A desenvolver | ✅ Client pronto |
| **Integração Zabbix** | A desenvolver | ✅ Client pronto |
| **Agente VSA** | A desenvolver | 🟡 Implementado (não integrado) |
| **Demo para Stakeholders** | Difícil (CLI) | Fácil (Web visual) |
| **User Adoption** | Baixa (CLI técnico) | Alta (Web acessível) |

---

## 11. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Mudança de escopo confunde stakeholders** | Média | Alto | Comunicar claramente o pivô e justificativa |
| **Usuários preferem CLI** | Baixa | Médio | Manter CLI no roadmap para v2.0 |
| **Performance do chat com múltiplos tools** | Média | Médio | Implementar caching e rate limiting |
| **Acurácia do intent detection** | Alta | Alto | Iteração contínua com feedback real |
| **Integração VSAAgent complexa** | Alta | Alto | Approach gradual (fase por fase) |
| **Credenciais GLPI/Zabbix não configuradas** | Média | Alto | Wizard de setup no frontend |

---

## 12. Próximos Passos Imediatos

### Semana 1 (Validação)

- [ ] **Apresentar PRD revisado para stakeholders**
- [ ] **Validar pivô de CLI para Chat**
- [ ] **Aprovar roadmap de 14 semanas**
- [ ] **Definir ambiente de testes (GLPI + Zabbix de staging)**

### Semana 2 (Setup)

- [ ] **Criar branch `feat/vsa-chat-integration`**
- [ ] **Configurar ambiente de desenvolvimento**
- [ ] **Implementar toggle de feature flags no frontend**
- [ ] **Escrever testes para integração GLPI/Zabbix**

### Semana 3-4 (Desenvolvimento Fase 1)

- [ ] **Integrar GLPI tools ao chat** (Task 1.1-1.5)
- [ ] **Integrar Zabbix tools ao chat** (Task 1.1-1.5)
- [ ] **Adaptar WorkflowAgent** (Task 1.6-1.8)
- [ ] **Deploy em staging para testes**

---

## 13. Conclusão

O **pivô de CLI-First para Chat-First** é estrategicamente correto por:

1. ✅ **Aproveitar trabalho existente** (template estável)
2. ✅ **Reduzir time-to-market** (3 meses vs 4+ meses)
3. ✅ **Facilitar demonstração** (interface visual)
4. ✅ **Aumentar adoção** (web mais acessível que CLI)
5. ✅ **Manter opção de CLI** (pode ser desenvolvido em v2.0)

A arquitetura de integrações (GLPI, Zabbix) e metodologias (ITIL, GUT, RCA) **permanece válida** - apenas muda a interface de entrega do produto.

---

## Aprovações Necessárias

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | | | ⏳ Pendente |
| Tech Lead | | | ⏳ Pendente |
| Stakeholder TI | | | ⏳ Pendente |
| Usuário Beta (Analista) | | | ⏳ Pendente |

---

**Documento gerado com base em análise profunda do código existente**
**Versão:** 1.1 (Revisão Chat-First)
**Data:** Janeiro 2026
