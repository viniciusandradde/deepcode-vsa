#!/bin/bash
# Script para testar scheduler em modo produção (sem reload)

echo "🚀 Iniciando backend em modo PRODUÇÃO (sem reload)..."
docker exec -d ai_agent_backend bash -c "pkill -f uvicorn && sleep 2 && cd /app && uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log"

sleep 5

echo "✅ Verificando scheduler..."
docker exec ai_agent_backend python -c "
from core.scheduler import get_scheduler_service
s = get_scheduler_service()
print(f'Scheduler running: {s.scheduler.running}')
print(f'Jobs: {len(s.scheduler.get_jobs())}')
for job in s.scheduler.get_jobs()[:3]:
    print(f'  - {job.name}: {job.next_run_time}')
"

echo ""
echo "📋 Logs recentes:"
docker logs ai_agent_backend --tail=15 | grep -E "(Scheduler|Application)"
