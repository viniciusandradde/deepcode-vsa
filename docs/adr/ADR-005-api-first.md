# ADR-005: Arquitetura API-First

## Status

**Aprovado** - Janeiro 2026

## Contexto

O DeepCode VSA precisa se integrar com múltiplos sistemas de TI:
- GLPI (ITSM)
- Zabbix (Monitoramento)
- Proxmox (Virtualização)
- Cloud providers (AWS, Azure, GCP)
- ERPs diversos

Duas abordagens principais foram consideradas:
1. **MCP (Model Context Protocol)**: Protocolo intermediário da Anthropic
2. **API-First**: Conexão direta às APIs nativas

## Decisão

O DeepCode VSA será **API-First**, conectando-se diretamente às APIs disponíveis, **sem MCP**.

## Justificativa

### Comparativo MCP vs API-First

| Critério | MCP | API-First |
|----------|-----|-----------|
| Escalabilidade | Limitada por servidores MCP | Ilimitada |
| Overhead | Alto (camada intermediária) | Baixo (direto) |
| Flexibilidade | Depende de MCP disponível | Total |
| Personalização | Limitada | Total por cliente |
| Manutenção | Dependente de terceiros | Interna |
| Latência | Maior (hop adicional) | Menor |

### Por que API-First?

1. **Escala para Dezenas de Sistemas**
   - Não depende de MCP existente para cada sistema
   - Qualquer sistema com REST/GraphQL API pode ser integrado
   - MSPs podem ter 50+ clientes com sistemas diferentes

2. **Menor Overhead**
   - Chamada direta à API do sistema
   - Sem serialização/desserialização adicional
   - Sem servidor intermediário para manter

3. **Maior Flexibilidade por Cliente**
   - Cada cliente pode ter configurações específicas
   - Endpoints customizados são suportados
   - Não há limitação pelo escopo do MCP

4. **Fácil Adicionar/Remover Integrações**
   - Nova API = novo arquivo de configuração
   - Remoção não afeta outras integrações
   - Hot-reload de configurações

## Arquitetura API-First

```
┌─────────────────────────────────────────────────────────────┐
│                      DeepCode VSA                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API Tool Registry                       │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  Tool Contract (Interface Padrão)            │   │   │
│  │  │  - name, description                         │   │   │
│  │  │  - read(), write()                           │   │   │
│  │  │  - auth_config                               │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  ┌──────┐ ┌──────┐ ┌─────────┐ ┌──────┐          │   │
│  │  │ GLPI │ │Zabbix│ │ Proxmox │ │ AWS  │  ...     │   │
│  │  │ Tool │ │ Tool │ │  Tool   │ │ Tool │          │   │
│  │  └──┬───┘ └──┬───┘ └────┬────┘ └──┬───┘          │   │
│  └─────┼────────┼──────────┼─────────┼───────────────┘   │
│        │        │          │         │                    │
└────────┼────────┼──────────┼─────────┼────────────────────┘
         │        │          │         │
         ▼        ▼          ▼         ▼
    ┌────────┐ ┌──────┐ ┌─────────┐ ┌──────┐
    │GLPI API│ │Zabbix│ │ Proxmox │ │ AWS  │
    │        │ │ API  │ │   API   │ │ API  │
    └────────┘ └──────┘ └─────────┘ └──────┘
```

## Consequências

### Positivas

- **Mais simples**: Sem camada intermediária
- **Mais escalável**: Sem limite de integrações
- **Mais vendável**: Demonstra flexibilidade ao cliente
- **Menor custo**: Sem infraestrutura MCP
- **Maior controle**: Implementação interna

### Negativas

- Mais código de integração por API
- Necessidade de manter compatibilidade com versões de API
- Responsabilidade de autenticação por sistema

## Mitigação das Desvantagens

| Desvantagem | Mitigação |
|-------------|-----------|
| Código por API | Template/SDK interno padronizado |
| Compatibilidade | Versionamento de integrações |
| Autenticação | Abstração comum de auth |

## Estrutura de Diretórios

```
deepcode_vsa/
├── integrations/
│   ├── base.py          # Classe base para todas as integrações
│   ├── registry.py      # Registro dinâmico de APIs
│   ├── glpi/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── tools.py
│   ├── zabbix/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── tools.py
│   └── ...
```

## Alternativas Consideradas

### MCP (Model Context Protocol)
Rejeitado por:
- Dependência de servidores MCP disponíveis
- Overhead de manutenção
- Limitação de funcionalidades ao que o MCP expõe

### Abstração Genérica Universal
Rejeitado por ser over-engineering para v1.

## Referências

- [API-First Design](https://swagger.io/resources/articles/adopting-an-api-first-approach/)
