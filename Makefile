.PHONY: help install install-frontend dev api studio frontend test test-integrations test-linear-project setup-db setup-planning-db \
	build build-backend build-frontend rebuild rebuild-all up down up-build \
	status logs-backend logs-frontend logs-postgres logs-worker logs-flower \
	restart-backend restart-frontend restart-postgres restart-worker \
	cleanup-checkpoints cleanup-checkpoints-dry-run health clean-frontend-cache maintenance queue-test

help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "Instalação:"
	@echo "  make install       - Instala dependências Python"
	@echo "  make install-frontend - Instala dependências do frontend (pnpm)"
	@echo "  make setup-db      - Configura banco de dados (executa scripts SQL)"
	@echo "  make setup-planning-db - Aplica schema de planning (projetos/etapas/orcamento)"
	@echo ""
	@echo "Build:"
	@echo "  make build         - Build de todos os containers (backend + frontend)"
	@echo "  make build-backend - Build apenas do container backend"
	@echo "  make build-frontend - Build apenas do container frontend"
	@echo "  make rebuild       - Rebuild completo sem cache (backend + frontend)"
	@echo "  make rebuild-all   - Rebuild de todos os containers sem cache"
	@echo "  make up            - Inicia todos os containers Docker"
	@echo "  make down          - Para todos os containers Docker"
	@echo "  make up-build      - Build e inicia todos os containers"
	@echo ""
	@echo "Desenvolvimento:"
	@echo "  make dev           - Inicia servidor de desenvolvimento (API)"
	@echo "  make frontend      - Inicia frontend Next.js (local)"
	@echo "  make studio        - Inicia LangGraph Studio"
	@echo "  make test          - Executa testes"
	@echo "  make test-integrations   - Testa APIs de integração (GLPI, Zabbix, Linear)"
	@echo "  make test-linear-project - Testa criação de projetos no Linear (dry_run)"
	@echo ""
	@echo "Docker:"
	@echo "  make status        - Mostra status dos containers Docker"
	@echo "  make logs-backend  - Mostra logs recentes do backend"
	@echo "  make logs-frontend - Mostra logs recentes do frontend"
	@echo "  make logs-postgres - Mostra logs recentes do Postgres"
	@echo "  make logs-worker   - Mostra logs do Celery Worker"
	@echo "  make logs-flower   - Mostra logs do Flower (Monitor)"
	@echo "  make restart-backend  - Reinicia o backend"
	@echo "  make restart-frontend - Reinicia o frontend (limpa cache automaticamente)"
	@echo "  make restart-postgres - Reinicia o Postgres"
	@echo "  make restart-worker   - Reinicia o Celery Worker"
	@echo "  make clean-frontend-cache - Limpa cache do Next.js (.next) no container"
	@echo ""
	@echo "Manutenção:"
	@echo "  make maintenance   - 🚑 Limpeza profunda e reset do Docker (corrige erros de ContainerConfig)"
	@echo "  make cleanup-checkpoints       - Limpa checkpoints antigos (padrão 180 dias)"
	@echo "  make cleanup-checkpoints-dry-run - Simula limpeza de checkpoints"
	@echo "  make health       - Verifica /health da API backend"
	@echo "  make queue-test   - Envia task de teste para a fila Celery"

install:
	pip install -r requirements.txt

install-frontend:
	cd frontend && pnpm install

build:
	@echo "Building backend e frontend containers..."
	docker compose build backend frontend

build-backend:
	@echo "Building backend container..."
	docker compose build backend

build-frontend:
	@echo "Building frontend container..."
	docker compose build frontend

rebuild:
	@echo "Rebuild completo (sem cache) de backend e frontend..."
	docker compose build --no-cache backend frontend

rebuild-all:
	@echo "Rebuild completo de TODOS os containers (sem cache)..."
	docker compose build --no-cache

setup-db:
	@echo "Configurando banco de dados..."
	@echo "Certifique-se de que o PostgreSQL está rodando e o banco 'ai_agent_db' existe"
	psql -U postgres -d ai_agent_db -f sql/kb/01_init.sql
	psql -U postgres -d ai_agent_db -f sql/kb/02_indexes.sql
	psql -U postgres -d ai_agent_db -f sql/kb/03_functions.sql
	psql -U postgres -d ai_agent_db -f sql/kb/04_archived_threads.sql
	@echo "Banco de dados configurado!"

dev:
	uvicorn api.main:app --reload --port 8000

frontend:
	cd frontend && pnpm run dev

up:
	@echo "Iniciando todos os containers..."
	docker compose up -d

down:
	@echo "Parando todos os containers..."
	docker compose down

up-build:
	@echo "Building e iniciando todos os containers..."
	docker compose up -d --build

studio:
	cd backend && langgraph dev

test:
	pytest tests/ -v

test-integrations:
	@echo "Testando APIs de integração (GLPI, Zabbix, Linear)..."
	uv run python scripts/test_integrations.py

test-linear-project:
	@echo "Testando criação de projetos no Linear (dry_run)..."
	uv run python scripts/test_linear_project.py

status:
	@echo "Status dos containers Docker:"
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs-backend:
	@echo "Logs do backend (ai_agent_backend):"
	docker logs ai_agent_backend --tail 100 -f

logs-frontend:
	@echo "Logs do frontend (ai_agent_frontend):"
	docker logs ai_agent_frontend --tail 100 -f

logs-postgres:
	@echo "Logs do Postgres (ai_agent_postgres):"
	docker logs ai_agent_postgres --tail 100 -f

logs-worker:
	@echo "Logs do Celery Worker:"
	docker logs ai_agent_celery_worker --tail 100 -f

logs-flower:
	@echo "Logs do Flower:"
	docker logs ai_agent_flower --tail 100 -f

restart-backend:
	@echo "Reiniciando backend..."
	docker compose restart backend

restart-frontend:
	@echo "Reiniciando frontend (limpando cache)..."
	docker exec ai_agent_frontend sh -c "rm -rf .next" 2>/dev/null || true
	docker compose restart frontend

restart-worker:
	@echo "Reiniciando Celery Worker..."
	docker compose restart celery_worker

clean-frontend-cache:
	@echo "Limpando cache do Next.js (.next) no container frontend..."
	docker exec ai_agent_frontend sh -c "rm -rf .next" || echo "Container não está rodando ou cache já limpo"

restart-postgres:
	@echo "Reiniciando Postgres..."
	docker compose restart postgres

cleanup-checkpoints:
	@echo "Limpando checkpoints antigos (180 dias) dentro do container backend..."
	docker exec -e PYTHONPATH=/app ai_agent_backend python scripts/cleanup_checkpoints.py --days 180

cleanup-checkpoints-dry-run:
	@echo "Simulando limpeza de checkpoints antigos (180 dias) dentro do container backend..."
	docker exec -e PYTHONPATH=/app ai_agent_backend python scripts/cleanup_checkpoints.py --days 180 --dry-run

health:
	@echo "Verificando /health da API backend..."
	curl -s http://localhost:8000/health || echo "Falha ao acessar /health"
	@echo

setup-planning-db:
	@echo "Aplicando schema de planning no PostgreSQL (05 + 06 RAG)..."
	docker exec -i ai_agent_postgres psql -U postgres -d ai_agent_db < sql/kb/05_planning_schema.sql
	docker exec -i ai_agent_postgres psql -U postgres -d ai_agent_db < sql/kb/06_rag_planning.sql
	docker exec -i ai_agent_postgres psql -U postgres -d ai_agent_db < sql/kb/07_model_agnostic.sql
	@echo "✅ Schema de planning e RAG (project_id) aplicados com sucesso!"

maintenance:
	@echo "🚑 Iniciando manutenção profunda (reset do Docker)..."
	@echo "1. Parando containers..."
	-docker compose down --remove-orphans
	@echo "2. Removendo containers fantasmas..."
	-docker ps -aq | grep "ai_agent" | xargs -r docker rm -f
	@echo "3. Subindo ambiente novamente com build..."
	docker compose up -d --build --force-recreate
	@echo "✅ Manutenção concluída!"

queue-test:
	@echo "Enviando task de teste para a fila..."
	curl -X POST http://localhost:8000/api/v1/queue/agent/enqueue \
	  -H "Content-Type: application/json" \
	  -d '{"prompt": "Healthcheck via Make", "priority": 10}'
	@echo ""

schedule-test:
	@test -n "$$TELEGRAM_BOT_TOKEN" || (echo "Set TELEGRAM_BOT_TOKEN env var first" && exit 1)
	@test -n "$$TELEGRAM_CHAT_ID" || (echo "Set TELEGRAM_CHAT_ID env var first" && exit 1)
	@echo "Criando agendamento de teste (Universal Scheduler)..."
	curl -X POST http://localhost:8000/api/v1/automation/schedule \
	  -H "Content-Type: application/json" \
	  -d '{"cron": "*/2 * * * *", "prompt": "Teste Agendado via Make", "name": "Healthcheck Make Schedule", "config": {"channel": "telegram", "target_id": "'$$TELEGRAM_CHAT_ID'", "credentials": {"token": "'$$TELEGRAM_BOT_TOKEN'"}}, "enabled": true}'
	@echo ""
	@echo "Agendamento criado! Verifique logs com 'make logs-backend' ou 'make logs-worker'"
