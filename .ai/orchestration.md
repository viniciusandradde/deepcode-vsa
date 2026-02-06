# Orquestracao de Desenvolvimento Multi-IDE

> Protocolo para manter contexto e consistencia entre Claude Code, Antigravity (Gemini),
> Cursor, GPT Codex e OpenCode. Organizado por **workstream**, nao por IDE.

---

## 1. IDEs e Mecanismos de Contexto

| IDE | Arquivo de Contexto | Leitura de Skills | Tipo |
|-----|---------------------|-------------------|------|
| **Claude Code** | `CLAUDE.md` (raiz) | `.agent/skills/` nativo | Direto |
| **Antigravity (Gemini)** | `.agent/rules/GEMINI.md` | `.agent/` completo | Nativo |
| **Cursor** | `.cursor/rules/*.mdc` | Via rules files | Adapter |
| **GPT Codex** | `codex.md` (raiz) | Inline | Adapter |
| **OpenCode** | `opencode.md` (raiz) | Inline | Adapter |
| **Augment** | `augment-guidelines.md` | Inline | Adapter |

### Fontes de Verdade

- **Desenvolvimento (skills, agents, workflows):** `.agent/` (40 skills, 21 agents, 12 workflows)
- **Contexto do projeto:** `.ai/context.md`
- **Estado de sessoes:** `.ai/progress.md`
- **Passagem de bastao:** `.ai/handoff.md`

---

## 2. Workstreams

A unidade de organizacao e o **workstream**, nao a IDE.
Qualquer IDE pode trabalhar em qualquer workstream.

| Workstream | Escopo | Skills relevantes (.agent/) | Skills relevantes (.ai/) |
|------------|--------|-----------------------------|--------------------------|
| `backend` | FastAPI, services, DB, config | api-patterns, database-design, python-patterns | database, wareline-api |
| `frontend` | Next.js, React, componentes | frontend-design, nextjs-react-expert | analytics-dashboard |
| `agents` | LangChain agents, tools, ITIL | langgraph-agent, vsa-methodologies | hospital-agents |
| `integrations` | GLPI, Zabbix, Linear clients | api-patterns | whatsapp-integration |
| `rag` | Ingestion, search, embeddings | database-design | - |
| `devops` | Docker, CI/CD, deploy | deployment-procedures | infrastructure, n8n-workflows |
| `compliance` | LGPD, audit, seguranca | vulnerability-scanner | lgpd-compliance |

---

## 3. Protocolo de Sessao

### INICIO (Toda IDE/IA deve fazer)

```
1. Ler .ai/context.md                    -> Entender o projeto
2. Ler .ai/progress.md (ultimas entradas) -> Saber o que foi feito
3. Ler .ai/handoff.md                     -> Saber pendencias
4. Ler skill relevante:
   - .agent/skills/<skill>/SKILL.md       -> Skills de desenvolvimento
   - .ai/skills/<skill>/SKILL.md          -> Skills hospital-especificas
5. Se agente especifico:
   - .agent/agents/<agent>.md             -> Agentes de dev
   - .ai/agents/<agent>.md               -> Agentes hospitalares
```

### DURANTE

1. Seguir regras da skill carregada
2. Documentar decisoes inline: `// DECISION: usar async porque...`
3. Se encontrar problema de outro workstream -> registrar no handoff.md

### FIM (Toda IDE/IA deve fazer)

1. Atualizar `.ai/progress.md` com entrada no TOPO
2. Se trabalho incompleto -> atualizar `.ai/handoff.md`
3. Se mudou arquitetura -> atualizar `.ai/context.md`
4. Commit com prefixo do workstream

---

## 4. Convencoes de Codigo

### Commits

Prefixo indica o **workstream**:

```
[workstream] tipo: descricao curta

Tipos: feat, fix, refactor, docs, test, chore, perf

Exemplos:
[backend] feat: add wareline connection pool
[agents] feat: implement triage with Manchester protocol
[frontend] fix: loading state in occupancy dashboard
[integrations] feat: zigchat webhook receiver
[devops] chore: docker-compose with redis
```

Para rastreabilidade da IDE, usar Co-Authored-By no corpo:

```
[backend] feat: add patient lookup endpoint

Tool: claude-code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Branches

```
feature/<workstream>/<descricao>
fix/<workstream>/<descricao>

Exemplos:
feature/agents/agente-triagem
fix/frontend/dashboard-responsive
feature/integrations/glpi-user-token
```

### Variaveis e Codigo

- Variaveis de negocio em portugues: `paciente`, `internacao`, `faturamento`
- Comentarios tecnicos em ingles: `// Cache-aside pattern`
- Nomes de arquivo em ingles: `patient_service.py`, `billing_router.py`
- Constantes UPPER_SNAKE_CASE: `MAX_POOL_SIZE = 10`

---

## 5. Resolucao de Conflitos

### Se duas IDEs modificaram o mesmo arquivo
1. Manter a versao mais recente (por timestamp do commit)
2. Registrar conflito em progress.md
3. IDE seguinte deve revisar o merge

### Se uma IDE discorda de decisao anterior
1. NAO reverter silenciosamente
2. Documentar em progress.md: "Discordo de ADR X porque..."
3. Criar issue/nota para revisao humana
4. Seguir a decisao existente ate revisao

### Se o context.md esta desatualizado
1. Atualizar com informacoes corretas
2. Registrar a mudanca em progress.md

---

## 6. Como cada IDE consome .agent/

### Claude Code
- Le `CLAUDE.md` na raiz automaticamente (system prompt)
- Invoca skills de `.agent/skills/` via Skill tool
- Nao precisa de adapter — acesso direto

### Antigravity (Gemini)
- Le `.agent/rules/GEMINI.md` como master config (trigger: always_on)
- Carrega agents, skills e workflows de `.agent/` nativamente
- Usa `brain/` para persistencia entre sessoes (protobuf)
- Usa `code_tracker/` para monitorar mudancas em arquivos
- Nao precisa de adapter — `.agent/` e sua estrutura nativa

### Cursor
- Le `.cursor/rules/*.mdc` (regras MDC por glob pattern)
- Precisa de adapter para gerar rules a partir de `.agent/`
- Alternativa: `.cursorrules` na raiz (formato antigo)

### GPT Codex
- Le `codex.md` na raiz automaticamente
- Precisa de adapter para consolidar contexto de `.agent/`

### OpenCode
- Le `opencode.md` na raiz automaticamente
- Precisa de adapter para consolidar contexto de `.agent/`

---

## 7. Diagrama de Fluxo

```
                    +---------------------+
                    |   Desenvolvedor     |
                    |   escolhe tarefa    |
                    +----------+----------+
                               |
                    +----------v----------+
                    |   Identifica        |
                    |   workstream        |
                    +----------+----------+
                               |
              +----------------+----------------+
              v                v                v
      +--------------+ +------------+ +--------------+
      | Ler context  | | Ler        | | Ler skill    |
      |    .md       | | progress   | | relevante    |
      +------+-------+ +-----+------+ +------+-------+
             +--------+------+               |
                      | Ler handoff.md       |
                      +----------------------+
                      v
           +--------------------+
           |   DESENVOLVER      |
           |   (com contexto)   |
           +----------+---------+
                      |
           +----------v---------+
           |   Commit com       |
           |   [workstream]     |
           +----------+---------+
                      |
         +------------+------------+
         v            v            v
  +-------------+ +----------+ +-------------+
  | Atualizar   | | Atualizar| | Atualizar   |
  | progress.md | | handoff  | | context.md  |
  | (SEMPRE)    | | (se pend)| | (se arq.    |
  |             | |          | |  mudou)     |
  +-------------+ +----------+ +-------------+
```
