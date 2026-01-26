---
description: DeepCode VSA development workflow. Activates vsa-developer agent with project context.
---

# /vsa - DeepCode VSA Development Workflow

Workflow específico para desenvolvimento do DeepCode VSA.

---

## Pré-Requisitos

Antes de qualquer implementação:

1. **Leia os documentos de referência:**
   - `CODEBASE.md` - Visão geral do projeto
   - `docs/PRD.md` - Requisitos do produto
   - `docs/adr/` - Decisões de arquitetura (9 ADRs)

2. **Ative o agente especializado:**
   - Use `@vsa-developer` para contexto específico

3. **Carregue as skills necessárias:**
   - `langgraph-agent` - Desenvolvimento com LangGraph
   - `python-patterns` - Padrões Python assíncronos
   - `api-patterns` - Design de APIs

---

## Fluxo de Desenvolvimento

### 1. Entender o Contexto

```
Perguntas a fazer:
├── Qual componente será implementado? (CLI, Agent, Integration, etc.)
├── Qual ADR é relevante para esta tarefa?
├── Existem dependências com outros componentes?
└── Quais são os critérios de aceite?
```

### 2. Verificar Arquitetura

| Componente | Caminho | ADR Relacionado |
|------------|---------|-----------------|
| CLI | `src/deepcode_vsa/cli/` | ADR-001 |
| Agent Core | `src/deepcode_vsa/agent/` | ADR-003, ADR-004 |
| Integrations | `src/deepcode_vsa/integrations/` | ADR-005, ADR-006 |
| Governance | `src/deepcode_vsa/governance/` | ADR-007 |
| LLM | `src/deepcode_vsa/llm/` | ADR-008 |

### 3. Implementar

**Princípios obrigatórios:**

- [ ] **Async-first**: Todas operações I/O são `async`
- [ ] **Pydantic**: Models tipados para validação
- [ ] **APITool contract**: Integrações seguem o contrato padrão
- [ ] **Governança**: READ automático, WRITE com dry-run
- [ ] **Type hints**: Completos em todas as funções públicas

### 4. Testar

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Specific test
pytest tests/unit/test_glpi_tool.py -v
```

### 5. Verificar

Antes de considerar a tarefa concluída:

- [ ] Código segue padrão async
- [ ] Pydantic models definidos
- [ ] Type hints completos
- [ ] Testes unitários criados
- [ ] Documentação atualizada
- [ ] Sem erros de lint

---

## Comandos Úteis

### Criar Nova Integração

```bash
# Estrutura de uma nova integração
mkdir -p src/deepcode_vsa/integrations/novo_sistema
touch src/deepcode_vsa/integrations/novo_sistema/__init__.py
touch src/deepcode_vsa/integrations/novo_sistema/client.py
touch src/deepcode_vsa/integrations/novo_sistema/tools.py
touch src/deepcode_vsa/integrations/novo_sistema/schemas.py
```

### Executar CLI (quando implementado)

```bash
# Análise
deepcode-vsa analyze "avaliar riscos operacionais"

# Consulta
deepcode-vsa query "quais chamados estão próximos do SLA?"

# Correlação
deepcode-vsa correlate "relacionar alertas do Zabbix com chamados GLPI"
```

---

## Referências Rápidas

### Stack

| Camada | Tecnologia |
|--------|------------|
| CLI | Typer + Rich |
| Agente | LangGraph |
| LLM | OpenRouter |
| HTTP | httpx (async) |
| Validação | Pydantic v2 |

### Padrão de Agente

```
Planner → Executor → Reflector
    ↑________________________|
```

### Governança

| Operação | Comportamento |
|----------|---------------|
| READ | Automático |
| WRITE | Dry-run + Confirmação |
| DELETE | Bloqueado (v1) |

---

## Checklist Final

- [ ] Código implementado e funcional
- [ ] Testes unitários passando
- [ ] Type hints completos
- [ ] Documentação atualizada
- [ ] Lint sem erros
- [ ] ADRs respeitados
