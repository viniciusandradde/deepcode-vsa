# Guia de Setup: Ambiente n8n para DeepCode VSA

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Configuração do PostgreSQL](#configuração-do-postgresql)
4. [Configuração do n8n](#configuração-do-n8n)
5. [Variáveis de Ambiente](#variáveis-de-ambiente)
6. [Subindo o Ambiente](#subindo-o-ambiente)
7. [Configuração de Credentials](#configuração-de-credentials)
8. [Verificação e Testes](#verificação-e-testes)
9. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

### Software Necessário

| Software | Versão Mínima | Para que serve |
|----------|---------------|----------------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Orquestração de containers |
| PostgreSQL Client | 14+ | Testes de banco (opcional) |
| curl/Postman | - | Testes de API |

### Verificar Instalações

```bash
# Docker
docker --version
# Output esperado: Docker version 24.0.0+

# Docker Compose
docker compose version
# Output esperado: Docker Compose version v2.20.0+

# PostgreSQL (opcional)
psql --version
# Output esperado: psql (PostgreSQL) 16.0+
```

---

## Estrutura de Arquivos

### Arquivos que Serão Criados

```
deepcode-vsa/
├── docker-compose.n8n.yml          # Configuração Docker n8n
├── .env.n8n                         # Variáveis de ambiente n8n
├── sql/n8n/                         # Scripts SQL para n8n
│   └── 01-create-n8n-schema.sql    # Schema do n8n
├── docs/n8n/                        # Workflows JSONs
│   ├── vsa-glpi-integration.json
│   ├── vsa-zabbix-integration.json
│   └── vsa-linear-integration.json
└── docs/setup/                      # Documentação (este arquivo)
    ├── n8n-setup.md
    ├── n8n-workflows-fase1.md
    └── n8n-testing.md
```

---

## Configuração do PostgreSQL

### 1. Criar Database para n8n

O n8n precisa de uma database separada para armazenar workflows, execuções e credentials.

**Arquivo:** `sql/n8n/01-create-n8n-schema.sql`

```sql
-- Criar database n8n (se não existir)
CREATE DATABASE n8n;

-- Conectar à database n8n
\c n8n

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE n8n TO postgres;

-- Nota: n8n criará suas próprias tabelas automaticamente no primeiro boot
```

### 2. Verificar Conexão com DeepCode VSA Database

O n8n precisará se conectar ao banco `ai_agent_db` para:

- RAG Search (tabelas `kb_chunks`, `kb_docs`)
- Checkpoints (tabela `checkpoints`)

**Testar conexão:**

```bash
# Entrar no container PostgreSQL
docker exec -it ai_agent_postgres psql -U postgres -d ai_agent_db

# Verificar tabelas existentes
\dt

# Output esperado:
#  public | checkpoints      | table | postgres
#  public | kb_chunks        | table | postgres
#  public | kb_docs          | table | postgres
#  public | writes           | table | postgres
```

---

## Configuração do n8n

### 1. Docker Compose n8n

**Arquivo:** `docker-compose.n8n.yml`

**Princípios:**

- Usar PostgreSQL existente (`ai_agent_postgres`)
- Expor porta 5678 para n8n UI
- Compartilhar network com FastAPI (`ai_agent_network`)
- Persistir dados n8n em volume

**Estrutura básica:**

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: deepcode_vsa_n8n
    
    environment:
      # Database n8n (metadata)
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      
      # Apontar para banco DeepCode VSA (para workflows)
      - VSA_DB_HOST=postgres
      - VSA_DB_NAME=ai_agent_db
    
    ports:
      - "5678:5678"
    
    networks:
      - ai_agent_network
    
    depends_on:
      - postgres

networks:
  ai_agent_network:
    external: true  # Usar network existente
```

### 2. Encryption Key

n8n requer uma chave de criptografia para credentials.

**Gerar chave:**

```bash
# Gerar chave aleatória de 32 caracteres
openssl rand -hex 16
# Output: 3a5f8c9d2e1b4a7c6f8e9d0a1b2c3d4e

# Adicionar ao .env.n8n
echo "N8N_ENCRYPTION_KEY=3a5f8c9d2e1b4a7c6f8e9d0a1b2c3d4e" >> .env.n8n
```

---

## Variáveis de Ambiente

### 1. Criar `.env.n8n`

**Arquivo:** `.env.n8n`

```bash
# ========================================
# n8n Core Configuration
# ========================================
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<SENHA_FORTE>

# Encryption
N8N_ENCRYPTION_KEY=<CHAVE_GERADA_ACIMA>

# Webhook URL (ajustar para produção)
WEBHOOK_URL=http://localhost:5678

# ========================================
# Database Configuration
# ========================================

# n8n Metadata Database
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=postgres
DB_POSTGRESDB_PASSWORD=postgres

# DeepCode VSA Database (para workflows)
VSA_DB_HOST=postgres
VSA_DB_PORT=5432
VSA_DB_NAME=ai_agent_db
VSA_DB_USER=postgres
VSA_DB_PASSWORD=postgres

# ========================================
# Executions Configuration
# ========================================
EXECUTIONS_MODE=regular
EXECUTIONS_DATA_SAVE_ON_ERROR=all
EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=true
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=336  # 14 dias

# ========================================
# Timezone
# ========================================
GENERIC_TIMEZONE=America/Sao_Paulo
TZ=America/Sao_Paulo

# ========================================
# External APIs (DeepCode VSA)
# ========================================

# GLPI
GLPI_BASE_URL=https://glpi.hospitalevangelico.com.br/glpi/apirest.php
GLPI_APP_TOKEN=<SEU_APP_TOKEN>
GLPI_USER_TOKEN=<SEU_USER_TOKEN>

# Zabbix
ZABBIX_BASE_URL=https://zabbix.hospitalevangelico.com.br
ZABBIX_API_TOKEN=<SEU_API_TOKEN>

# Linear
LINEAR_API_KEY=lin_api_<SUA_CHAVE>

# OpenRouter / OpenAI
OPENROUTER_API_KEY=sk-or-v1-<SUA_CHAVE>
OPENAI_API_KEY=sk-<SUA_CHAVE>

# Tavily (Web Search)
TAVILY_API_KEY=tvly-<SUA_CHAVE>
```

### 2. Copiar Credenciais do `.env` Principal

Se já possui `.env` configurado no DeepCode VSA:

```bash
# Copiar variáveis necessárias
grep -E "GLPI_|ZABBIX_|LINEAR_|OPENROUTER_|OPENAI_|TAVILY_" .env >> .env.n8n
```

---

## Subindo o Ambiente

### 1. Primeira Execução

```bash
# 1. Criar database n8n
docker exec -it ai_agent_postgres psql -U postgres -f /docker-entrypoint-initdb.d/n8n/01-create-n8n-schema.sql

# 2. Subir n8n
docker compose -f docker-compose.n8n.yml up -d

# 3. Ver logs
docker compose -f docker-compose.n8n.yml logs -f n8n

# Output esperado:
# n8n ready on http://0.0.0.0:5678
# Version: 1.xx.x
```

### 2. Acessar n8n UI

**URL:** `http://localhost:5678`

**Credenciais:**

- Usuário: `admin` (definido em .env.n8n)
- Senha: `<SENHA_FORTE>` (definida em .env.n8n)

### 3. Verificar Health Check

```bash
# Verificar status do container
docker ps | grep n8n

# Verificar endpoint de saúde
curl http://localhost:5678/healthz

# Output esperado:
# {"status":"ok"}
```

---

## Configuração de Credentials

Após primeiro login no n8n UI, configurar credentials para as APIs externas.

### 1. PostgreSQL (DeepCode VSA Database)

**Path:** Settings → Credentials → Add Credential → Postgres

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Name** | `deepcode-vsa-postgres` |
| **Host** | `postgres` |
| **Port** | `5432` |
| **Database** | `ai_agent_db` |
| **User** | `postgres` |
| **Password** | `<DB_PASSWORD>` |
| **SSL Mode** | `disable` |

**Testar Conexão:**

- Clicar em **"Test"**
- Verificar mensagem: ✅ "Connection successful"

---

### 2. OpenAI API

**Path:** Settings → Credentials → Add Credential → OpenAI

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Name** | `openai-vsa` |
| **API Key** | `sk-<SUA_CHAVE>` |

**Testar:**

- Criar workflow temporário com OpenAI node
- Executar: "Hello, test"

---

### 3. GLPI API (Custom Credential)

**Path:** Settings → Credentials → Add Credential → HTTP Header Auth

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Name** | `glpi-api-vsa` |
| **Header Name 1** | `App-Token` |
| **Header Value 1** | `<GLPI_APP_TOKEN>` |
| **Header Name 2** | `Authorization` |
| **Header Value 2** | `user_token <GLPI_USER_TOKEN>` |

---

### 4. Zabbix API (Custom Credential)

**Path:** Settings → Credentials → Add Credential → Generic Credential

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Name** | `zabbix-api-vsa` |
| **Credential Data** | `{"api_token": "<ZABBIX_API_TOKEN>"}` |

---

### 5. Linear API

**Path:** Settings → Credentials → Add Credential → HTTP Header Auth

**Configuração:**

| Campo | Valor |
|-------|-------|
| **Name** | `linear-api-vsa` |
| **Header Name** | `Authorization` |
| **Header Value** | `Bearer <LINEAR_API_KEY>` |

---

## Verificação e Testes

### 1. Verificar Containers Ativos

```bash
# Listar containers
docker ps

# Output esperado:
# CONTAINER ID   IMAGE              STATUS         PORTS                    NAMES
# abc123def456   n8nio/n8n:latest   Up 2 minutes   0.0.0.0:5678->5678/tcp  deepcode_vsa_n8n
# def456ghi789   pgvector/pgvector  Up 5 minutes   0.0.0.0:5433->5432/tcp  ai_agent_postgres
```

### 2. Verificar Database n8n

```bash
# Conectar ao PostgreSQL
docker exec -it ai_agent_postgres psql -U postgres -d n8n

# Listar tabelas n8n
\dt

# Output esperado (após primeiro boot):
#  public | credentials_entity        | table | postgres
#  public | execution_entity          | table | postgres
#  public | workflow_entity           | table | postgres
```

### 3. Teste de Workflow Simples

**Criar workflow no n8n UI:**

1. **New Workflow**
2. Adicionar node **"Manual Trigger"**
3. Adicionar node **"HTTP Request"**
   - Method: GET
   - URL: `http://backend:8000/health`
4. Conectar nodes
5. **Execute Workflow**

**Output esperado:**

```json
{
  "status": "healthy",
  "checks": {
    "openrouter_api_key": true,
    "database": true
  }
}
```

---

## Troubleshooting

### 1. n8n não inicia

**Sintoma:** Container reinicia constantemente

**Diagnóstico:**

```bash
docker compose -f docker-compose.n8n.yml logs n8n
```

**Causas comuns:**

| Erro | Causa | Solução |
|------|-------|---------|
| `ECONNREFUSED postgres:5432` | PostgreSQL não está pronto | Adicionar `depends_on` com health check |
| `Missing encryption key` | `N8N_ENCRYPTION_KEY` não definida | Gerar chave com `openssl rand -hex 16` |
| `Database n8n does not exist` | Database n8n não criada | Executar `01-create-n8n-schema.sql` |
| `Port 5678 already in use` | Porta ocupada | Alterar `N8N_PORT` no .env.n8n |

---

### 2. Credenciais não funcionam

**Sintoma:** Workflow falha ao chamar GLPI/Zabbix

**Diagnóstico:**

```bash
# Ver execução no n8n UI
# Executions → Últimas 10
# Clicar em execução com erro
# Ver JSON de erro
```

**Causas comuns:**

| Erro | Causa | Solução |
|------|-------|---------|
| `401 Unauthorized (GLPI)` | User Token inválido | Regenerar token no GLPI |
| `Connection timeout (Zabbix)` | URL incorreta | Verificar `ZABBIX_BASE_URL` |
| `Invalid API Key (Linear)` | Chave expirada | Gerar nova chave no Linear |

---

### 3. Workflow não encontra database DeepCode VSA

**Sintoma:** PostgreSQL node retorna "relation kb_chunks does not exist"

**Diagnóstico:**

```bash
# Verificar se tabelas existem
docker exec -it ai_agent_postgres psql -U postgres -d ai_agent_db -c "\dt"
```

**Solução:**

```bash
# Executar migrations do DeepCode VSA
docker exec -it ai_agent_backend python scripts/setup_db.py
```

---

### 4. Performance lenta

**Sintoma:** Workflows demoram > 10s

**Diagnóstico:**

```bash
# Ver uso de recursos
docker stats deepcode_vsa_n8n
```

**Otimizações:**

1. **Aumentar workers:**

   ```yaml
   # docker-compose.n8n.yml
   environment:
     - EXECUTIONS_PROCESS=main
     - N8N_CONCURRENCY_PRODUCTION_LIMIT=10
   ```

2. **Adicionar índices PostgreSQL:**

   ```sql
   CREATE INDEX CONCURRENTLY idx_kb_chunks_empresa ON kb_chunks(empresa);
   ```

3. **Habilitar cache:**

   ```yaml
   environment:
     - N8N_CACHE_ENABLED=true
   ```

---

## Próximos Passos

Após completar este setup:

1. ✅ n8n acessível em `http://localhost:5678`
2. ✅ Credentials configuradas (GLPI, Zabbix, Linear, OpenAI)
3. ✅ PostgreSQL conectado (n8n + DeepCode VSA)
4. ✅ Health check passando

**Seguir para:**

- `n8n-workflows-fase1.md` - Criar workflows de integração
- `n8n-testing.md` - Testar workflows

---

**Data:** 04/02/2026  
**Versão:** 1.0  
**Autor:** DeepCode VSA Team
