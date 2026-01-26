# ADR-001: Tipo de Aplicação - CLI Local

## Status

**Aprovado** - Janeiro 2026

## Contexto

O DeepCode VSA precisa de uma interface para interação com os gestores de TI. As opções consideradas incluem:
- Aplicação web
- Aplicação desktop
- CLI (Command Line Interface)
- API sem interface

O público-alvo (gestores de TI, coordenadores de infraestrutura) trabalha predominantemente em ambientes Linux/servidor.

## Decisão

O sistema será uma **CLI local em Linux**.

## Justificativa

| Fator | CLI Local | Web App | Desktop |
|-------|-----------|---------|---------|
| Ambientes de TI/servidores | Ideal | Requer browser | Limitado |
| Segurança | Alta (local) | Exposição de rede | Média |
| Automação/scripts | Nativo | Complexo | Limitado |
| Overhead | Mínimo | Alto | Médio |
| Tempo de desenvolvimento | Baixo | Alto | Alto |

### Razões Principais

1. **Ambientes de Servidores**: Gestores de TI frequentemente trabalham via SSH em servidores Linux
2. **Segurança**: Execução local evita exposição de APIs e credenciais
3. **Automação**: Integração natural com scripts, cron, e pipelines
4. **Baixo Overhead**: Não requer servidor web, banco de dados separado, etc.
5. **Time-to-market**: Desenvolvimento mais rápido para MVP

## Consequências

### Positivas

- Implantação simples (pip install ou binário)
- Integração com ferramentas de automação existentes
- Baixo consumo de recursos
- Funcionamento offline parcial
- Segurança por isolamento

### Negativas

- Curva de aprendizado para usuários não-técnicos
- Sem interface visual para dashboards
- Colaboração limitada (single-user)

## Alternativas Consideradas

### Web Application
Rejeitada por adicionar complexidade desnecessária para v1 e aumentar superfície de ataque.

### Desktop Application (Electron/Qt)
Rejeitada por overhead de desenvolvimento e incompatibilidade com ambientes headless.

### API-only
Rejeitada por não fornecer interface de usuário direta, dificultando adoção inicial.

## Referências

- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46)
- [Typer - FastAPI for CLIs](https://typer.tiangolo.com/)
