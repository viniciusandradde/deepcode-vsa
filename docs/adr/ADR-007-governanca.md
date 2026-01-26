# ADR-007: Execução Segura (Governança)

## Status

**Aprovado** - Janeiro 2026

## Contexto

O DeepCode VSA interagirá com sistemas críticos de TI (ITSM, monitoramento, infraestrutura). Operações mal executadas podem causar:
- Criação de tickets indevidos
- Alterações em configurações
- Perda de dados
- Interrupção de serviços

É essencial estabelecer um modelo de governança que:
- Proteja contra ações destrutivas
- Permita auditoria completa
- Mantenha confiança do gestor
- Seja transparente e explicável

## Decisão

Adotar modelo de permissões baseado em tipo de operação:

| Operação | Comportamento | Requisitos |
|----------|---------------|------------|
| **READ** | Automático | Credenciais válidas |
| **WRITE** | Confirmação explícita | Dry-run + Aprovação do usuário |
| **DELETE** | Bloqueado (v1) | Não disponível |

## Justificativa

### Princípio do Menor Privilégio

O agente deve ter apenas as permissões necessárias para sua função principal: **análise e recomendação**.

```
                    Pirâmide de Risco

                         ╱╲
                        ╱  ╲
                       ╱ ❌ ╲     DELETE - Bloqueado
                      ╱──────╲
                     ╱   ⚠️   ╲    WRITE - Controlado
                    ╱──────────╲
                   ╱     ✅     ╲   READ - Automático
                  ╱──────────────╲
```

### Fluxo de Operações WRITE

```
┌──────────────────────────────────────────────────────────────┐
│                    Fluxo de Escrita Segura                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Agente identifica necessidade de WRITE                   │
│                     │                                        │
│                     ▼                                        │
│  2. Executa em modo DRY-RUN                                  │
│     └── Simula operação sem efeitos                         │
│                     │                                        │
│                     ▼                                        │
│  3. Apresenta preview ao usuário                             │
│     ┌─────────────────────────────────────────────┐         │
│     │ 📝 Ação proposta:                           │         │
│     │    Criar ticket no GLPI                     │         │
│     │                                             │         │
│     │ Dados:                                      │         │
│     │   - Título: "Servidor web01 - CPU alta"    │         │
│     │   - Prioridade: Alta                        │         │
│     │   - Categoria: Infraestrutura               │         │
│     │                                             │         │
│     │ Confirmar? [s/N]                            │         │
│     └─────────────────────────────────────────────┘         │
│                     │                                        │
│           ┌─────────┴─────────┐                             │
│           │                   │                             │
│           ▼                   ▼                             │
│     Confirmado (s)       Cancelado (N)                      │
│           │                   │                             │
│           ▼                   ▼                             │
│  4. Executa operação    Operação abortada                   │
│           │                   │                             │
│           ▼                   ▼                             │
│  5. Registra em log     Registra tentativa                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Implementação

### Decorator para Governança

```python
from enum import Enum
from functools import wraps

class OperationType(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

def governed_operation(operation_type: OperationType):
    """Decorator que aplica regras de governança."""

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, dry_run: bool = True, **kwargs):
            # DELETE sempre bloqueado
            if operation_type == OperationType.DELETE:
                raise PermissionError(
                    "Operações DELETE não são permitidas na v1"
                )

            # READ executa direto
            if operation_type == OperationType.READ:
                return await func(self, *args, **kwargs)

            # WRITE requer dry-run primeiro
            if operation_type == OperationType.WRITE:
                if dry_run:
                    # Retorna preview sem executar
                    return await self._preview_operation(
                        func.__name__, *args, **kwargs
                    )
                else:
                    # Executa com log
                    result = await func(self, *args, **kwargs)
                    await self._audit_log(
                        operation=func.__name__,
                        args=args,
                        kwargs=kwargs,
                        result=result
                    )
                    return result

        return wrapper
    return decorator
```

### Uso nas Ferramentas

```python
class GLPITool(APITool):

    @governed_operation(OperationType.READ)
    async def get_tickets(self, filters: dict) -> ToolResult:
        """Busca tickets - execução automática."""
        ...

    @governed_operation(OperationType.WRITE)
    async def create_ticket(self, data: dict) -> ToolResult:
        """Cria ticket - requer confirmação."""
        ...
```

## Formato de Auditoria

```json
{
  "id": "audit-20260122-001",
  "timestamp": "2026-01-22T10:30:00Z",
  "session_id": "sess-abc123",
  "user": "admin",
  "operation": {
    "type": "write",
    "tool": "glpi",
    "method": "create_ticket",
    "target": "glpi.ticket"
  },
  "input": {
    "title": "Servidor web01 - CPU alta",
    "priority": 3,
    "category": "infrastructure"
  },
  "dry_run": false,
  "confirmed_by": "admin",
  "confirmed_at": "2026-01-22T10:30:05Z",
  "result": {
    "success": true,
    "ticket_id": 12345
  },
  "explanation": "Ticket criado automaticamente baseado em correlação de alertas Zabbix com tendência de degradação."
}
```

## Consequências

### Positivas

- **Segurança operacional**: Sem ações destrutivas acidentais
- **Confiança do gestor**: Controle total sobre mudanças
- **Auditoria completa**: Rastreabilidade de todas as ações
- **Explicabilidade**: Justificativa documentada
- **Reversibilidade**: Dry-run permite validação prévia

### Negativas

- Fricção para operações de escrita legítimas
- Não é possível automação completa (by design)
- Necessidade de interação humana para WRITE

## Configurações Futuras (v2+)

```yaml
# Possível relaxamento para usuários avançados
governance:
  write_policy:
    require_confirmation: true  # Pode ser false para power users
    auto_approve_low_risk: false  # Auto-aprovar operações de baixo risco
    allowed_auto_writes:
      - "glpi.add_comment"  # Comentários são baixo risco
      - "glpi.update_status"  # Status updates são baixo risco
```

## Alternativas Consideradas

### Sem Governança (Tudo Automático)
Rejeitado por risco operacional inaceitável.

### Tudo Manual (Incluindo READ)
Rejeitado por tornar o agente inútil para análise.

### RBAC Complexo
Considerado para v2, mas over-engineering para MVP.

## Referências

- [OWASP - Principle of Least Privilege](https://owasp.org/www-community/Access_Control)
- [Audit Logging Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
