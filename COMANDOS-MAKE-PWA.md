# Comandos Make - DeepCode VSA + PWA

**Última atualização:** 28/01/2026

---

## Comandos de Build

### Build Rápido
```bash
make build              # Build backend + frontend
make build-backend      # Build apenas backend  
make build-frontend     # Build apenas frontend
```

### Rebuild (sem cache)
```bash
make rebuild            # Rebuild backend + frontend (sem cache)
make rebuild-all        # Rebuild TODOS os containers (sem cache)
```

---

## Comandos Docker

### Gerenciamento de Containers
```bash
make up                 # Iniciar todos os containers
make down               # Parar todos os containers
make up-build           # Build e iniciar (útil após mudanças)
```

### Status e Logs
```bash
make status             # Ver status de todos os containers
make logs-frontend      # Logs do frontend (últimas 100 linhas)
make logs-backend       # Logs do backend (últimas 100 linhas)
make logs-postgres      # Logs do Postgres (últimas 100 linhas)
```

### Restart Individual
```bash
make restart-frontend   # Reiniciar apenas frontend
make restart-backend    # Reiniciar apenas backend
make restart-postgres   # Reiniciar apenas Postgres
```

---

## Desenvolvimento Local

### Instalação
```bash
make install            # Instalar dependências Python (backend)
make install-frontend   # Instalar dependências frontend (pnpm)
make setup-db           # Configurar banco de dados (SQL schemas)
```

### Executar Localmente
```bash
make dev                # Iniciar backend local (uvicorn)
make frontend           # Iniciar frontend local (pnpm run dev)
make studio             # Iniciar LangGraph Studio
make test               # Executar testes Python
```

---

## Manutenção

### Banco de Dados
```bash
make cleanup-checkpoints         # Limpar checkpoints antigos (180 dias)
make cleanup-checkpoints-dry-run # Simular limpeza (sem deletar)
```

### Health Check
```bash
make health             # Verificar endpoint /health da API
```

---

## Workflow Típico

### Iniciar Ambiente (primeira vez)
```bash
make install            # Deps Python
make install-frontend   # Deps frontend (pnpm)
make setup-db           # Schemas SQL
make up                 # Iniciar containers
```

### Após Mudanças de Código
```bash
# Se alterou código Python ou frontend:
make restart-backend    # ou make restart-frontend

# Se alterou dependências ou Dockerfile:
make rebuild            # Rebuild backend + frontend
make up                 # Reiniciar
```

### Desenvolvimento Diário
```bash
make up                 # Iniciar containers
make logs-frontend      # Ver logs se necessário
make down               # Parar ao final do dia
```

---

## PWA (Progressive Web App)

### Testar PWA Localmente
```bash
cd frontend
pnpm build              # Gera Service Worker (sw.js)
pnpm start              # Roda em production mode
# Acessar: http://localhost:3000
```

### Ativar PWA no Docker

**1. Modificar `docker-compose.yml` (linha 90):**
```yaml
- NODE_ENV=production   # Mudar de development
```

**2. Rebuild e iniciar:**
```bash
make rebuild
make up
```

**3. Validar:**
- Chrome DevTools > Application > Service Workers
- Chrome DevTools > Lighthouse > PWA

---

## Troubleshooting

### Container não inicia
```bash
make logs-frontend      # Ver erro nos logs
make rebuild-all        # Rebuild completo
make up                 # Reiniciar
```

### Mudanças não aparecem
```bash
make restart-frontend   # Reiniciar container
# ou
docker compose restart frontend
```

### Erro de permissão
```bash
# Ajustar owner dos arquivos
sudo chown -R vps:vps frontend/
```

### Port já em uso
```bash
make down               # Parar todos
docker ps               # Ver processos rodando
make up                 # Reiniciar
```

---

## Atalhos Úteis

```bash
# Ver tudo funcionando
make status

# Rebuild rápido
make build-frontend && make restart-frontend

# Rebuild completo
make rebuild-all && make up

# Ver logs em tempo real
docker logs ai_agent_frontend -f
docker logs ai_agent_backend -f
```

---

## Referências

- **Makefile:** `/home/projects/agentes-ai/deepcode-vsa/Makefile`
- **Docker Compose:** `/home/projects/agentes-ai/deepcode-vsa/docker-compose.yml`
- **PWA Guide:** `docs/PWA-GUIDE.md`
- **README:** `README.md`
