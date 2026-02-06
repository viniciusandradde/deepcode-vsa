# Skill: LGPD Compliance para Dados de Saúde

## Descrição
Define regras e padrões obrigatórios de conformidade com a LGPD para tratamento de dados de saúde em todos os módulos do VSA Analytics Health.

## Contexto
- **Lei:** LGPD (Lei 13.709/2018)
- **Categoria:** Dados sensíveis de saúde (Art. 5º, II e Art. 11)
- **Hospitais:** Mackenzie Dourados, Presbiteriano CG, Presbiteriano Rio Verde
- **Sistemas:** Wareline, ZigChat, Redis, FastAPI

## Regras Obrigatórias (TODA IA deve seguir)

### 1. Classificação de Dados

| Tipo | Exemplos | Tratamento |
|------|----------|------------|
| **Identificação** | CPF, RG, nome completo | Mascarar em logs e respostas |
| **Saúde** | Diagnóstico, CID, exames, prontuário | NUNCA expor via WhatsApp |
| **Financeiro** | Valores, convênio, faturamento | Acesso apenas com autorização |
| **Contato** | Telefone, e-mail, endereço | Mascarar em logs |
| **Biométrico** | Imagens, digitais | Não armazenar fora do Wareline |

### 2. Regras de Mascaramento

```python
# utils/lgpd.py

def mask_cpf(cpf: str) -> str:
    """***.***.XXX-XX → mostra apenas últimos 5 chars."""
    if not cpf or len(cpf) < 5:
        return "***"
    clean = cpf.replace(".", "").replace("-", "")
    return f"***.***{clean[-5:-2]}-{clean[-2:]}"

def mask_nome(nome: str) -> str:
    """João da Silva → J*** da S***."""
    parts = nome.split()
    masked = []
    for part in parts:
        if len(part) <= 2:  # preposições
            masked.append(part)
        else:
            masked.append(f"{part[0]}***")
    return " ".join(masked)

def mask_telefone(tel: str) -> str:
    """(67) 99999-1234 → (67) ****-1234."""
    clean = tel.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if len(clean) >= 4:
        return f"****-{clean[-4:]}"
    return "****"

def mask_email(email: str) -> str:
    """joao@hospital.com → j***@hospital.com."""
    parts = email.split("@")
    if len(parts) == 2:
        return f"{parts[0][0]}***@{parts[1]}"
    return "***@***"
```

### 3. Regras por Canal

**WhatsApp (ZigChat):**
- NUNCA enviar: CID, diagnóstico, resultado de exame detalhado, prontuário
- PODE enviar: confirmação de agendamento (sem detalhes clínicos), protocolo, horários
- Para laudos: enviar link seguro com autenticação, não o PDF direto
- Sempre confirmar identidade antes de fornecer informações

**Dashboard (React):**
- Dados agregados em indicadores (não mostrar pacientes individuais)
- Acesso por RBAC (cada perfil vê apenas o que precisa)
- Sessão com timeout de 30 minutos
- Log de acesso a dados sensíveis

**API (FastAPI):**
- Todos os endpoints com autenticação JWT
- Dados de paciente mascarados por padrão
- Flag `include_sensitive=true` apenas com permissão elevada
- Rate limiting para evitar data scraping

**Logs (qualquer sistema):**
- NUNCA logar CPF, nome completo, telefone, dados clínicos
- Usar IDs internos para referência
- Logs de auditoria separados dos logs operacionais

### 4. Consentimento

```python
# Para atendimento WhatsApp
CONSENT_MESSAGE = (
    "Para prosseguir com o atendimento, informamos que seus dados "
    "serão tratados conforme a Lei Geral de Proteção de Dados (LGPD). "
    "Ao continuar, você consente com o tratamento dos seus dados "
    "para fins de atendimento hospitalar. "
    "Para mais informações, acesse nosso portal de privacidade."
)
```

### 5. Direitos do Titular (Art. 18)

O sistema deve suportar:
- Confirmação de existência de tratamento
- Acesso aos dados
- Correção de dados incompletos
- Eliminação de dados (quando aplicável)
- Portabilidade
- Revogação de consentimento

## Anti-Padrões (NÃO FAZER)

- ❌ Logar: `logger.info(f"Paciente {nome} CPF {cpf} consultou")`
- ✅ Logar: `logger.info(f"Paciente ID {id_interno} realizou consulta")`
- ❌ Enviar via WhatsApp: "Seu exame de HIV deu positivo"
- ✅ Enviar via WhatsApp: "Seus resultados estão disponíveis. Acesse: [link seguro]"
- ❌ Cache com dados completos de paciente
- ✅ Cache com dados mascarados ou IDs

## Checklist de Compliance por Feature

- [ ] Dados sensíveis mascarados em logs?
- [ ] Dados sensíveis mascarados em respostas ao paciente?
- [ ] Acesso autenticado e autorizado?
- [ ] Consentimento coletado (se via WhatsApp)?
- [ ] Auditoria de acesso implementada?
- [ ] Dados retidos apenas pelo tempo necessário?
- [ ] Criptografia em trânsito (HTTPS/TLS)?
