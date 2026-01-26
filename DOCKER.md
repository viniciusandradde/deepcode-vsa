# Docker Compose - Guia de Uso

Este projeto inclui uma configuração completa do Docker Compose para facilitar o desenvolvimento e deploy.

## 📋 Serviços Incluídos

- **PostgreSQL** (com extensão pgvector) - Porta 5432
- **Backend API** (FastAPI) - Porta 8000
- **Frontend** (Next.js) - Porta 3000

## 🚀 Início Rápido

### 1. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure suas variáveis:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha:
- `OPENAI_API_KEY` - Obrigatório
- `OPENROUTER_API_KEY` - Obrigatório
- `TAVILY_API_KEY` - Opcional
- `COHERE_API_KEY` - Opcional
- `DB_PASSWORD` - Senha do PostgreSQL

### 2. Iniciar os Serviços

```bash
docker-compose up -d
```

Isso irá:
- Criar e iniciar todos os containers
- Inicializar o banco de dados PostgreSQL com pgvector
- Executar os scripts SQL de inicialização
- Iniciar a API FastAPI
- Iniciar o frontend Next.js

### 3. Verificar Status

```bash
docker-compose ps
```

### 4. Ver Logs

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

## 🔧 Comandos Úteis

### Parar os Serviços

```bash
docker-compose down
```

### Parar e Remover Volumes (limpar dados)

```bash
docker-compose down -v
```

### Reconstruir Imagens

```bash
docker-compose build --no-cache
```

### Executar Comandos no Container

```bash
# Backend
docker-compose exec backend bash
docker-compose exec backend python scripts/rag_ingest.py

# Frontend
docker-compose exec frontend sh

# PostgreSQL
docker-compose exec postgres psql -U postgres -d ai_agent_db
```

### Reiniciar um Serviço Específico

```bash
docker-compose restart backend
docker-compose restart frontend
```

## 📊 Acessos

Após iniciar os serviços:

- **API Backend**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432

## 🗄️ Banco de Dados

O banco de dados é inicializado automaticamente com:
- Extensão `pgvector` habilitada
- Scripts SQL executados em ordem:
  - `sql/kb/01_init.sql` - Schema inicial
  - `sql/kb/02_indexes.sql` - Índices
  - `sql/kb/03_functions.sql` - Funções de busca

### Conectar ao Banco de Dados

```bash
docker-compose exec postgres psql -U postgres -d ai_agent_db
```

### Backup do Banco de Dados

```bash
docker-compose exec postgres pg_dump -U postgres ai_agent_db > backup.sql
```

### Restaurar Backup

```bash
docker-compose exec -T postgres psql -U postgres -d ai_agent_db < backup.sql
```

## 🔄 Desenvolvimento

### Modo Desenvolvimento

Os serviços estão configurados para desenvolvimento com:
- **Backend**: Hot reload habilitado (`--reload`)
- **Frontend**: Modo desenvolvimento do Next.js
- **Volumes**: Código montado para edições em tempo real

### Rebuild após Mudanças

Se você alterar:
- `Dockerfile.backend` ou `Dockerfile.frontend`
- `requirements.txt` ou `package.json`

Execute:

```bash
docker-compose build
docker-compose up -d
```

## 🐛 Troubleshooting

### Erro: KeyError: 'ContainerConfig'

Este erro ocorre quando há containers corrompidos ou antigos. Execute:

```bash
# Opção 1: Usar o script de correção
./scripts/fix-docker.sh

# Opção 2: Limpeza manual
docker-compose down -v --remove-orphans
docker ps -a --filter "name=ai_agent" -q | xargs docker rm -f 2>/dev/null || true
docker volume ls --filter "name=template" -q | xargs docker volume rm 2>/dev/null || true

# Depois reconstruir
docker-compose up -d --build --force-recreate
```

### Docker em modo Swarm

Se aparecer aviso sobre "swarm mode", saia do modo swarm:

```bash
docker swarm leave --force
```

### Porta já em uso

Se alguma porta estiver em uso, altere no `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Mude 8000 para 8001
```

### Erro de permissão no script init-db.sh

```bash
chmod +x scripts/init-db.sh
```

### Erro de permissão do Docker

Se aparecer "Permission denied" ao acessar o Docker:

```bash
# Adicionar usuário ao grupo docker (requer logout/login)
sudo usermod -aG docker $USER

# Ou usar sudo (temporário)
sudo docker-compose up -d
```

### Limpar tudo e começar do zero

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

### Verificar logs de erro

```bash
docker-compose logs backend | grep -i error
docker-compose logs postgres | grep -i error
```

## 📝 Notas

- Os dados do PostgreSQL são persistidos no volume `postgres_data`
- O cache do Python é persistido no volume `backend_cache`
- Para produção, ajuste as configurações de segurança (CORS, SSL, etc.)

