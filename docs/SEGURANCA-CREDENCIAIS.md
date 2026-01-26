# Segurança de Credenciais - DeepCode VSA

**⚠️ IMPORTANTE: Este documento contém informações críticas de segurança**

---

## Credenciais Configuradas

O sistema está configurado com credenciais de **produção** do Hospital Evangélico:

### GLPI (ITSM)

- **URL:** <https://glpi.hospitalevangelico.com.br/glpi/apirest.php>
- **App Token:** `gvP15n0MEabjKEhRxzsqX8rp4Z6a27FEmUKv8s4b`
- **Auth Method:** Basic Auth (Username + Password)
- **Status:** ✅ Operacional

### Zabbix (Monitoring)

- **URL:** <https://zabbix.hospitalevangelico.com.br/api_jsonrpc.php>
- **API Token:** `a4419b6574113b0be4062813f54d39aa88b33d07a43f2dadbf0a9b044f4d87b1`

### Linear.app (Project Management)

- **API Key:** `lin_api_VZJYnVszyfCSbmFwWYaPEvC2dCHHtgoDhdDYAE9G`

---

## ⚠️ Regras de Segurança OBRIGATÓRIAS

### 1. Proteção do Arquivo .env

✅ **Verificado:** `.gitignore` está configurado para ignorar `.env`

**NUNCA:**

- ❌ Commitar o arquivo `.env` no Git
- ❌ Compartilhar credenciais em chat/email sem criptografia
- ❌ Fazer upload do `.env` para serviços de nuvem públicos
- ❌ Incluir credenciais em logs ou outputs visíveis

**SEMPRE:**

- ✅ Manter `.env` apenas local
- ✅ Usar `.env.example` como template (sem valores reais)
- ✅ Rotacionar credenciais periodicamente
- ✅ Usar variáveis de ambiente em produção

### 2. Permissões das APIs

#### GLPI

- **READ:** Consultar tickets, SLAs, entidades
- **WRITE:** Criar tickets (DRY_RUN ativo por padrão)
- **DELETE:** ❌ Bloqueado no código

#### Zabbix

- **READ:** Consultar alertas, hosts, métricas
- **WRITE:** ❌ Não implementado (read-only)
- **DELETE:** ❌ Não implementado

#### Linear

- **READ:** Consultar issues, teams, comments
- **WRITE:** Criar issues, adicionar comments (DRY_RUN ativo por padrão)
- **DELETE:** ❌ Não implementado

### 3. Modo Dry-Run (Segurança)

**Padrão do Sistema:** `DRY_RUN=True`

Todas as operações WRITE são **simuladas por padrão**:

```python
# core/config.py
class Settings(BaseSettings):
    dry_run: bool = True  # Safe by default
```

Para executar operações reais:

1. Usuário deve **confirmar explicitamente** no chat
2. Sistema valida a operação
3. Gera preview da ação
4. Solicita confirmação final
5. Executa com `dry_run=False`

### 4. Auditoria

Todas as operações são registradas:

```json
{
  "timestamp": "2026-01-27T10:30:00Z",
  "user": "vsa_agent",
  "operation": "create_ticket",
  "target": "glpi",
  "dry_run": false,
  "data": {...},
  "result": "success",
  "explanation": "Ticket criado após análise GUT"
}
```

### 5. Acesso Restrito

**Quem pode usar o sistema:**

- ✅ Equipe de TI autorizada
- ✅ Gestores de TI
- ✅ NOC/Service Desk

**Controle de acesso:**

- Sistema deve rodar em servidor seguro
- Acesso via VPN/rede interna
- Logs de todas as sessões
- Autenticação de usuários (implementar)

---

## 🔐 Boas Práticas Implementadas

### ✅ No Código

1. **Credenciais via Environment Variables**

   ```python
   from core.config import get_settings
   settings = get_settings()  # Carrega de .env
   ```

2. **Nunca hardcoded**

   ```python
   # ❌ ERRADO
   api_key = "hmj96ml658lz3t3mf0ouxw0dbt0qfdf2ie4j4he8"

   # ✅ CORRETO
   api_key = settings.glpi.app_token
   ```

3. **Dry-Run por Padrão**

   ```python
   async def create_ticket(..., dry_run: bool = True):
       if dry_run:
           return {"preview": data, "dry_run": True}
       # Executa apenas se dry_run=False
   ```

4. **Logs Sanitizados**

   ```python
   logger.info(f"GLPI token: {token[:10]}...")  # Não loga token completo
   ```

### ✅ Na Infraestrutura

1. **Servidor Seguro**
   - Deploy em servidor interno/VPN
   - Firewall configurado
   - SSL/TLS habilitado

2. **Backup de Credenciais**
   - Vault/Secret Manager (recomendado)
   - Backup criptografado do `.env`
   - Acesso controlado

3. **Rotação de Credenciais**
   - GLPI: Gerar novo App Token a cada 90 dias
   - Zabbix: Rotacionar API token a cada 90 dias
   - Linear: Rotacionar API key a cada 90 dias

---

## 🚨 Procedimento em Caso de Vazamento

Se qualquer credencial for comprometida:

### Ação Imediata (< 15 minutos)

1. **GLPI:**

   ```
   1. Acesse: https://glpi.hospitalevangelico.com.br
   2. Setup → API → Tokens
   3. Revogue o token: hmj96ml658lz3t3mf0ouxw0dbt0qfdf2ie4j4he8
   4. Gere novo token
   5. Atualize .env
   ```

2. **Zabbix:**

   ```
   1. Acesse: https://zabbix.hospitalevangelico.com.br
   2. Administration → API tokens
   3. Revogue o token: a4419b6574113b0be4062813f54d39aa...
   4. Gere novo token
   5. Atualize .env
   ```

3. **Linear:**

   ```
   1. Acesse: https://linear.app/settings/api
   2. Revoque a key: lin_api_VZJYnVszyfCSbmFwWYaPEvC2dCHHtgoDhdDYAE9G
   3. Gere nova key
   4. Atualize .env
   ```

### Investigação (< 1 hora)

1. Revisar logs de acesso
2. Identificar operações suspeitas
3. Verificar dados criados/modificados
4. Documentar incidente

### Pós-Incidente

1. Atualizar procedimentos de segurança
2. Revisar permissões de acesso
3. Implementar controles adicionais
4. Treinar equipe

---

## ✅ Checklist de Segurança

### Antes de Deploy

- [ ] Arquivo `.env` não está no Git
- [ ] `.gitignore` contém `.env`
- [ ] Credenciais estão corretas
- [ ] Dry-run está habilitado por padrão
- [ ] Logs não expõem credenciais completas
- [ ] Servidor tem firewall configurado
- [ ] SSL/TLS está habilitado
- [ ] Acesso via VPN/rede interna

### Operação Regular

- [ ] Revisar logs semanalmente
- [ ] Auditar operações mensalmente
- [ ] Rotacionar credenciais trimestralmente
- [ ] Testar procedimento de incidente semestralmente
- [ ] Atualizar documentação quando necessário

### Desenvolvimento

- [ ] Nunca commitar `.env`
- [ ] Usar `.env.example` para novos devs
- [ ] Testar sempre com dry_run primeiro
- [ ] Validar permissões antes de WRITE
- [ ] Documentar todas as mudanças de API

---

## 📝 User Token GLPI (Pendente)

**Atenção:** O sistema GLPI requer um `GLPI_USER_TOKEN` para algumas operações.

### Como Obter

1. Acesse GLPI como usuário específico
2. Vá em: Meu Perfil → Configurações Remotas → Tokens de API
3. Gere um novo token
4. Adicione ao `.env`:

   ```bash
   GLPI_USER_TOKEN=seu_token_de_usuario_aqui
   ```

### Diferença App Token vs User Token

- **App Token:** Identifica a aplicação (VSA)
- **User Token:** Identifica o usuário específico
- Ambos são necessários para operações completas

---

## 📞 Contatos

**Em caso de dúvidas ou incidentes de segurança:**

- **TI Hospital Evangélico:** [contato da TI]
- **Responsável Segurança:** [responsável]
- **Emergência:** [telefone/email]

---

## 📚 Referências

- [GLPI API Documentation](https://glpi-project.org/documentation/)
- [Zabbix API Documentation](https://www.zabbix.com/documentation/current/manual/api)
- [Linear API Documentation](https://developers.linear.app/docs)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

---

**Documento criado:** Janeiro 2026
**Responsável:** Equipe DeepCode VSA
**Próxima revisão:** Abril 2026

---

⚠️ **ESTE DOCUMENTO É CONFIDENCIAL - NÃO COMPARTILHAR FORA DA EQUIPE AUTORIZADA**
