# Skill: Database PostgreSQL / Wareline

## Descrição
Define como acessar e consultar o banco de dados PostgreSQL do sistema Wareline (ERP hospitalar). Todo acesso é READ-ONLY.

## Contexto
- **Database:** PostgreSQL 15
- **Sistema:** Wareline (ERP Hospitalar)
- **Acesso:** Read-only via usuário `vsa_reader`
- **Infra:** Proxmox Enterprise
- **Cache:** Redis com TTL adaptativo

## Regras Obrigatórias

1. **NUNCA** executar INSERT, UPDATE, DELETE ou DDL no Wareline
2. **SEMPRE** usar connection pool limitado (max 10 conexões)
3. **SEMPRE** usar queries parametrizadas (nunca concatenar strings)
4. **SEMPRE** aplicar cache Redis antes de consultar o Wareline
5. **NUNCA** logar dados sensíveis de pacientes (CPF, nome completo, dados clínicos)
6. **SEMPRE** adicionar LIMIT em queries que podem retornar muitos resultados
7. **SEMPRE** usar async/await (asyncpg) para não bloquear o event loop

## Stack
- **Driver:** asyncpg (async) + SQLAlchemy 2.0
- **Cache:** Redis (aioredis)
- **Padrão:** Cache-Aside (Application-Level)
- **Pool:** min=2, max=10

## Tabelas Prioritárias do Wareline

| Tabela | Descrição | Módulo |
|--------|-----------|--------|
| `arqatend` | Atendimentos/consultas | Atendimento |
| `arqint` | Internações | Internação |
| `arqpac` | Cadastro de pacientes | Geral |
| `arqfat` | Faturamento | Financeiro |
| `arqconv` | Convênios | Financeiro |
| `arqmed` | Cadastro de médicos | Geral |
| `arqexa` | Exames solicitados | SADT |
| `arqleito` | Controle de leitos | Internação |
| `arqage` | Agendamentos | Agendamento |
| `arqcc` | Centro cirúrgico | Cirurgia |

## Padrão de Connection Pool

```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class WarelineDatabase:
    """Conexão read-only com Wareline PostgreSQL."""
    
    def __init__(self, settings):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{settings.db_wareline_user}:"
            f"{settings.db_wareline_password}@"
            f"{settings.db_wareline_host}:"
            f"{settings.db_wareline_port}/"
            f"{settings.db_wareline_name}",
            pool_size=2,         # Mínimo de conexões
            max_overflow=8,      # Até 10 total
            pool_timeout=30,
            pool_recycle=1800,   # Reciclar a cada 30 min
            pool_pre_ping=True,  # Verificar conexão antes de usar
            echo=False,          # NUNCA True em produção (loga queries)
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session
```

## Padrão de Repository

```python
# repositories/internacao_repository.py
from sqlalchemy import text

class InternacaoRepository:
    """Acesso read-only às internações do Wareline."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_internacoes_ativas(self, limit: int = 100):
        """Busca internações ativas com dados mascarados."""
        query = text("""
            SELECT 
                i.codigo,
                i.data_entrada,
                i.leito,
                i.setor,
                -- Mascarar CPF: mostrar apenas últimos 4 dígitos
                CONCAT('***.***.', RIGHT(p.cpf, 6)) as cpf_masked,
                -- Nome apenas iniciais
                CONCAT(
                    LEFT(p.nome, 1), '***'
                ) as nome_masked,
                c.descricao as convenio
            FROM arqint i
            JOIN arqpac p ON i.paciente_id = p.codigo
            LEFT JOIN arqconv c ON i.convenio_id = c.codigo
            WHERE i.data_saida IS NULL
            ORDER BY i.data_entrada DESC
            LIMIT :limit
        """)
        result = await self.session.execute(query, {"limit": limit})
        return result.mappings().all()
```

## Padrão de Cache

```python
# core/cache.py
import json
import aioredis
from functools import wraps

# TTLs por categoria
CACHE_TTL = {
    "realtime": 60,          # 1 min - ocupação de leitos
    "operational": 300,       # 5 min - agendamentos do dia
    "analytical": 900,        # 15 min - indicadores
    "report": 3600,          # 1 hora - relatórios consolidados
    "static": 86400,         # 24 horas - cadastros
}

def cached(category: str, key_prefix: str):
    """Decorator para cache automático com TTL por categoria."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # Tentar cache primeiro
            cached_value = await self.redis.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
            
            # Cache miss - buscar no Wareline
            result = await func(self, *args, **kwargs)
            
            # Salvar no cache
            ttl = CACHE_TTL.get(category, 300)
            await self.redis.set(
                cache_key, 
                json.dumps(result, default=str), 
                ex=ttl
            )
            return result
        return wrapper
    return decorator
```

## Anti-Padrões (NÃO FAZER)

- ❌ `SELECT * FROM arqpac` sem LIMIT (tabela gigante)
- ❌ Concatenar valores na query: `f"WHERE cpf = '{cpf}'"` (SQL injection)
- ❌ Logar resultado de query com dados de paciente
- ❌ Criar índices ou alterar schema do Wareline
- ❌ Pool com mais de 10 conexões (impacta o Wareline em produção)
- ❌ Queries sem timeout (pode travar conexão do pool)
- ❌ Expor dados completos de paciente via API (LGPD)

## Troubleshooting

| Problema | Causa Provável | Solução |
|----------|---------------|---------|
| Connection timeout | Pool esgotado | Verificar queries lentas, aumentar timeout |
| Query lenta > 5s | Sem índice ou tabela grande | Adicionar WHERE mais restritivo, usar LIMIT |
| Dados desatualizados | TTL muito longo | Ajustar categoria do cache |
| Pool exhausted | Muitas requests simultâneas | Implementar queue/rate limiting |
