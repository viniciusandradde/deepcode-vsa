# Skill: Wareline API (FastAPI Backend)

## Descrição
Define padrões para a camada de API REST que expõe dados do Wareline para agentes, dashboard e integrações.

## Contexto
- **Framework:** FastAPI
- **Docs:** Scalar (substituindo Swagger padrão)
- **Auth:** JWT + RBAC
- **Versão API:** v1

## Estrutura de Routers

```
/api/v1/
├── /auth/           → login, refresh, me
├── /internacoes/    → listar, buscar, indicadores
├── /agendamentos/   → listar, criar (via agente), cancelar
├── /faturamento/    → resumo, glosas, por convênio
├── /leitos/         → ocupação, disponibilidade, mapa
├── /pacientes/      → buscar (mascarado), histórico
├── /indicadores/    → KPIs C1-C20, por período
├── /agents/         → webhook handler para cada agente
│   ├── /atendimento
│   ├── /agendamentos
│   ├── /exames
│   ├── /tesouraria
│   ├── /orcamentos
│   ├── /rh
│   ├── /ouvidoria
│   └── /informacoes
├── /reports/        → relatórios consolidados
└── /health          → healthcheck
```

## Padrão de Router

```python
# api/v1/internacoes.py
from fastapi import APIRouter, Depends, Query
from ..services.internacao_service import InternacaoService
from ..core.auth import require_role

router = APIRouter(prefix="/internacoes", tags=["Internações"])

@router.get("/ativas")
async def get_internacoes_ativas(
    setor: str = Query(None, description="Filtrar por setor"),
    service: InternacaoService = Depends(),
    _: dict = Depends(require_role(["gestor", "enfermagem", "medico"]))
):
    """Lista internações ativas com dados mascarados (LGPD)."""
    return await service.get_ativas(setor=setor)
```

## Padrão de Service

```python
# services/internacao_service.py
from ..core.cache import cached

class InternacaoService:
    def __init__(self, repo: InternacaoRepository, redis):
        self.repo = repo
        self.redis = redis
    
    @cached(category="realtime", key_prefix="internacoes:ativas")
    async def get_ativas(self, setor: str = None):
        return await self.repo.get_internacoes_ativas(setor=setor)
```

## RBAC - Perfis de Acesso

| Perfil | Acesso |
|--------|--------|
| admin | Tudo |
| gestor | Indicadores, relatórios, ocupação |
| medico | Pacientes (próprios), agendamentos, leitos |
| enfermagem | Leitos, internações, agendamentos |
| financeiro | Faturamento, glosas, convênios |
| atendimento | Agendamentos, informações paciente (mascarado) |
| rh | Dados de RH apenas |

## Anti-Padrões

- ❌ Endpoint sem autenticação
- ❌ Retornar dados sensíveis sem mascaramento
- ❌ Query sem paginação (usar limit/offset)
- ❌ Lógica de negócio no router (mover para service)
- ❌ Acessar banco diretamente no router (usar repository)
