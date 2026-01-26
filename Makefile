.PHONY: help install install-frontend dev api studio frontend test setup-db

help:
	@echo "Comandos disponíveis:"
	@echo "  make install       - Instala dependências Python"
	@echo "  make install-frontend - Instala dependências do frontend"
	@echo "  make setup-db      - Configura banco de dados (executa scripts SQL)"
	@echo "  make dev           - Inicia servidor de desenvolvimento (API)"
	@echo "  make frontend      - Inicia frontend Next.js"
	@echo "  make studio        - Inicia LangGraph Studio"
	@echo "  make test          - Executa testes"

install:
	pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

setup-db:
	@echo "Configurando banco de dados..."
	@echo "Certifique-se de que o PostgreSQL está rodando e o banco 'ai_agent_db' existe"
	psql -U postgres -d ai_agent_db -f sql/kb/01_init.sql
	psql -U postgres -d ai_agent_db -f sql/kb/02_indexes.sql
	psql -U postgres -d ai_agent_db -f sql/kb/03_functions.sql
	@echo "Banco de dados configurado!"

dev:
	uvicorn api.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

studio:
	cd backend && langgraph dev

test:
	pytest tests/ -v

