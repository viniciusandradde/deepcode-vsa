# DeepCode VSA - Product Requirements Document (PRD)

**Versão:** 1.0
**Data:** Janeiro 2026
**Status:** Aprovado
**Produto:** DeepCode VSA (API-First)
**Subtítulo:** Agente Inteligente CLI para Gestão de TI

---

## Sumário

1. [Visão do Produto](#1-visão-do-produto)
2. [Problema a ser Resolvido](#2-problema-a-ser-resolvido)
3. [Público-Alvo](#3-público-alvo)
4. [Objetivos do Produto](#4-objetivos-do-produto)
5. [Escopo do Produto](#5-escopo-do-produto)
6. [Funcionalidades Principais](#6-funcionalidades-principais)
7. [Requisitos Funcionais](#7-requisitos-funcionais)
8. [Requisitos Não Funcionais](#8-requisitos-não-funcionais)
9. [Metodologias de Gestão Suportadas](#9-metodologias-de-gestão-de-ti-suportadas)
10. [Arquitetura de Alto Nível](#10-arquitetura-de-alto-nível)
11. [Integrações](#11-integrações)
12. [Segurança e Governança](#12-segurança-e-governança)
13. [Métricas de Sucesso](#13-métricas-de-sucesso)
14. [Roadmap](#14-roadmap)
15. [Glossário](#15-glossário)

---

## 1. Visão do Produto

O **DeepCode VSA** é um agente inteligente em CLI (Linux, Python) que apoia gestores de TI na análise, decisão e governança, conectando-se diretamente a múltiplas APIs (GLPI, Zabbix, Proxmox, Cloud, ERP, etc.).

### O agente é capaz de:

- **Analisar** dados operacionais de múltiplas fontes
- **Correlacionar** informações entre sistemas heterogêneos
- **Priorizar** demandas baseado em metodologias consolidadas
- **Sugerir** ações baseadas em ITIL e boas práticas
- **Consultar e criar** informações via APIs, de forma segura e auditável

### Proposta de Valor

> Transformar dados dispersos de APIs em decisões de gestão inteligentes, reduzindo o tempo de diagnóstico e aumentando a maturidade operacional de TI.

---

## 2. Problema a ser Resolvido

### Contexto Atual

| Problema | Impacto |
|----------|---------|
| Dados espalhados em vários sistemas | Falta de visão holística |
| Falta de visão integrada (ITSM + Infra + Negócio) | Decisões fragmentadas |
| Decisões reativas e manuais | Tempo de resposta elevado |
| Alto custo de análise humana | Escalabilidade limitada |
| Baixa padronização de diagnósticos | Inconsistência operacional |

### Solução Proposta

O DeepCode VSA atua como um **analista virtual** que:

1. Conecta-se às APIs dos sistemas de TI
2. Coleta e normaliza dados em tempo real
3. Aplica raciocínio estruturado (ITIL, GUT, 5W2H)
4. Gera insights acionáveis para gestores

---

## 3. Público-Alvo

### Personas Primárias

| Persona | Perfil | Necessidade Principal |
|---------|--------|----------------------|
| **Gestor de TI** | Decisor estratégico | Visão consolidada e KPIs |
| **Coordenador de Infraestrutura/NOC** | Operacional técnico | Diagnóstico rápido e correlação |
| **Analista de Service Desk** | ITSM | Priorização e contexto de chamados |

### Personas Secundárias

| Persona | Perfil | Necessidade Principal |
|---------|--------|----------------------|
| **MSPs e Consultorias** | Multi-cliente | Escala e padronização |
| **TI Hospitalar** | Ambiente crítico | Compliance e auditoria |
| **TI Educacional** | Recursos limitados | Eficiência operacional |
| **TI Corporativa** | Ambientes complexos | Integração multi-sistema |

---

## 4. Objetivos do Produto

### Objetivo Principal

Criar um **agente de gestão de TI API-First**, capaz de:

- Entender contextos complexos de operação
- Correlacionar múltiplas fontes de dados
- Apoiar decisões estratégicas com base em dados
- Escalar para muitos sistemas e clientes

### Objetivos Secundários

| Objetivo | Métrica Alvo |
|----------|--------------|
| Reduzir tempo de diagnóstico | -60% no tempo médio |
| Padronizar análises | 100% aderência às metodologias |
| Aumentar maturidade ITIL | +2 níveis em 6 meses |
| Criar base para automação | Pipeline de automações definido |

---

## 5. Escopo do Produto

### Dentro do Escopo (v1.0)

| Categoria | Item | Status |
|-----------|------|--------|
| **Plataforma** | CLI local (Linux) | Confirmado |
| **Linguagem** | Python 3.11+ | Confirmado |
| **Arquitetura** | API-First | Confirmado |
| **Integrações** | Múltiplas APIs (GLPI, Zabbix, etc.) | Confirmado |
| **Agente** | LangGraph (Planner/Executor/Reflector) | Confirmado |
| **LLM** | Via OpenRouter | Confirmado |
| **Operações** | Consultas (READ) automáticas | Confirmado |
| **Operações** | Criação controlada (WRITE) | Confirmado |
| **Metodologias** | ITIL, GUT, 5W2H, PDCA, RCA | Confirmado |

### Fora do Escopo (v1.0)

| Item | Justificativa | Previsão |
|------|---------------|----------|
| Interface gráfica (Web/Desktop) | Foco em CLI para v1 | v2.0 |
| Execução destrutiva automática | Risco operacional | Avaliação futura |
| Exclusão de dados via API | Segurança | Não previsto |
| Mobile app | Fora do core | v3.0 |

---

## 6. Funcionalidades Principais

### 6.1 CLI Inteligente

Interface de linha de comando com linguagem natural:

```bash
# Análise de riscos
deepcode-vsa analyze "avaliar riscos operacionais"

# Consulta específica
deepcode-vsa query "quais chamados estão próximos do SLA?"

# Correlação
deepcode-vsa correlate "relacionar alertas do Zabbix com chamados GLPI"

# Criação controlada
deepcode-vsa create "abrir chamado crítico para servidor web01"
```

### 6.2 Integração API-First

| Sistema | Tipo | Operações v1 |
|---------|------|--------------|
| **GLPI** | ITSM | READ (chamados, SLAs), WRITE (tickets) |
| **Zabbix** | Monitoramento | READ (alertas, hosts, métricas) |
| **Proxmox** | Virtualização | READ (VMs, recursos) |
| **Cloud Providers** | IaaS | READ (instâncias, custos) |
| **ERP** | Negócio | READ (contexto organizacional) |

### 6.3 Agente Inteligente

Arquitetura de agente com três componentes:

```
┌─────────────────────────────────────────────────────────┐
│                    DeepCode VSA Agent                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌──────────┐    ┌───────────┐          │
│  │ PLANNER │───▶│ EXECUTOR │───▶│ REFLECTOR │          │
│  └─────────┘    └──────────┘    └───────────┘          │
│       │              │               │                  │
│       ▼              ▼               ▼                  │
│  Estratégia     Execução API    Validação              │
│  Multi-etapas   Controlada      e Síntese              │
└─────────────────────────────────────────────────────────┘
```

- **Planner**: Decompõe problemas complexos em etapas
- **Executor**: Executa chamadas às APIs de forma controlada
- **Reflector**: Valida resultados e gera síntese executiva

### 6.4 Governança e Segurança

| Mecanismo | Descrição |
|-----------|-----------|
| **Dry-run** | Modo padrão para operações de escrita |
| **Confirmação explícita** | Requer aprovação para WRITE |
| **Logs auditáveis** | Todas as operações são registradas |
| **Explicabilidade** | Justificativa para cada decisão |

---

## 7. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|------------|-------------------|
| **FR-01** | Executar análises via CLI | Alta | CLI aceita comandos em linguagem natural |
| **FR-02** | Consultar múltiplas APIs | Alta | Suporte a 5+ APIs diferentes |
| **FR-03** | Criar dados via API (controlado) | Alta | WRITE com confirmação explícita |
| **FR-04** | Correlacionar informações | Alta | Cruzamento de 2+ fontes de dados |
| **FR-05** | Priorizar demandas | Média | Aplicação de matriz GUT |
| **FR-06** | Gerar resposta executiva | Alta | Síntese em formato gerencial |
| **FR-07** | Suportar dezenas de APIs | Média | Registry dinâmico de APIs |
| **FR-08** | Operar com LLM externo | Alta | Integração OpenRouter funcional |
| **FR-09** | Modo dry-run | Alta | Simulação sem efeitos colaterais |
| **FR-10** | Logs de auditoria | Média | Registro de todas as operações |

---

## 8. Requisitos Não Funcionais

| ID | Categoria | Requisito | Especificação |
|----|-----------|-----------|---------------|
| **NFR-01** | Execução | Local | Sem dependência de servidor externo |
| **NFR-02** | Arquitetura | Modularidade | Componentes independentes |
| **NFR-03** | Extensibilidade | Plugins | Fácil adição de novas APIs |
| **NFR-04** | Segurança | Credenciais | Armazenamento seguro (env/vault) |
| **NFR-05** | Custo | Operacional | Uso de LLMs custo-efetivos |
| **NFR-06** | Transparência | Explicabilidade | Justificativa para decisões |
| **NFR-07** | Performance | Resposta | < 30s para consultas simples |
| **NFR-08** | Confiabilidade | Disponibilidade | Operação offline parcial |

---

## 9. Metodologias de Gestão de TI Suportadas

### ITIL v4

| Prática | Suporte |
|---------|---------|
| Gestão de Incidentes | Completo |
| Gestão de Problemas | Completo |
| Gestão de Mudanças | Parcial |
| Gestão de Ativos | Parcial |

### Frameworks de Priorização

| Metodologia | Aplicação |
|-------------|-----------|
| **Matriz GUT** | Priorização de chamados e alertas |
| **5W2H** | Estruturação de análises |
| **PDCA** | Ciclo de melhoria contínua |
| **RCA (5 Porquês)** | Análise de causa raiz |
| **Kanban** | Gestão de backlog |

---

## 10. Arquitetura de Alto Nível

```
┌────────────────────────────────────────────────────────────────────┐
│                         DeepCode VSA                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                  │
│  │   CLI Layer  │  Typer + Rich                                    │
│  └──────┬───────┘                                                  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Agent Core (LangGraph)                     │ │
│  │  ┌─────────┐    ┌──────────┐    ┌───────────┐               │ │
│  │  │ Planner │───▶│ Executor │───▶│ Reflector │               │ │
│  │  └─────────┘    └──────────┘    └───────────┘               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   API Tool Registry                           │ │
│  │  ┌──────┐ ┌──────┐ ┌─────────┐ ┌───────┐ ┌─────┐           │ │
│  │  │ GLPI │ │Zabbix│ │ Proxmox │ │ Cloud │ │ ERP │  ...      │ │
│  │  └──────┘ └──────┘ └─────────┘ └───────┘ └─────┘           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────┐                                                  │
│  │  LLM Layer   │  OpenRouter (GPT-4, Claude, Llama, etc.)        │
│  └──────────────┘                                                  │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 11. Integrações

### API Tool Contract

Todas as integrações seguem um contrato padronizado:

```python
class APITool(Protocol):
    """Contrato padrão para ferramentas de API."""

    name: str
    description: str
    operations: List[Operation]

    def read(self, query: Query) -> Result:
        """Operação de leitura (automática)."""
        ...

    def write(self, data: WriteData, dry_run: bool = True) -> Result:
        """Operação de escrita (controlada)."""
        ...
```

### Integrações Planejadas

| Fase | Sistemas | Prioridade |
|------|----------|------------|
| **v1.0** | GLPI, Zabbix | Alta |
| **v1.1** | Proxmox, AWS | Média |
| **v1.2** | Azure, GCP, ERP | Média |
| **v2.0** | Custom APIs | Baixa |

---

## 12. Segurança e Governança

### Modelo de Permissões

| Operação | Comportamento | Requisito |
|----------|---------------|-----------|
| **READ** | Automático | Credenciais válidas |
| **WRITE** | Confirmação explícita | Dry-run + Aprovação |
| **DELETE** | Bloqueado (v1) | N/A |

### Segurança de Credenciais

- Variáveis de ambiente
- Suporte a HashiCorp Vault (futuro)
- Nunca em código ou logs

### Auditoria

```json
{
  "timestamp": "2026-01-22T10:30:00Z",
  "user": "admin",
  "operation": "write",
  "target": "glpi.ticket",
  "data": { "title": "...", "priority": 3 },
  "dry_run": false,
  "result": "success",
  "explanation": "Ticket criado conforme análise de criticidade"
}
```

---

## 13. Métricas de Sucesso

### KPIs Principais

| Métrica | Baseline | Meta v1 | Medição |
|---------|----------|---------|---------|
| Tempo médio de diagnóstico | 45 min | 15 min | Analytics |
| Clareza da resposta | N/A | NPS > 8 | Survey |
| Aderência ITIL | Manual | 100% | Checklist |
| APIs integradas | 0 | 5+ | Count |
| Uptime do agente | N/A | 99% | Monitoramento |

### Critérios de Sucesso do Produto

- [ ] 80% dos usuários conseguem executar análise sem ajuda
- [ ] Redução mensurável no tempo de triagem de incidentes
- [ ] Feedback positivo de gestores sobre qualidade das análises
- [ ] Zero incidentes de segurança relacionados ao agente

---

## 14. Roadmap

### Fase 1: MVP (v1.0) - Q1 2026

- [x] Arquitetura base definida
- [ ] CLI funcional
- [ ] Integração GLPI
- [ ] Integração Zabbix
- [ ] Agente LangGraph básico
- [ ] Documentação

### Fase 2: Expansão (v1.x) - Q2 2026

- [ ] Integração Proxmox
- [ ] Integração Cloud (AWS/Azure)
- [ ] Melhorias no Reflector
- [ ] Dashboard de auditoria (CLI)

### Fase 3: Produto (v2.0) - Q3-Q4 2026

- [ ] API HTTP para integrações
- [ ] Web UI (opcional)
- [ ] Multi-tenancy
- [ ] Marketplace de integrações

---

## 15. Glossário

| Termo | Definição |
|-------|-----------|
| **API-First** | Arquitetura que prioriza integração via APIs |
| **CLI** | Command Line Interface |
| **GUT** | Gravidade, Urgência, Tendência |
| **ITIL** | Information Technology Infrastructure Library |
| **ITSM** | IT Service Management |
| **LangGraph** | Framework para construção de agentes com grafos de estado |
| **LLM** | Large Language Model |
| **MSP** | Managed Service Provider |
| **NOC** | Network Operations Center |
| **OpenRouter** | Gateway para múltiplos provedores de LLM |
| **PRD** | Product Requirements Document |
| **RCA** | Root Cause Analysis |
| **SLA** | Service Level Agreement |
| **VSA** | Virtual Support Agent |

---

## Aprovações

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | | | Pendente |
| Tech Lead | | | Pendente |
| Stakeholder | | | Pendente |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | Jan 2026 | - | Versão inicial |

---

*Documento gerado para o projeto DeepCode VSA*
