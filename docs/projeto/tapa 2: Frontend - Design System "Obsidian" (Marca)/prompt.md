Atue como um **Especialista em Frontend e Design Systems (Next.js + Tailwind)**.

Vamos aplicar o redesign **"DeepCode Obsidian v2.0"** no frontend do projeto.
**Identidade Visual:**

- **Tema:** Dark Mode profundo (quase preto, não cinza).
- **Cores da Marca:** Primária Laranja (`#F97316`) e Secundária Azul (`#3B82F6`).
- **Estilo:** Glassmorphism, Neon Glows, Layout fluido (App-Shell).

Execute as seguintes alterações nos arquivos existentes em `frontend/`:

### 1. Configurar Tokens (`frontend/tailwind.config.ts`)

Atualize o `theme.extend`:

- **Cores:**
  - `obsidian`: `{ 950: '#050505', 900: '#0a0a0a', 800: '#121212' }`
  - `brand`: `{ primary: '#F97316', secondary: '#3B82F6', dark: '#9a3412' }`
- **Sombras (Glows):**
  - `glow-brand`: `'0 0 40px -10px rgba(249, 115, 22, 0.4)'`
  - `glow-blue`: `'0 0 40px -10px rgba(59, 130, 246, 0.4)'`
- **Animações:** Adicione `float` e `pulse-slow`.

### 2. CSS Global (`frontend/src/app/globals.css`)

- Defina o `body` com `bg-obsidian-950`, `color-white` e `overflow-hidden`.
- Crie a classe `.glass-panel`:

  ```css
  .glass-panel {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }


Crie classes .ambient-orb para adicionar esferas de luz laranja/azul fixas no fundo (z-index: -1).

1. Layout Principal (frontend/src/app/layout.tsx)
Adicione as divs de luz ambiente (Ambient Orbs) no nível raiz.

Garanta que a estrutura suporte o layout de tela cheia sem scroll na janela principal.

1. Sidebar Moderna (frontend/src/components/app/Sidebar.tsx)
Refatore a Sidebar:

Use backdrop-blur-xl e fundo semitransparente.

Ícones: Use lucide-react.

Item Ativo: Deve ter um gradiente linear sutil de Laranja para transparente e uma borda esquerda Laranja (border-l-4 border-brand-primary).

O rodapé deve mostrar o status do sistema.

1. Atualizar Componentes (frontend/src/components/ui/*.tsx)
Button: Atualize as variantes para usar bg-brand-primary com shadow-glow-brand no estado padrão. Adicione efeito de escala (active:scale-95).

Card: Adicione a classe glass-panel como padrão.
