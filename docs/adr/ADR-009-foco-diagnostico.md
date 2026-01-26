# ADR-009: Foco Inicial em Diagnóstico e Decisão

## Status

**Aprovado** - Janeiro 2026

## Contexto

Agentes de IA podem ter diferentes níveis de autonomia:

```
          Espectro de Autonomia

Análise ◄─────────────────────────► Automação
Passiva                              Completa

   │                                     │
   │  • Relatórios                       │  • Auto-remediação
   │  • Insights                         │  • Execução autônoma
   │  • Recomendações                    │  • Zero intervenção
   │                                     │
   └─────────────┬───────────────────────┘
                 │
                 ▼
         DeepCode VSA v1
         (Diagnóstico + Decisão)
```

A tentação de criar automação completa existe, mas traz riscos significativos em ambientes de TI críticos.

## Decisão

A versão inicial do DeepCode VSA será focada em **análise, correlação e recomendação**, não em automação agressiva.

## Justificativa

### Por que NÃO automação completa?

| Risco | Descrição | Impacto |
|-------|-----------|---------|
| **Ações incorretas** | LLM pode interpretar mal contexto | Alto |
| **Loops destrutivos** | Automação pode escalar problemas | Crítico |
| **Perda de controle** | Gestor não entende o que aconteceu | Alto |
| **Confiança** | Usuário não confia em "caixa preta" | Alto |
| **Compliance** | Regulações exigem aprovação humana | Crítico |

### Por que Diagnóstico e Decisão?

| Benefício | Descrição |
|-----------|-----------|
| **Valor imediato** | Insights são úteis desde o dia 1 |
| **Menor risco** | READ não causa danos |
| **Adoção mais fácil** | Usuário mantém controle |
| **Confiança gradual** | Prova valor antes de automatizar |
| **Compliance** | Humano sempre no loop |

### Matriz de Valor vs Risco

```
                  Alto Valor
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        │  ANÁLISE    │  AUTOMAÇÃO  │
        │  + DECISÃO  │  INTELIGENTE│
        │  ★ v1 aqui  │  (futuro)   │
        │             │             │
Baixo ──┼─────────────┼─────────────┼── Alto
Risco   │             │             │   Risco
        │  RELATÓRIOS │  AUTOMAÇÃO  │
        │  SIMPLES    │  CEGA       │
        │             │             │
        └─────────────┼─────────────┘
                      │
                 Baixo Valor
```

## Capacidades v1 (Diagnóstico + Decisão)

### O que o agente FAZ:

| Capacidade | Exemplo |
|------------|---------|
| **Análise** | "3 servidores estão com CPU > 90%" |
| **Correlação** | "Alerta de CPU coincide com chamado #123" |
| **Priorização** | "Servidor web01 é prioridade 1 (GUT: 125)" |
| **Recomendação** | "Recomendo escalar para equipe infra" |
| **Contexto** | "Este servidor hospeda sistema crítico ERP" |
| **Síntese** | Relatório executivo para gestor |

### O que o agente NÃO FAZ (v1):

| Capacidade | Status | Previsão |
|------------|--------|----------|
| Reiniciar serviços | Bloqueado | v2+ com aprovação |
| Escalar recursos | Bloqueado | v2+ com aprovação |
| Fechar chamados | Bloqueado | v2+ |
| Aplicar patches | Bloqueado | Avaliação futura |
| Modificar configs | Bloqueado | Não previsto |

## Fluxo Típico v1

```
┌─────────────────────────────────────────────────────────────┐
│                    Fluxo de Diagnóstico                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Gestor: "Quais são os riscos operacionais agora?"         │
│                      │                                      │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AGENTE: Coleta dados (READ)                         │   │
│  │  • Zabbix: 5 alertas ativos                        │   │
│  │  • GLPI: 12 chamados abertos                       │   │
│  │  • Correlação: 3 alertas → 3 chamados              │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AGENTE: Análise e Priorização                       │   │
│  │  • GUT aplicada                                     │   │
│  │  • 2 situações críticas identificadas              │   │
│  │  • Impacto em 150 usuários                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AGENTE: Recomendação                                │   │
│  │                                                     │   │
│  │  📊 Síntese Executiva:                             │   │
│  │                                                     │   │
│  │  1. CRÍTICO: Servidor DB01 - disco 95%             │   │
│  │     → Ação: Liberar espaço ou expandir             │   │
│  │     → Responsável: Equipe Infra                    │   │
│  │                                                     │   │
│  │  2. ALTO: API Gateway - latência elevada           │   │
│  │     → Ação: Investigar conexões                    │   │
│  │     → Responsável: Equipe Dev                      │   │
│  │                                                     │   │
│  │  Deseja que eu abra chamados para estas ações?     │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│                      ▼                                      │
│  Gestor decide: "Sim, abra para a situação 1"              │
│                      │                                      │
│                      ▼                                      │
│  AGENTE: Executa WRITE (com confirmação) → Chamado #456    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Consequências

### Positivas

- **Valor imediato**: Gestores recebem insights desde o primeiro uso
- **Menor risco**: Impossível causar danos operacionais
- **Adoção facilitada**: Baixa barreira de entrada
- **Confiança construída**: Usuário valida qualidade antes de confiar mais
- **Compliance**: Sempre há humano no loop

### Negativas

- Não resolve problemas automaticamente
- Requer interação humana para ações
- Pode parecer "limitado" para usuários avançados

## Roadmap de Autonomia

| Versão | Nível | Capacidades |
|--------|-------|-------------|
| **v1.0** | Consultor | Análise, correlação, recomendação |
| **v1.5** | Assistente | + Criação de chamados (aprovado) |
| **v2.0** | Co-piloto | + Ações de baixo risco aprovadas |
| **v3.0** | Agente | + Automação configrável |

## Alternativas Consideradas

### Automação Completa desde v1
Rejeitada por riscos operacionais e dificuldade de adoção.

### Apenas Relatórios (sem interação)
Rejeitada por baixo valor agregado.

### Modo "Playground" para testes
Considerado para v1.5 - ambiente sandbox para validar automações.

## Referências

- [Human-in-the-Loop AI](https://hbr.org/2022/03/the-power-of-human-ai-collaboration)
- [Levels of Autonomy in AI Systems](https://www.nist.gov/artificial-intelligence)
