# ADR-006: API Tool Registry Dinâmico

## Status

**Aprovado** - Janeiro 2026

## Contexto

Com a arquitetura API-First (ADR-005), o DeepCode VSA precisa gerenciar múltiplas integrações de forma:
- Consistente (interface padrão)
- Dinâmica (adicionar/remover sem restart)
- Escalável (dezenas de integrações)
- Descobrível (agente sabe quais ferramentas tem)

## Decisão

Todas as APIs seguirão um **contrato padrão** e serão **registradas dinamicamente** em um Tool Registry central.

## Justificativa

### Benefícios do Registry Dinâmico

| Benefício | Descrição |
|-----------|-----------|
| Plug-and-play | Novas integrações sem alterar código core |
| Padronização | Todas as tools seguem mesma interface |
| Descoberta | Agente consulta ferramentas disponíveis |
| Configurável | Habilitar/desabilitar por ambiente |
| Testável | Mock fácil de integrações |

### Contrato Padrão

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class Operation(BaseModel):
    """Descreve uma operação disponível."""
    name: str
    description: str
    method: str  # GET, POST, PUT, DELETE
    requires_confirmation: bool = False

class ToolResult(BaseModel):
    """Resultado padronizado de operações."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    metadata: dict = {}

class APITool(ABC):
    """Contrato base para todas as ferramentas de API."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome único da ferramenta."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição para o LLM entender quando usar."""
        pass

    @property
    @abstractmethod
    def operations(self) -> List[Operation]:
        """Lista de operações disponíveis."""
        pass

    @abstractmethod
    async def read(self, operation: str, params: dict) -> ToolResult:
        """Executa operação de leitura."""
        pass

    @abstractmethod
    async def write(
        self,
        operation: str,
        data: dict,
        dry_run: bool = True
    ) -> ToolResult:
        """Executa operação de escrita."""
        pass
```

## Arquitetura do Registry

```
┌─────────────────────────────────────────────────────────────┐
│                     Tool Registry                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  register(tool: APITool)      Registra nova ferramenta     │
│  unregister(name: str)        Remove ferramenta            │
│  get(name: str) -> APITool    Obtém ferramenta por nome    │
│  list() -> List[APITool]      Lista todas as ferramentas   │
│  get_for_llm() -> List[dict]  Formato para function calling │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Registered Tools                        │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ "glpi" → GLPITool(config)                    │  │   │
│  │  │ "zabbix" → ZabbixTool(config)                │  │   │
│  │  │ "proxmox" → ProxmoxTool(config)              │  │   │
│  │  │ ...                                          │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Implementação de Exemplo

```python
class ToolRegistry:
    """Registro central de ferramentas de API."""

    def __init__(self):
        self._tools: dict[str, APITool] = {}

    def register(self, tool: APITool) -> None:
        """Registra uma ferramenta."""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> APITool:
        """Obtém ferramenta por nome."""
        if name not in self._tools:
            raise KeyError(f"Tool {name} not found")
        return self._tools[name]

    def list_tools(self) -> list[APITool]:
        """Lista todas as ferramentas registradas."""
        return list(self._tools.values())

    def get_tools_for_llm(self) -> list[dict]:
        """Retorna ferramentas em formato para function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_schema()
                }
            }
            for tool in self._tools.values()
        ]

# Uso
registry = ToolRegistry()

# Registro dinâmico baseado em config
if config.glpi_enabled:
    registry.register(GLPITool(config.glpi))

if config.zabbix_enabled:
    registry.register(ZabbixTool(config.zabbix))
```

## Consequências

### Positivas

- **Desacoplamento**: Core não conhece implementações específicas
- **Extensibilidade**: Nova API = nova classe + registro
- **Descoberta**: LLM sabe dinamicamente o que pode fazer
- **Testabilidade**: Mock registry para testes
- **Configurabilidade**: Enable/disable por ambiente

### Negativas

- Indireção adicional (registry lookup)
- Necessidade de manter contrato consistente
- Validação de contratos em runtime

## Configuração por Ambiente

```yaml
# config.yaml
integrations:
  glpi:
    enabled: true
    base_url: "https://glpi.empresa.com/apirest.php"
    app_token: "${GLPI_APP_TOKEN}"
    user_token: "${GLPI_USER_TOKEN}"

  zabbix:
    enabled: true
    base_url: "https://zabbix.empresa.com/api_jsonrpc.php"
    api_token: "${ZABBIX_API_TOKEN}"

  proxmox:
    enabled: false  # Desabilitado neste ambiente
```

## Alternativas Consideradas

### Hardcoded Tools
Rejeitado por falta de flexibilidade e dificuldade de manutenção.

### Plugin System (Entry Points)
Considerado para v2, mas over-engineering para MVP.

### Dependency Injection Container
Complexidade adicional sem benefício claro para este caso.

## Referências

- [Registry Pattern](https://martinfowler.com/eaaCatalog/registry.html)
- [Plugin Architecture](https://python-patterns.guide/gang-of-four/registry/)
