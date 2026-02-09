Plano: Design System "DeepCode Obsidian v2.0"

 Contexto

 O frontend atual usa design light-first (fundo branco #F5F6F8, bordas slate, sombras claras). Os docs de projeto definem o novo visual "Obsidian": dark mode profundo (#050505), glassmorphism, glow
 colorido (laranja/azul), ambient orbs, e tipografia Inter. As cores de marca também mudam: laranja #F7941D -> #F97316, azul #00AEEF -> #3B82F6 (alinhamento com Tailwind palette). A Etapa 3 adiciona
 Command Palette (Cmd+K), virtualização de chat, e skeleton loading.

 Impacto: ~30 arquivos tocados (3 CSS, 1 tailwind config, 1 layout, 7 UI primitives, ~15 app components, 5 pages, 2 novos componentes).

 ---
 Fase 1: Fundação (tokens, CSS global, fonts, layout)

 1.1 Instalar dependencias

 cd frontend && npm install cmdk react-virtuoso

 1.2 Swap fonts: Source Sans + Poppins -> Inter

 Arquivo: frontend/src/app/layout.tsx

- Remover imports Source_Sans_3, Poppins
- Importar Inter do next/font/google
- Manter JetBrains_Mono
- Atualizar body className: ${inter.variable} ${jetbrainsMono.variable}
- Atualizar themeColor de #F7941D para #0a0a0a

 1.3 Reescrever Design Tokens CSS

 Arquivo: frontend/src/app/vsa-design-tokens.css

- Adicionar variáveis --obsidian-* (950: #050505, 900: #0a0a0a, 800: #121212, 700: #1a1a1a, 600: #262626)
- Adicionar --brand-primary: #F97316, --brand-secondary: #3B82F6 + variantes dark/light
- Adicionar tokens de texto escuro: --text-primary: #f5f5f5, --text-secondary: #a3a3a3, --text-muted: #737373
- Adicionar tokens de borda: --border-subtle: rgba(255,255,255,0.06), --border-default: rgba(255,255,255,0.10)
- Adicionar tokens de glass: --glass-bg, --glass-border, --glass-blur
- Adicionar tokens de glow: --glow-orange, --glow-blue (+ lg variants)
- Atualizar --vsa-orange-500 para #F97316, --vsa-blue-500 para #3B82F6
- Remover bloco [data-theme="dark"] (app é agora dark-only)
- Atualizar scrollbar para estilo thin dark (6px, thumb white/10%)
- Atualizar ::selection para brand-primary/30

 1.4 Reescrever Global CSS

 Arquivo: frontend/src/app/globals.css

- Body: bg-[#0a0a0a] text-[#f5f5f5] (era #F5F6F8 light)
- Adicionar classe .glass-panel (bg rgba(20,20,20,0.6), backdrop-blur 16px, border white/6%)
- Substituir .vsa-main-background (geometric pattern) por ambient orbs via CSS pseudo-elements
- Adicionar .skeleton com animacao pulse (bg shimmer white/3% -> white/8%)
- Adicionar @keyframes float (8s ease-in-out) e @keyframes pulse-slow

 1.5 Atualizar Tailwind Config

 Arquivo: frontend/tailwind.config.ts

- Adicionar namespace obsidian (950-500) em colors
- Adicionar namespace brand com primary (#F97316) e secondary (#3B82F6)
- Manter vsa-orange/vsa-blue existentes mas atualizar valores DEFAULT
- Adicionar shadows: glow-orange, glow-orange-lg, glow-blue, glow-blue-lg
- Adicionar animations: float, pulse-slow
- Atualizar fontFamily removendo Source Sans Pro / Poppins
- Atualizar gradient hex values nos plugins (text-vsa-gradient, border-vsa-gradient)
- Atualizar background: "white" no .border-vsa-gradient para background: "#0a0a0a"

 1.6 Atualizar Component CSS

 Arquivo: frontend/src/app/vsa-components.css

- Converter TODOS os .vsa-btn*, .vsa-card*, .vsa-input*, .vsa-sidebar*, .vsa-modal* para dark
- Pattern: background: white -> var(--obsidian-800) ou var(--glass-bg)
- Pattern: color: var(--vsa-gray-700) -> var(--text-secondary)
- Pattern: border: var(--vsa-gray-300) -> var(--border-default)
- .vsa-card -> glass-panel base
- .vsa-modal-backdrop -> rgba(0,0,0,0.7) + backdrop-blur-md

 ---
 Fase 2: UI Primitives (7 arquivos em frontend/src/components/ui/)

 Tabela de substituicao mecanica aplicada em TODOS:
 ┌──────────────────────────┬────────────────────────────────┐
 │       Classe Light       │        Classe Obsidian         │
 ├──────────────────────────┼────────────────────────────────┤
 │ bg-white                 │ bg-obsidian-800 ou glass-panel │
 ├──────────────────────────┼────────────────────────────────┤
 │ bg-slate-50/100          │ bg-white/5                     │
 ├──────────────────────────┼────────────────────────────────┤
 │ text-slate-900           │ text-white                     │
 ├──────────────────────────┼────────────────────────────────┤
 │ text-slate-700           │ text-neutral-300               │
 ├──────────────────────────┼────────────────────────────────┤
 │ text-slate-500           │ text-neutral-500               │
 ├──────────────────────────┼────────────────────────────────┤
 │ border-slate-300         │ border-white/[0.06]            │
 ├──────────────────────────┼────────────────────────────────┤
 │ border-2                 │ border (1px em dark)           │
 ├──────────────────────────┼────────────────────────────────┤
 │ shadow-sm                │ removido                       │
 ├──────────────────────────┼────────────────────────────────┤
 │ bg-vsa-orange            │ bg-brand-primary               │
 ├──────────────────────────┼────────────────────────────────┤
 │ text-vsa-orange          │ text-brand-primary             │
 ├──────────────────────────┼────────────────────────────────┤
 │ focus:ring-vsa-orange/40 │ focus:ring-brand-primary/30    │
 ├──────────────────────────┼────────────────────────────────┤
 │ focus:ring-offset-white  │ focus:ring-offset-obsidian-900 │
 └──────────────────────────┴────────────────────────────────┘
 Arquivos:

- button.tsx: Variants primary (brand-primary + glow-orange), ghost (bg-transparent hover:bg-white/5), outline (border-white/10 bg-white/5)
- card.tsx: Classe base glass-panel rounded-xl border border-white/[0.06]
- dialog.tsx: Backdrop bg-black/70 backdrop-blur-md, panel glass-panel
- badge.tsx: bg-white/5 text-neutral-300 border border-white/10
- switch.tsx: Track unchecked bg-white/10, checked bg-brand-primary shadow-glow-orange
- select.tsx: Trigger/dropdown dark bg, selected bg-brand-primary/10
- toast.tsx: Tipos com bg semitransparente escuro (emerald-900/40, red-900/40)

 ---
 Fase 3: App Shell (Sidebar, ChatPane, Input, Pages)

 3.1 Sidebar.tsx (~399 linhas)

- Aside: bg-obsidian-900 border-r border-white/[0.06]
- Active session: border-brand-primary/40 bg-brand-primary/10 shadow-glow-orange
- Inactive session: border-white/[0.06] bg-obsidian-800 hover:bg-white/5
- Textos: white/neutral-300/neutral-500

 3.2 ChatPane.tsx (~310 linhas)

- Header: bg-obsidian-900/80 backdrop-blur-md border-b border-white/[0.06]
- Status badge: glass-panel com dot bg-brand-primary animate-pulse
- Main area: vsa-main-background (agora com ambient orbs)

 3.3 MessageInput.tsx (~145 linhas)

- Container: bg-obsidian-900/80 backdrop-blur-md border-t border-white/[0.06]
- Textarea: bg-obsidian-800 border-white/10 text-white focus:border-brand-primary
- Send button: bg-brand-primary hover:shadow-glow-orange

 3.4 Pages

- page.tsx (chat): Adicionar bg-obsidian-950
- planning/page.tsx: bg-[#F5F6F8] -> bg-obsidian-950 text-white, modal glass-panel
- planning/[id]/page.tsx: Mesma conversao light -> dark
- automation/*: Normalizar bg-zinc-950 -> bg-obsidian-950, emerald buttons -> glass style
- design/page.tsx: Atualizar showcase para dark

 ---
 Fase 4: Content Components (~12 arquivos)

 4.1 MessageItem.tsx (~286 linhas)

- User msg: border-brand-primary/20 bg-brand-primary/10 text-white (right-aligned)
- Agent msg: glass-panel border border-white/[0.06] text-neutral-200
- Markdown components:
  - Code: bg-white/5 text-neutral-200
  - Pre: bg-obsidian-800 border border-white/10
  - Table: border-white/10, thead bg-white/5, hover hover:bg-white/5
  - Blockquote: border-brand-primary/30
  - Links: text-brand-primary

 4.2 ArtifactPanel.tsx (~300 linhas)

- Panel: bg-obsidian-900 border-l border-white/[0.06]
- Tab active: border-brand-primary text-white

 4.3 Outros componentes (mesma conversao mecanica)

- ArtifactCard.tsx: glass-panel + badge colors dark variant
- SuggestionChips.tsx: glass-panel hover:glow-orange
- SettingsPanel.tsx: Card/Switch/Select dark
- ThinkingIndicator.tsx: brand-primary dots/progress
- ITILBadge.tsx: bg--500/15 text--300 variants
- ActionPlan.tsx: bg-obsidian-800 borders
- MessageActions.tsx, QuickActionsMenu.tsx, DeleteConfirmDialog.tsx, Logo.tsx, ErrorBoundary.tsx

 ---
 Fase 5: Novos Features

 5.1 Command Palette (Cmd+K)

 Novo arquivo: frontend/src/components/app/CommandPalette.tsx

- Usa biblioteca cmdk instalada na fase 1
- Overlay: bg-black/60 backdrop-blur-md
- Dialog: glass-panel com max-w-lg
- Acoes: Navegar (Chat, Planning, Automation, Design), Nova sessao, Toggle VSA/GLPI/Zabbix/Linear
- Registrar atalho Cmd+K / Ctrl+K no page.tsx root

 5.2 Skeleton Loading

 Novo arquivo: frontend/src/components/ui/skeleton.tsx

- Componente simples usando .skeleton class definida na fase 1
- Aplicar em: Sidebar loading, ChatPane empty state, Planning loading

 5.3 Chat Virtualization

 Arquivo: frontend/src/components/app/ChatPane.tsx

- Substituir .map() de mensagens por <Virtuoso> de react-virtuoso
- followOutput="smooth" para auto-scroll
- Remove logica manual de scroll-to-bottom

 ---
 Verificacao

 1. cd frontend && npm run build - deve compilar sem erros
 2. npm run dev - verificar visualmente:

- Background escuro profundo (#050505)
- Ambient orbs laranja/azul suaves
- Glassmorphism em cards, sidebar, dialogs
- Texto branco/neutral legivel
- Brand orange (#F97316) em botoes, badges, focus states
- Scrollbar thin estilizada

 1. Testar Command Palette: Cmd+K abre, navega entre paginas
 2. Testar chat: mensagens user (direita, brand-primary/10) vs agent (glass-panel)
 3. Testar planning/automation: visual consistente dark
 4. npm run lint - verificar sem erros de lint
