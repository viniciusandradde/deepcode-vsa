# DeepCode VSA - Contexto de Retomada

> **Use este prompt ao iniciar novas sessões para continuar de onde parou.**

## Projeto

**DeepCode VSA** - Virtual Support Agent para Gestão de TI
**Stack**: Python 3.11 + FastAPI + LangGraph (Backend) | Next.js 15 + React (Frontend)
**Arquitetura**: Chat-First com metodologias ITIL integradas

## Status Atual (27/01/2026)

### ✅ Fase 1 - COMPLETA

- [x] Integração dinâmica de tools (GLPI, Zabbix, Linear)
- [x] Toggles no frontend (SettingsPanel.tsx)
- [x] Testes validados: GLPI, Zabbix, Linear 100% funcionais

### ✅ Fase 2.1-2.5 - COMPLETA

- [x] System Prompt ITIL em `api/routes/chat.py`
- [x] Classificação automática (Incident/Problem/Change/Request)
- [x] GUT Score (Gravidade x Urgência x Tendência)
- [x] `ITILBadge.tsx` para exibir classificação visual
- [x] Botão "Cancelar" envio de mensagem (AbortController)

### 🔄 Próximos Passos (Fase 2.6+)

- [ ] **2.6** Node `Planner` para planos de ação ITIL
- [ ] **2.7** `StructuredResponse.tsx` para respostas estruturadas
- [ ] **2.8** Confirmação do usuário para operações WRITE
- [ ] **2.9** Execução step-by-step com feedback visual

### 📋 Fase 3 - Correlação (Futuro)

- [ ] Correlação GLPI ↔ Zabbix ↔ Linear
- [ ] Timeline de eventos cross-system
- [ ] RCA (5 Whys) automatizado

## Arquivos Chave

| Arquivo | Descrição |
|---------|-----------|
| `api/routes/chat.py` | Endpoints + VSA_ITIL_SYSTEM_PROMPT |
| `frontend/src/state/useGenesisUI.tsx` | Estado global do frontend |
| `frontend/src/components/app/ChatPane.tsx` | Interface de chat |
| `frontend/src/components/app/ITILBadge.tsx` | Badge visual ITIL |
| `frontend/src/components/app/SettingsPanel.tsx` | Toggles VSA |
| `core/tools/glpi.py` | Tools LangChain para GLPI |
| `core/tools/zabbix.py` | Tools LangChain para Zabbix |
| `core/tools/linear.py` | Tools LangChain para Linear |
| `docs/PRD-REVISADO.md` | Roadmap completo do projeto |
| `.agent/ARCHITECTURE.md` | Visão geral da arquitetura |

## Ambiente

```bash
# Iniciar containers
docker compose up -d

# Testar integrações
.venv/bin/python scripts/test_integrations.py --all

# Reiniciar após mudanças
docker compose restart backend frontend

# Logs
docker compose logs -f backend
docker compose logs -f frontend
```

**URLs**:

- Frontend: <http://localhost:3000>
- Backend: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>

## Credenciais (via .env)

| Serviço | Método | Status |
|---------|--------|--------|
| GLPI | Basic Auth + App Token | ✅ Funcional |
| Zabbix | API Token | ✅ Funcional |
| Linear | API Key | ✅ Funcional |
| OpenRouter | API Key | ✅ Funcional |

## Bloqueadores Conhecidos

1. **PostgresSaver do LangGraph**: TypeError ao inicializar. Usando `MemorySaver` como solução temporária.
2. **Lint warnings**: Tabelas em arquivos .md têm warnings de formatação (não crítico).

## Como Usar Este Prompt

1. Copie todo o conteúdo deste arquivo
2. Cole como primeira mensagem em uma nova sessão
3. Adicione sua instrução específica, por exemplo:
   - "Continuar com Task 2.6 - Node Planner"
   - "Corrigir o PostgresSaver"
   - "Implementar StructuredResponse.tsx"

---

**INSTRUÇÃO PARA O AGENTE**: Leia `docs/PRD-REVISADO.md` e `.agent/ARCHITECTURE.md` para contexto completo. Pergunte qual tarefa devo executar ou sugira a próxima baseada no roadmap.
