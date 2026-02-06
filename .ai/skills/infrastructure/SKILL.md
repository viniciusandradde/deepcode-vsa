# Skill: Infraestrutura e Deploy (Proxmox)

## Descrição
Define padrões de infraestrutura, deploy e operações para o ambiente Proxmox Enterprise.

## Contexto
- **Virtualização:** Proxmox VE Enterprise
- **Containers:** Docker + Docker Compose
- **OS:** Ubuntu 24 LTS (VMs)
- **Rede:** Interna hospitalar (segmentada)

## Stack de Infraestrutura

```
Proxmox Enterprise
├── VM: vsa-backend
│   ├── Docker: FastAPI (backend)
│   ├── Docker: Redis
│   └── Docker: n8n
├── VM: vsa-frontend
│   └── Docker: Nginx + React (build)
└── VM: wareline-db (existente - NÃO MODIFICAR)
    └── PostgreSQL 15 (Wareline)
```

## Docker Compose Base

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DB_WARELINE_HOST=${DB_WARELINE_HOST}
      - REDIS_HOST=redis
    depends_on:
      - redis
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
    restart: unless-stopped

volumes:
  redis_data:
  n8n_data:
```

## Regras

1. NUNCA modificar a VM do Wareline
2. Backups automáticos diários via Proxmox
3. Monitoramento de recursos (CPU, RAM, disco)
4. TLS obrigatório para endpoints externos
5. Firewall: apenas portas necessárias abertas

## Anti-Padrões

- ❌ Deploy manual sem docker-compose
- ❌ Dados em volumes efêmeros
- ❌ Expor Redis ou PostgreSQL para internet
- ❌ Rodar containers como root
