# ADR-003: Arquitetura de Agente Inteligente

## Status

**Aprovado** - Janeiro 2026

## Contexto

O DeepCode VSA precisa processar solicitações complexas de gestão de TI que envolvem:
- Análise de múltiplas fontes de dados
- Raciocínio sobre contextos complexos
- Tomada de decisões estruturadas
- Explicação clara das conclusões

Uma abordagem linear simples (prompt → resposta) não é suficiente para:
- Problemas que requerem múltiplas etapas
- Decisões que precisam de validação
- Respostas que exigem explicabilidade

## Decisão

Uso de **Agente com três componentes**: Planner, Executor e Reflector.

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Architecture                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Input ──▶ [PLANNER] ──▶ [EXECUTOR] ──▶ [REFLECTOR]   │
│                 │              │              │         │
│                 ▼              ▼              ▼         │
│            Estratégia      Ações API      Validação    │
│            de Passos       Executadas     + Síntese    │
│                                                         │
│                    ◀── Loop de Refinamento ──▶         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Justificativa

### Por que não um agente simples (ReAct)?

| Aspecto | ReAct Simples | Planner-Executor-Reflector |
|---------|---------------|---------------------------|
| Planejamento | Implícito | Explícito e auditável |
| Controle | Baixo | Alto |
| Explicabilidade | Limitada | Completa |
| Escalabilidade | Problemas simples | Problemas complexos |

### Componentes e Responsabilidades

#### Planner
- Analisa a solicitação do usuário
- Identifica APIs necessárias
- Define sequência de ações
- Considera metodologias (ITIL, GUT)

#### Executor
- Executa chamadas às APIs
- Coleta resultados
- Gerencia erros e retries
- Respeita governança (READ/WRITE)

#### Reflector
- Valida se objetivos foram atingidos
- Identifica gaps de informação
- Solicita re-planejamento se necessário
- Gera síntese executiva final

## Consequências

### Positivas

- **Explicabilidade**: Cada passo é documentado
- **Controle**: Pontos de verificação entre etapas
- **Qualidade**: Validação antes da entrega
- **Debug**: Facilita identificação de problemas
- **Governança**: Separação clara de responsabilidades

### Negativas

- Maior complexidade de implementação
- Latência adicional (múltiplas chamadas LLM)
- Custo de tokens maior

## Fluxo de Exemplo

```
Usuário: "Avaliar riscos operacionais críticos"

[PLANNER]
├── Identificar fontes: GLPI, Zabbix
├── Plano:
│   1. Buscar alertas críticos no Zabbix
│   2. Buscar chamados P1/P2 no GLPI
│   3. Correlacionar por hostname
│   4. Aplicar matriz GUT
│   5. Gerar priorização

[EXECUTOR]
├── GET /zabbix/api/alerts?severity=high
├── GET /glpi/api/tickets?priority=1,2
├── Correlação interna
└── Resultados coletados

[REFLECTOR]
├── Validar: dados completos? ✓
├── Validar: correlação faz sentido? ✓
├── Gerar síntese executiva
└── Output final para usuário
```

## Alternativas Consideradas

### ReAct Puro
Simples de implementar, mas difícil de controlar e auditar.

### Chain-of-Thought (CoT)
Bom para raciocínio, mas não separa planejamento de execução.

### Tree of Thoughts
Muito complexo para o caso de uso, overhead desnecessário.

## Referências

- [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091)
- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)
