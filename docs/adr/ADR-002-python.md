# ADR-002: Linguagem - Python

## Status

**Aprovado** - Janeiro 2026

## Contexto

A escolha da linguagem de programação impacta diretamente:
- Ecossistema de bibliotecas disponíveis
- Facilidade de integração com LLMs e frameworks de IA
- Velocidade de desenvolvimento
- Manutenibilidade a longo prazo
- Facilidade de encontrar desenvolvedores

## Decisão

**Python** será a linguagem oficial do DeepCode VSA.

## Justificativa

### Ecossistema de IA/LLM

Python possui o ecossistema mais maduro para IA:

| Biblioteca | Propósito |
|------------|-----------|
| LangChain/LangGraph | Orquestração de agentes |
| OpenAI SDK | Integração com LLMs |
| Pydantic | Validação de dados |
| httpx/aiohttp | Chamadas HTTP assíncronas |

### Ferramentas de CLI

| Biblioteca | Propósito |
|------------|-----------|
| Typer | Framework CLI moderno |
| Rich | Output formatado e colorido |
| Click | Alternativa robusta |

### Comparativo de Linguagens

| Critério | Python | Go | Rust | TypeScript |
|----------|--------|-----|------|------------|
| Ecossistema IA | Excelente | Limitado | Limitado | Bom |
| Velocidade dev | Alta | Média | Baixa | Alta |
| Performance | Boa | Excelente | Excelente | Boa |
| CLI tooling | Excelente | Bom | Bom | Médio |
| Manutenibilidade | Alta | Alta | Média | Alta |

## Consequências

### Positivas

- Acesso ao melhor ecossistema de IA/ML
- Desenvolvimento rápido de MVP
- Facilidade de prototipagem
- Grande pool de desenvolvedores
- Integração nativa com LangGraph

### Negativas

- Performance inferior a linguagens compiladas
- GIL limita paralelismo (mitigado com async)
- Distribuição requer runtime ou empacotamento

## Especificações Técnicas

- **Versão mínima**: Python 3.11+
- **Gerenciador de pacotes**: Poetry ou uv
- **Type hints**: Obrigatórios
- **Linting**: Ruff
- **Formatação**: Black

## Alternativas Consideradas

### Go
Excelente para CLIs e binários únicos, mas ecossistema de IA imaturo.

### Rust
Performance excepcional, mas curva de aprendizado alta e ecossistema de IA limitado.

### TypeScript/Deno
Bom ecossistema, mas menos maduro para IA e automação de infraestrutura.
