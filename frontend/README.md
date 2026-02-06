# Frontend - AI Agent + RAG Template

Frontend Next.js completo com interface de chat avançada e gerenciamento de sessões.

## Características

- ✅ Interface de chat completa com markdown
- ✅ Gerenciamento de sessões múltiplas
- ✅ Configuração dinâmica de modelo e ferramentas
- ✅ Sidebar com seleção de modelos e sessões
- ✅ State management com Context API
- ✅ Integração com API FastAPI

## Estrutura

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Página principal
│   │   ├── layout.tsx            # Layout base
│   │   └── api/
│   │       ├── models/            # API de modelos
│   │       └── threads/           # API de threads e mensagens
│   ├── components/
│   │   ├── app/
│   │   │   ├── ChatPane.tsx      # Componente de chat
│   │   │   └── Sidebar.tsx       # Sidebar com configurações
│   │   └── ui/                    # Componentes UI básicos
│   ├── state/
│   │   ├── types.ts              # Shared types
│   │   ├── error-utils.ts        # API error translation
│   │   ├── use-local-storage-state.ts # localStorage hook
│   │   ├── config-context.tsx    # Models & integration toggles
│   │   ├── session-context.tsx   # Session CRUD
│   │   ├── chat-context.tsx      # Messages & streaming
│   │   └── useGenesisUI.tsx      # Facade hook (backward-compat)
│   └── lib/
│       └── config.ts              # Configuração de URLs
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.mjs
```

## Instalação

```bash
cd frontend
npm install
```

## Configuração

Configure as variáveis de ambiente em `.env.local`:

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## Execução

```bash
npm run dev
```

Acesse `http://localhost:3000` para ver a interface.

## Componentes Principais

### ChatPane

Componente principal de chat com:
- Renderização de mensagens com markdown
- Auto-scroll inteligente
- Indicadores de status (pensando, enviando)
- Suporte a múltiplas sessões

### Sidebar

Sidebar com:
- Seleção de modelos LLM
- Configuração de ferramentas (Tavily)
- Lista de sessões ativas
- Criação de novas sessões

### State Management (split contexts)

O estado do frontend foi refatorado de um monolito (1239 linhas) para 3 contextos focados:

- **ConfigContext** (`config-context.tsx`) — Modelos LLM, toggles de integracao (GLPI, Zabbix, Linear, etc.)
- **SessionContext** (`session-context.tsx`) — CRUD de sessoes, navegacao entre sessoes
- **ChatContext** (`chat-context.tsx`) — Mensagens, streaming SSE, envio/edicao/reenvio

O hook `useGenesisUI()` continua disponivel como facade backward-compatible que compoe os 3 contextos.
Componentes podem opcionalmente usar `useConfig()`, `useSession()` ou `useChat()` diretamente para re-renders mais granulares.

## Integração com API

O frontend se conecta à API FastAPI através das rotas Next.js em `src/app/api/`:

- `/api/models` - Lista modelos disponíveis
- `/api/threads` - Gerencia threads/sessões
- `/api/threads/[threadId]/messages` - Envia mensagens

## Próximos Passos

- Adicionar streaming de respostas (SSE)
- Implementar histórico de conversas persistente
- Adicionar mais opções de configuração
- Melhorar tratamento de erros

