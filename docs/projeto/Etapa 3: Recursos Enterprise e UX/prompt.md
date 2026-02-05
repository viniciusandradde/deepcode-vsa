## 🚀 Etapa 3: Recursos Enterprise e UX

**Objetivo:** Implementar funcionalidades de nível empresarial como "Command Palette", virtualização de chat e melhorias de performance percebida.

**Copie este Prompt:**

```markdown
Atue como um **Engenheiro de Produto Sênior**.

O backend e o visual base já foram atualizados. Agora, vamos implementar recursos de **UX Enterprise** para o `deepcode-vsa`.

Implemente as seguintes melhorias no Frontend (`frontend/`):

### 1. Command Palette (Cmd+K)
Instale a biblioteca `cmdk` (`npm install cmdk`).
- Crie o componente `CommandMenu.tsx`.
- Ele deve abrir com `Ctrl+K` ou `Cmd+K`.
- **Ações:**
  - Navegar para: Dashboard, Planejamento, Configurações.
  - Ações Rápidas: "Novo Agendamento", "Ver Status do Linear", "Limpar Chat".
  - Tema: Alternar visualização (se houver).
- Estilize o modal usando o efeito `glass-panel` e as cores da marca (Laranja na seleção).

### 2. Melhoria na Área de Chat (`frontend/src/components/app/ChatPane.tsx`)
- **Virtualização:** Se possível, integre `react-virtuoso` para renderizar listas longas de mensagens sem travar o navegador.
- **Formatação:** As mensagens do usuário devem ter alinhamento à direita com fundo `bg-brand-primary/20`. As do agente à esquerda com `glass-panel`.
- **Markdown:** Garanta que as tabelas (como a Matriz do Linear) sejam renderizadas com estilos de bordas finas e cabeçalhos escuros.

### 3. Página de Automação (`frontend/src/app/automation/page.tsx`)
Crie uma nova página para gerenciar os agendamentos criados na Etapa 1.
- **Listagem:** Tabela com os Jobs ativos, frequência (CRON) e próxima execução.
- **Criação:** Um formulário (em um Dialog/Modal) para criar novos agendamentos de Prompt.
  - Campo de Prompt (Textarea).
  - Seletor de Frequência (Diário, Semanal, Custom CRON).
  - Seletor de Canal (Telegram, Teams, WhatsApp).
- Use os componentes estilizados (Botões Laranja, Inputs Glass).

### 4. Skeleton Loading
Crie um componente `Skeleton.tsx` que usa uma animação `pulse` com `bg-white/5`.
- Aplique este esqueleto nas áreas de Dashboard e Chat enquanto os dados do backend estão carregando, substituindo os "Spinners" antigos.
