# Guia PWA - DeepCode VSA

## Visão Geral

O frontend do **DeepCode VSA** (Next.js 15 + React 19) foi preparado como **Progressive Web App (PWA)**:

- Installável em desktop e mobile
- Suporte básico a uso offline (assets e shell da aplicação)
- Otimizações específicas para dispositivos móveis

Este guia explica como instalar, testar e depurar a PWA.

---

## Instalação da PWA

### Android (Chrome)

1. Acesse a URL do DeepCode VSA no Chrome.
2. Aguarde o banner **"Instalar DeepCode VSA"** aparecer no rodapé.
3. Clique em **Instalar**.
4. Confirme na modal do navegador.

A PWA ficará disponível na tela inicial e na gaveta de apps.

### iOS (Safari)

1. Acesse a URL do DeepCode VSA no Safari.
2. Toque no ícone de **compartilhar**.
3. Selecione **"Adicionar à Tela de Início"**.
4. Confirme o nome sugerido ou personalize.

O app abrirá em modo standalone, sem barra de endereço.

### Desktop (Chrome / Edge)

1. Acesse a URL do DeepCode VSA.
2. Clique no ícone de instalação na barra de endereços (ícone de monitor + seta / "Instalar app").
3. Confirme a instalação.

O app fica disponível como aplicação standalone no sistema operacional.

---

## Comportamento Offline

### O que funciona offline

- Shell da aplicação (layout, sidebar, UI principal).
- Assets estáticos:
  - CSS, JS, fontes, imagens.
- Sessões e mensagens salvas em `localStorage`.

### O que NÃO funciona offline

- Requisições para a API de chat (`/api/threads/...`).
- Streaming SSE do backend.

Quando o dispositivo estiver sem conexão:

- O **banner amarelo** no topo ("Sem conexão com a internet") é exibido.
- A UI continua acessível; mensagens antigas permanecem visíveis.
- Novas mensagens podem falhar ao enviar (dependendo da conectividade).

---

## Componentes PWA Implementados

### Manifest

- Arquivo: `frontend/public/manifest.json`
- Principais campos:
  - `name`: DeepCode VSA - Virtual Support Agent
  - `short_name`: DeepCode VSA
  - `display`: `standalone`
  - `background_color`: `#0d1426`
  - `theme_color`: `#FF6B35`
  - `icons`: utiliza `public/images/vsa-logo.png` (192px e 512px)

### Service Worker

- Integrado via **next-pwa**:
  - Configuração em `frontend/next.config.mjs`.
  - Gera `public/sw.js` em build de produção.
  - Ativo em `NODE_ENV=production`.
- Estratégia geral:
  - **Shell + assets estáticos** em cache.
  - Requests da API continuam `NetworkFirst` (sem cache agressivo de respostas do chat).

### Banners

- `InstallPromptBanner`:
  - Arquivo: `frontend/src/components/app/InstallPromptBanner.tsx`
  - Usa hook `useInstallPrompt` (`frontend/src/hooks/useInstallPrompt.ts`).
  - Exibe CTA para instalar o app quando o evento `beforeinstallprompt` estiver disponível.

- `OfflineBanner`:
  - Arquivo: `frontend/src/components/app/OfflineBanner.tsx`
  - Usa hook `useOnlineStatus` (`frontend/src/hooks/useOnlineStatus.ts`).
  - Mostra aviso fixo no topo quando `navigator.onLine === false`.

### Hooks Utilitários

- `useInstallPrompt`: gerencia o fluxo de instalação (PWA install prompt).
- `useOnlineStatus`: expõe `isOnline` reagindo a eventos `online/offline`.
- `useSwipeGesture`: disponível para futuras otimizações de UX em mobile.
- `useNotifications`: encapsula permissões e exibição de notificações (integração futura com o chat).

---

## Boas Práticas de Uso

1. **Sempre testar em produção**
   - Service Worker e PWA se comportam de forma diferente em `development`.
   - Use build de produção (`pnpm build` + `pnpm start`) ou ambiente de deploy.

2. **Forçar atualização**
   - Quando o frontend for atualizado, o Service Worker será substituído.
   - O next-pwa usa `skipWaiting`, então a nova versão assume assim que o usuário recarregar o app.

3. **Evitar cache de respostas do chat**
   - Manter as respostas da API como `NetworkFirst` reduz inconsistências.
   - O foco do cache é performance de assets e shell da aplicação.

---

## Como Testar a PWA

### Chrome DevTools (Lighthouse)

1. Abra o app no Chrome.
2. Abra DevTools (F12).
3. Aba **Lighthouse**.
4. Selecione:
   - Device: **Mobile**
   - Categories: ao menos **Performance, Best Practices, PWA**.
5. Clique em **Analyze page load**.

Objetivos:

- PWA: checklist completo (installável, offline, manifest válido).
- Performance: > 90 (em ambientes estáveis).

### Painel Application (DevTools)

1. Aba **Application**.
2. Verifique:
   - **Manifest**: todos os campos carregados, ícones válidos.
   - **Service Workers**: `sw.js` ativo, scope `/`.
   - **Cache Storage**: entradas para assets estáticos.

---

## Roadmap de Evolução PWA

Itens sugeridos para versões futuras:

1. **Background Sync**
   - Sincronizar mensagens enviadas offline quando a conexão voltar.
2. **Notificações Push integradas ao chat**
   - Notificar quando novas respostas chegarem com o app em background.
3. **Web Share API**
   - Compartilhar análises ou planos de ação gerados pelo VSA.
4. **Export/Import de Sessões**
   - Usar File System Access API (navegadores suportados).

---

## Referências

- Documentação oficial PWA:
  - https://web.dev/learn/pwa/
- next-pwa:
  - https://github.com/shadowwalker/next-pwa
- Progressive Web Apps no Next.js:
  - https://nextjs.org/docs/app/building-your-application/optimizing/progressive-web-apps
