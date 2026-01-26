# Configuração do LangSmith

O LangSmith é uma ferramenta de observabilidade para LangChain/LangGraph que permite rastrear e depurar chamadas de agentes.

## 📋 Pré-requisitos

1. **Conta no LangSmith**: Crie uma conta gratuita em [https://smith.langchain.com](https://smith.langchain.com)
2. **API Key**: Obtenha sua API key em [https://smith.langchain.com/settings](https://smith.langchain.com/settings)

## 🔧 Configuração

### 1. Adicione as variáveis de ambiente no `.env`:

```env
# LangSmith
LANGCHAIN_API_KEY=lsv2_pt_...  # Sua API key do LangSmith
LANGCHAIN_TRACING_V2=true      # Habilita o tracing
LANGCHAIN_PROJECT=ai-agent-template  # Nome do projeto (opcional)
```

### 2. Reinicie o backend:

```bash
sudo docker-compose restart backend
```

### 3. Verifique os logs:

```bash
sudo docker-compose logs -f backend
```

Você deve ver:
```
✅ LangSmith tracing enabled
   Project: ai-agent-template
```

## 🎯 Como Usar

1. **Acesse o LangSmith**: [https://smith.langchain.com](https://smith.langchain.com)
2. **Navegue até seu projeto**: Selecione o projeto configurado em `LANGCHAIN_PROJECT`
3. **Veja os traces**: Todas as chamadas do agente serão automaticamente rastreadas

## 🔍 O que é Rastreado

- Chamadas de modelos LLM
- Execução de ferramentas (tools)
- Fluxo do agente (steps)
- Tempos de resposta
- Erros e exceções
- Tokens usados

## ⚠️ Troubleshooting

### LangSmith não está abrindo

1. **Verifique se a API key está configurada**:
   ```bash
   echo $LANGCHAIN_API_KEY
   ```

2. **Verifique os logs do backend**:
   ```bash
   sudo docker-compose logs backend | grep LangSmith
   ```

3. **Teste a API key**:
   ```bash
   curl -H "x-api-key: $LANGCHAIN_API_KEY" https://api.smith.langchain.com/api/v1/projects
   ```

4. **Verifique se o tracing está habilitado**:
   - `LANGCHAIN_TRACING_V2` deve ser `true`
   - `LANGCHAIN_API_KEY` deve estar definida

### Não vejo traces no LangSmith

1. **Aguarde alguns segundos**: Os traces podem levar alguns segundos para aparecer
2. **Verifique o projeto**: Certifique-se de estar visualizando o projeto correto
3. **Faça uma chamada**: Envie uma mensagem pelo frontend para gerar um trace
4. **Verifique os logs**: Os logs devem mostrar "LangSmith tracing enabled"

## 📚 Recursos

- [Documentação do LangSmith](https://docs.smith.langchain.com/)
- [Guia de Início Rápido](https://docs.smith.langchain.com/docs/get-started)
- [API Reference](https://api.smith.langchain.com/docs)

