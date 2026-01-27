# Classificação ITIL - Português do Brasil

> **Atualizado:** 27/01/2026
> **Versão:** 1.0

Este documento define a nomenclatura padrão ITIL utilizada no DeepCode VSA em Português do Brasil.

---

## 📋 Tipos de Demanda

### 🔥 INCIDENTE

**Definição:** Interrupção inesperada de um serviço de TI ou degradação da qualidade de um serviço.

**Objetivo:** Restaurar o serviço o mais rápido possível.

**Exemplos:**
- Servidor web fora do ar
- Aplicação travando para múltiplos usuários
- Perda de conectividade de rede
- Sistema lento afetando produção

**Plano Típico:**
1. Coleta de Informações
2. Diagnóstico
3. Resolução (correção ou workaround)
4. Documentação

---

### 🔍 PROBLEMA

**Definição:** Causa raiz de um ou mais incidentes. Análise profunda para prevenir recorrência.

**Objetivo:** Identificar e eliminar a causa raiz para evitar futuros incidentes.

**Exemplos:**
- Memory leak recorrente em aplicação
- Backup falhando todas as sextas-feiras
- Padrão de quedas em horário específico
- Degradação progressiva de performance

**Plano Típico:**
1. Coleta de Dados (incidentes relacionados)
2. Análise RCA (5 Porquês)
3. Ação Corretiva
4. Documentação

---

### 🔄 MUDANÇA

**Definição:** Adição, modificação ou remoção de algo que possa ter um efeito direto ou indireto nos serviços de TI.

**Objetivo:** Garantir que mudanças sejam implementadas de forma controlada com mínimo impacto.

**Exemplos:**
- Atualização de sistema operacional
- Migração de servidor
- Deploy de nova versão de aplicação
- Alteração de configuração de firewall

**Plano Típico:**
1. Avaliação de Impacto
2. Planejamento (janela de manutenção)
3. Validação de pré-requisitos
4. Documentação

---

### 📋 REQUISIÇÃO

**Definição:** Solicitação de um usuário para obter informações, aconselhamento, serviço padrão ou acesso a um serviço.

**Objetivo:** Atender à solicitação de forma rápida e eficiente.

**Exemplos:**
- Solicitação de acesso a sistema
- Pedido de instalação de software
- Requisição de nova impressora
- Alteração de senha

**Plano Típico:**
1. Validação (requisitos e aprovações)
2. Execução
3. Verificação
4. Documentação

---

### 💬 CONVERSA

**Definição:** Interação em tempo real, geralmente para suporte rápido ou coleta de informações iniciais.

**Objetivo:** Responder dúvidas, orientar, ou coletar informações para abertura de ticket formal.

**Exemplos:**
- "Como funciona o processo de backup?"
- "Qual o horário da manutenção programada?"
- "Preciso de ajuda com uma consulta SQL"
- Chat geral sem demanda técnica específica

**Plano Típico:**
1. Entendimento da necessidade
2. Resposta ou orientação
3. Encaminhamento (se necessário)

---

## 🏷️ Categorias

### Infraestrutura
Problemas ou solicitações relacionadas a servidores, armazenamento, virtualização, datacenter.

**Exemplos:** Servidor offline, disco cheio, VM não iniciando, storage lento

### Rede
Problemas de conectividade, desempenho de rede, configuração de dispositivos de rede.

**Exemplos:** Lentidão na rede, VPN não conecta, switch travado, DNS não resolvendo

### Software
Problemas com aplicativos, sistemas operacionais, licenças, integrações.

**Exemplos:** Aplicação travando, erro ao salvar dados, sistema não abre, licença expirada

### Hardware
Problemas com computadores, impressoras, periféricos, componentes físicos.

**Exemplos:** Impressora não imprime, teclado com defeito, HD com ruído, monitor piscando

### Segurança
Incidentes ou solicitações relacionadas à segurança da informação.

**Exemplos:** Tentativa de invasão, malware detectado, certificado SSL expirado, usuário suspeito

### Acesso
Solicitações de acesso a sistemas, pastas, recursos, permissões.

**Exemplos:** Novo usuário no Active Directory, acesso ao sistema financeiro, liberação de pasta compartilhada

### Consulta
Solicitações de informações ou dúvidas gerais sem execução técnica.

**Exemplos:** Como funciona o backup?, Quando será a manutenção?, Dúvida sobre política de senhas

---

## 📊 GUT Score - Priorização

**Fórmula:** GUT = Gravidade × Urgência × Tendência

Cada dimensão é avaliada de 1 a 5:

### Gravidade (Impacto)
- 5: Muito alta - Impacto crítico nos negócios
- 4: Alta - Impacto significativo
- 3: Média - Impacto moderado
- 2: Baixa - Impacto pequeno
- 1: Muito baixa - Impacto mínimo

### Urgência (Tempo)
- 5: Muito alta - Ação imediata necessária
- 4: Alta - Ação em poucas horas
- 3: Média - Ação no mesmo dia
- 2: Baixa - Ação em alguns dias
- 1: Muito baixa - Pode esperar

### Tendência (Evolução)
- 5: Muito alta - Vai piorar rapidamente
- 4: Alta - Vai piorar em breve
- 3: Média - Pode piorar
- 2: Baixa - Não deve piorar
- 1: Muito baixa - Não vai piorar

### Prioridades Resultantes

| GUT Score | Prioridade | Ação |
|-----------|------------|------|
| 100-125 | CRÍTICO | Ação imediata |
| 64-99 | ALTO | Ação urgente |
| 27-63 | MÉDIO | Ação planejada |
| 1-26 | BAIXO | Backlog |

---

## 🔄 Fluxo de Trabalho VSA

```
1. CLASSIFICAÇÃO
   ↓
   Tipo: INCIDENTE/PROBLEMA/MUDANÇA/REQUISIÇÃO/CONVERSA
   Categoria: Infraestrutura/Rede/Software/Hardware/Segurança/Acesso/Consulta
   GUT Score: Cálculo automático

2. PLANEJAMENTO
   ↓
   Criação de plano de ação baseado no tipo ITIL

3. EXECUÇÃO
   ↓
   Consulta GLPI, Zabbix, Linear conforme necessário

4. RESULTADO
   ↓
   Análise detalhada + Recomendações
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Incidente

```
Usuário: "O servidor web01 está fora do ar"

VSA Classifica:
- Tipo: INCIDENTE
- Categoria: Infraestrutura
- GUT Score: 125 (5×5×5)
- Prioridade: CRÍTICO

Plano:
1. Coleta de Informações (GLPI + Zabbix)
2. Diagnóstico (verificar logs, alertas)
3. Resolução (restart serviço ou servidor)
4. Documentação
```

### Exemplo 2: Problema

```
Usuário: "Todo dia às 14h o sistema fica lento, precisamos investigar"

VSA Classifica:
- Tipo: PROBLEMA
- Categoria: Software
- GUT Score: 80 (4×5×4)
- Prioridade: ALTO

Plano:
1. Coleta de Dados (histórico de incidentes)
2. Análise RCA (5 Porquês)
3. Ação Corretiva (otimização ou escalabilidade)
4. Documentação
```

### Exemplo 3: Requisição

```
Usuário: "Preciso de acesso ao sistema financeiro"

VSA Classifica:
- Tipo: REQUISIÇÃO
- Categoria: Acesso
- GUT Score: 27 (3×3×3)
- Prioridade: MÉDIO

Plano:
1. Validação (verificar aprovação do gestor)
2. Execução (criar usuário/permissões)
3. Verificação (testar acesso)
4. Documentação
```

---

## 🔗 Referências

- ITIL Foundation v4
- ITIL Service Operation
- GUT Matrix (Kepner-Tregoe)
- DeepCode VSA Documentation

---

**Documento mantido por:** VSA Tecnologia
**Última revisão:** 27/01/2026
