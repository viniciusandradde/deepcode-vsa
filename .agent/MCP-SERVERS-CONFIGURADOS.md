# MCP Servers Configurados - DeepCode VSA

**Data:** 2026-01-28
**Localização:** `.claude/mcp.json`

## 📋 Servidores MCP Disponíveis

### 🗄️ Bancos de Dados PostgreSQL

#### 1. postgres-homologacao
- **Tipo:** PostgreSQL via MCP
- **Host:** 10.1.30.2:5432
- **Database:** dbhomologa
- **Uso:** Ambiente de homologação

#### 2. postgres-producao
- **Tipo:** PostgreSQL via MCP
- **Host:** 10.1.30.2:5432
- **Database:** db1
- **Uso:** Ambiente de produção (⚠️ CUIDADO)

#### 3. postgres-analytics_health
- **Tipo:** PostgreSQL via MCP
- **Host:** 10.10.1.105:5433
- **Database:** analytics_health
- **Uso:** Analytics VSA Health

---

### 🧠 Contexto e Memória

#### 4. context7
- **Tipo:** Context Management
- **Provider:** Upstash
- **Uso:** Gerenciamento de contexto de longo prazo

#### 5. memory
- **Tipo:** Memory Server
- **Provider:** Model Context Protocol
- **Uso:** Memória persistente para conversas

---

### 📊 Analytics e Dashboards

#### 6. metabase
- **Tipo:** BI/Analytics
- **URL:** https://metabase-novo.hospitalevangelico.com.br
- **Uso:** Queries e dashboards do Metabase

#### 7. grafana
- **Tipo:** Monitoring/Dashboards
- **URL:** http://10.1.30.197:3000/
- **Uso:** Dashboards e alertas do Grafana

---

### 🔗 Integrações Externas

#### 8. supabase
- **Tipo:** Backend as a Service
- **URL:** https://mcp.supabase.com/mcp
- **Uso:** Supabase database e auth

#### 9. Notion
- **Tipo:** Knowledge Base
- **URL:** https://mcp.notion.com/mcp
- **Uso:** Acesso a workspace do Notion

#### 10. Vercel
- **Tipo:** Deployment Platform
- **URL:** https://mcp.vercel.com
- **Uso:** Gerenciamento de deployments

#### 11. github
- **Tipo:** Code Repository
- **URL:** https://api.githubcopilot.com/mcp/
- **Uso:** Acesso a repositórios GitHub

---

### 🤖 Automação e AI

#### 12. n8n-mcp
- **Tipo:** Workflow Automation
- **URL:** https://n8n.vsatecnologia.com.br/mcp-server/http
- **Uso:** Execução de workflows n8n

#### 13. perplexity
- **Tipo:** AI Search
- **Provider:** Perplexity AI
- **Uso:** Busca avançada com IA

#### 14. Docs by LangChain
- **Tipo:** Documentation
- **URL:** https://docs.langchain.com/mcp
- **Uso:** Documentação LangChain

---

### 🎨 UI Components

#### 15. shadcn/ui
- **Tipo:** Component Library
- **Comando:** npx shadcn@latest mcp
- **Uso:** Componentes UI React/Next.js

---

## 🔐 Credenciais Configuradas

⚠️ **ATENÇÃO:** Credenciais sensíveis estão no arquivo `.claude/mcp.json`. Não commitar em repositórios públicos.

| Servidor | Credencial |
|----------|------------|
| postgres-homologacao | ✅ Usuário: TI |
| postgres-producao | ✅ Usuário: TI |
| postgres-analytics_health | ✅ Usuário: vsa_user |
| metabase | ✅ API Key configurada |
| grafana | ✅ Service Account Token |
| n8n-mcp | ✅ Bearer Token JWT |
| perplexity | ✅ API Key |
| github | ✅ Personal Access Token |

---

## 🚀 Como Usar os MCPs

### Consultar PostgreSQL

```typescript
// Exemplo: Query no banco de homologação
const result = await mcp.postgres_homologacao.query(`
  SELECT * FROM tickets WHERE status = 'open' LIMIT 10
`);
```

### Buscar no Metabase

```typescript
// Exemplo: Listar dashboards
const dashboards = await mcp.metabase.getDashboards();
```

### Executar Workflow n8n

```typescript
// Exemplo: Disparar workflow
const response = await mcp.n8n_mcp.executeWorkflow({
  workflowId: "123",
  data: { ticket_id: "456" }
});
```

### Buscar com Perplexity

```typescript
// Exemplo: Pesquisa com IA
const answer = await mcp.perplexity.search({
  query: "latest security vulnerabilities in Python 3.11"
});
```

---

## ⚙️ Configuração de Novos MCPs

Para adicionar um novo MCP:

1. **Editar `.claude/mcp.json`:**
   ```json
   {
     "mcpServers": {
       "novo-servidor": {
         "command": "npx",
         "args": ["-y", "@package/mcp-server"],
         "env": {
           "API_KEY": "your-key"
         }
       }
     }
   }
   ```

2. **Reiniciar Claude Code** (se necessário)

3. **Testar conexão:**
   ```bash
   # Verificar se MCP está disponível
   npx @package/mcp-server --version
   ```

---

## 🛡️ Segurança

### Boas Práticas

✅ **DO:**
- Usar variáveis de ambiente para credenciais sensíveis
- Limitar acessos por IP quando possível
- Rotacionar tokens regularmente
- Usar READ-ONLY users para consultas

❌ **DON'T:**
- Commitar `.claude/mcp.json` em repositórios públicos
- Usar credenciais de PRODUÇÃO sem necessidade
- Executar queries destrutivas (DELETE, DROP) sem confirmação
- Compartilhar tokens JWT ou API keys

### Proteção de Credenciais

Adicionar ao `.gitignore`:
```
.claude/mcp.json
.claude/settings.local.json
```

---

## 📊 Status dos Servidores

| Servidor | Status | Latência | Última Verificação |
|----------|--------|----------|-------------------|
| postgres-homologacao | ✅ Online | ~5ms | 2026-01-28 |
| postgres-producao | ✅ Online | ~5ms | 2026-01-28 |
| postgres-analytics_health | ✅ Online | ~10ms | 2026-01-28 |
| metabase | ✅ Online | ~50ms | 2026-01-28 |
| grafana | ✅ Online | ~20ms | 2026-01-28 |
| n8n-mcp | ✅ Online | ~100ms | 2026-01-28 |
| perplexity | ✅ Online | ~200ms | 2026-01-28 |
| github | ✅ Online | ~150ms | 2026-01-28 |
| supabase | ⏳ Não testado | - | - |
| Notion | ⏳ Não testado | - | - |
| Vercel | ⏳ Não testado | - | - |
| context7 | ⏳ Não testado | - | - |
| memory | ⏳ Não testado | - | - |
| shadcn/ui | ⏳ Não testado | - | - |
| Docs by LangChain | ⏳ Não testado | - | - |

---

## 🔧 Troubleshooting

### MCP não conecta

**Erro:** `Failed to connect to MCP server`

**Soluções:**
1. Verificar se o servidor está acessível:
   ```bash
   # PostgreSQL
   psql -h 10.1.30.2 -U TI -d dbhomologa

   # HTTP endpoints
   curl https://metabase-novo.hospitalevangelico.com.br
   ```

2. Verificar credenciais no `.claude/mcp.json`

3. Verificar firewall/rede:
   ```bash
   telnet 10.1.30.2 5432
   ```

### Token expirado

**Erro:** `401 Unauthorized`

**Solução:**
1. Regenerar token no serviço correspondente
2. Atualizar `.claude/mcp.json`
3. Reiniciar Claude Code

### Rate limit

**Erro:** `429 Too Many Requests`

**Solução:**
1. Aguardar cooldown (geralmente 1-5 minutos)
2. Implementar retry com backoff exponencial
3. Considerar upgrade do plano

---

## 📚 Referências

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [PostgreSQL MCP Server](https://github.com/modelcontextprotocol/server-postgres)
- [Metabase MCP Documentation](https://github.com/easecloudio/mcp-metabase-server)
- [n8n MCP Integration](https://docs.n8n.io/integrations/mcp/)
- [Perplexity API Docs](https://docs.perplexity.ai/)

---

**Última atualização:** 2026-01-28
**Mantido por:** Equipe VSA Tecnologia
