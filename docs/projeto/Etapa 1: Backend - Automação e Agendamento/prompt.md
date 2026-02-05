Atue como um **Arquiteto de Backend Sênior (Python/FastAPI)**.

Vamos implementar o módulo **"Automation Engine"** no projeto `deepcode-vsa`. O objetivo é permitir agendamento de relatórios do Linear e execução de prompts de IA recorrentes.

**Contexto:** O projeto já possui `LinearClient` e `UnifiedAgent`. Precisamos criar a camada de agendamento.

Siga este plano de implementação, criando ou editando os arquivos listados:

### 1. Instalar Dependências (`backend/requirements.txt`)

Adicione:

- `apscheduler==3.10.4`
- `httpx==0.27.0`
- `sqlalchemy>=2.0.0` (Necessário para o JobStore do APScheduler)

### 2. Criar Serviço de Notificação (`core/notifications.py`)

Implemente a classe `NotificationService` com métodos assíncronos:

- `send_telegram(token, chat_id, message)`
- `send_teams(webhook_url, title, message)`
- `send_whatsapp(api_url, token, to_number, message)`
*Requisito:* Trate exceções com `logging.error` para não quebrar o fluxo se uma mensagem falhar.

### 3. Atualizar Relatórios do Linear (`core/reports/linear.py`)

Implemente o método `generate_status_matrix(issues)`.

- **Lógica de "Atrasados":** Se `dueDate < hoje` e status != Concluído/Cancelado, classifique como "🚨 Atrasados".
- **Mapeamento de Estados (PT-BR):**
  1. `🆕 Novo` (Triage)
  2. `📝 A Fazer` (Unstarted)
  3. `🚧 Em Progresso` (Started)
  4. `🚨 Atrasados` (Lógica acima)
  5. `✅ Concluído` (Completed)
- **Saída:** Gere uma tabela Markdown cruzando essas linhas com colunas de Prioridade (Urgente, Alta, Média, Baixa).

### 4. Criar Jobs (`core/jobs.py`)

Implemente as funções que o scheduler executará:

- `job_send_linear_matrix_report`: Busca issues via `LinearClient`, gera a matriz e envia via `notification_service`.
- `job_execute_prompt_report`:
  1. Recebe um `prompt` e `credentials`.
  2. Adiciona contexto de data: `f"{prompt}\n[Data: {datetime.now()}]"`.
  3. Instancia e executa o `UnifiedAgent`.
  4. Envia o resultado via `notification_service`.
  5. Implemente um loop de `retry` simples (3 tentativas).

### 5. Configurar Scheduler (`core/scheduler.py`)

Implemente a classe `SchedulerService`.

- **Persistência:** Use `SQLAlchemyJobStore` conectado à `DATABASE_URL` para que os agendamentos não se percam ao reiniciar o container.
- **Métodos:** `start()`, `shutdown()`, `add_prompt_execution_job()`, `list_jobs()`, `remove_job()`.

### 6. Criar API de Controle (`api/routes/automation.py`)

Crie endpoints para o Frontend gerenciar isso:

- `POST /automation/schedule`: Recebe CRON, Prompt e Configuração.
- `GET /automation/schedules`: Lista jobs ativos.
- `DELETE /automation/schedule/{job_id}`: Remove job.

### 7. Inicialização (`api/main.py`)

No evento `lifespan` do FastAPI, inicie o `scheduler_service.start()` e garanta o `shutdown()` ao fechar.

Markdown

Atue como um **Arquiteto de Backend (Python/FastAPI)**.

O objetivo é implementar o **"Universal Prompt Scheduler"** no `deepcode-vsa`.
Diferente de agendamentos estáticos, o usuário enviará uma instrução em linguagem natural (ex: *"Toda segunda, analise o Linear e liste tarefas atrasadas"*) e o sistema agendará a execução desse prompt.

Implemente ou Atualize os seguintes arquivos:

### 1. Modelos de Dados (`api/models/automation.py`)

Defina a estrutura que receberá o prompt do usuário:

```python
from pydantic import BaseModel, Field
from typing import Dict, Optional

class ScheduleConfig(BaseModel):
    channel: str = Field(..., description="Canal de saída: 'telegram', 'teams', 'whatsapp'")
    target_id: str = Field(..., description="ID do chat ou Webhook URL")
    # Credenciais podem ser opcionais se já estiverem nas env vars
    credentials: Optional[Dict[str, str]] = None 

class UniversalScheduleRequest(BaseModel):
    name: str = Field(..., description="Nome do Agendamento (ex: Relatório Semanal)")
    prompt: str = Field(..., description="A instrução COMPLETA para o Agente (ex: 'Analise as issues do projeto X...')")
    cron: str = Field(..., description="Expressão CRON (ex: '0 8 * * 1')")
    config: ScheduleConfig
2. Job Executor (core/jobs.py)
Crie a função job_run_agent_prompt que será salva no banco:

Parâmetros: prompt (str), channel_config (dict).

Fluxo:

Instancie o UnifiedAgent com acesso a TODAS as ferramentas disponíveis (Linear, Zabbix, Search, RAG).

Injete o contexto temporal no prompt: final_prompt = f"Data/Hora Atual: {datetime.now()}\nInstrução Agendada: {prompt}"

Execute o agente: result = await agent.run(final_prompt).

Envie o result para o NotificationService conforme o channel_config.

Tratamento de Erros: Se o agente falhar ou alucinar erro, envie um log de erro para o canal de notificação avisando o usuário.

3. API de Criação (api/routes/automation.py)
Endpoint: POST /automation/universal-schedule

Ação: Recebe o UniversalScheduleRequest.

Lógica: Chama o scheduler_service.add_job passando o prompt como argumento fixo para a função job_run_agent_prompt.

Persistência: Garanta que o job seja salvo no SQLAlchemyJobStore.

Nota: O segredo aqui é que o payload do agendamento carrega o prompt. O agente só é instanciado no momento da execução (trigger do cron), garantindo que ele use dados em tempo real.


---

### 🎨 Prompt de Frontend: Interface de Criação de Automação
**Copie este código para criar a UI onde o usuário digita o prompt e define a frequência.**

```markdown
Atue como um **Engenheiro Frontend Sênior (Next.js/React)**.

Precisamos criar a página **"Automation Studio"** (`frontend/src/app/automation/page.tsx`).
O objetivo é permitir que o usuário crie rotinas de IA usando linguagem natural.

**Requisitos da Interface (Use componentes 'Glass-Shell' e cores da marca):**

### 1. Lista de Agendamentos Ativos
- Tabela ou Cards mostrando:
  - **Nome:** Título da automação.
  - **Prompt (Resumo):** "Analise as issues..." (truncado).
  - **Próxima Execução:** Data/Hora relativa.
  - **Ações:** Botão de Pausar/Excluir.

### 2. Modal de Criação "Nova Automação"
Ao clicar em "Criar Agendamento", abra um Dialog com:

- **Campo 1: O que a IA deve fazer? (O Prompt)**
  - Componente: `Textarea` grande e com foco.
  - Placeholder: *"Ex: Verifique o status do servidor Zabbix e me avise se a CPU estiver > 80%..."*
  - Dica visual: "Você tem acesso a: Linear, Zabbix, Web Search."

- **Campo 2: Quando executar? (Frequência)**
  - Tabs: [Predefinições] | [Custom CRON]
  - Predefinições: "Toda manhã (08:00)", "Semanal (Seg 09:00)", "Mensal".
  - Custom: Input para string CRON.

- **Campo 3: Onde enviar a resposta? (Destino)**
  - Select: Telegram, WhatsApp, Teams.
  - Input Condicional: ID do Chat ou Webhook URL.

### 3. Lógica de Envio
- Ao salvar, faça um POST para `/api/automation/universal-schedule`.
- Mostre um Toast de sucesso e atualize a lista via Optimistic UI.

**Estilo:**
- Use o componente `glass-panel` para o modal.
- O botão de salvar deve ser `bg-brand-primary` (Laranja) com `shadow-glow-brand`.
Exemplo de Uso Prático
Com essa implementação, o fluxo do usuário será:

O usuário abre a página Automação.

Clica em "Nova Rotina".

No campo de prompt, digita:

"Acesse o projeto 'DeepCode' no Linear. Identifique todas as tarefas marcadas como 'Urgent' que não foram atualizadas há mais de 3 dias. Gere um resumo xingando educadamente os responsáveis e envie no grupo do Telegram."

Define a frequência: "Toda Sexta às 17:00".

Salva.

O Sistema:

Guarda esse texto e o CRON no Postgres.

Na sexta às 17h, "acorda".

Lança um Agente de IA.

O Agente lê o prompt, usa a tool do Linear para buscar dados, processa a lógica ("xingar educadamente") e envia o texto final.
