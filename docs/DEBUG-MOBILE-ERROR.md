# Debug - Erro Mobile PWA

**Data:** 28/01/2026  
**Erro:** Application error: a client-side exception has occurred

---

## Contexto

**Antes do PWA:** ✅ Funcionava normalmente  
**Depois do PWA:** ❌ Erro no mobile (VPN ativa)  
**Desktop:** ✅ Funciona normalmente

---

## Análise do Erro

### Screenshot do Erro

```
Application error: a client-side exception has occurred while 
loading agente-ai.hospitalevangelico.com.br (see the browser 
console for more information).
```

### Arquivos Modificados (PWA)

1. `frontend/src/app/layout.tsx` - Viewport export + manifest
2. `frontend/src/app/page.tsx` - Banners PWA adicionados
3. `frontend/next.config.mjs` - next-pwa configurado
4. `frontend/src/state/useGenesisUI.tsx` - Fix escopo
5. `frontend/src/components/app/MessageItem.tsx` - Fix tipos

---

## Hipóteses

### 1. Banners PWA causando hydration error
- **Probabilidade:** ALTA
- **Teste:** Desabilitar banners temporariamente
- **Status:** Em teste

### 2. Viewport export incompatível
- **Probabilidade:** MÉDIA
- **Solução:** Reverter para metadata inline
- **Status:** A testar se banners não forem o problema

### 3. next-pwa conflito
- **Probabilidade:** MÉDIA  
- **Solução:** Desabilitar next-pwa temporariamente
- **Status:** A testar

### 4. Mudança em useGenesisUI.tsx
- **Probabilidade:** BAIXA
- **Motivo:** Mudança mínima (escopo de variável)
- **Status:** Improvável

---

## Plano de Diagnóstico

### Passo 1: Testar sem banners PWA (ATUAL)

```typescript
// page.tsx - banners comentados
{/* <OfflineBanner /> */}
{/* <InstallPromptBanner /> */}
```

**Ação:** Reiniciar frontend e pedir ao usuário para testar no celular

**Se funcionar:** Problema está nos banners → implementar lazy loading  
**Se não funcionar:** Problema está em outro lugar → testar Passo 2

### Passo 2: Reverter viewport export

```typescript
// layout.tsx - voltar viewport para metadata
export const metadata: Metadata = {
  // ... outros campos
  viewport: {
    width: "device-width",
    initialScale: 1,
    // ...
  },
};
```

### Passo 3: Desabilitar next-pwa

```javascript
// next.config.mjs - comentar withPWA
export default nextConfig;  // Sem wrapping de PWA
```

### Passo 4: Reverter todas as mudanças PWA

```bash
git revert HEAD~10..HEAD  # Reverter últimos 10 commits
```

---

## Testes Necessários

### Teste 1: Sem Banners PWA
- [ ] Frontend compila
- [ ] Desktop funciona
- [ ] Mobile funciona (usuário testar)

### Teste 2: Sem Viewport Export
- [ ] Reverter viewport para metadata
- [ ] Rebuild
- [ ] Testar mobile

### Teste 3: Sem next-pwa
- [ ] Desabilitar withPWA
- [ ] Rebuild
- [ ] Testar mobile

---

## Logs de Análise

### Desktop (local)
```
✓ Ready in 3.2s
GET / 200
0 erros
```

### Mobile (produção via VPN)
```
❌ Application error
❌ Client-side exception
```

### Diferenças Identificadas

| Aspecto | Desktop | Mobile |
|---------|---------|--------|
| Rede | localhost | VPN |
| Ambiente | development | development |
| Browser | Chrome desktop | Chrome mobile |
| Erro | Nenhum | Client-side exception |

---

## Próximos Passos

1. **AGUARDAR** usuário testar com banners desabilitados
2. **SE FUNCIONAR:** Implementar lazy loading de banners
3. **SE NÃO FUNCIONAR:** Reverter viewport export
4. **SE AINDA NÃO FUNCIONAR:** Desabilitar next-pwa completamente

---

## Rollback Plan

Se nada funcionar:

```bash
# Opção 1: Reverter commits PWA
git revert HEAD~10..HEAD

# Opção 2: Reset para antes do PWA
git reset --hard 0940ad3
git clean -fd

# Opção 3: Cherry-pick apenas correções necessárias
git cherry-pick <hash-do-commit-necessario>
```

---

**Status:** 🔍 **EM DIAGNÓSTICO**  
**Próxima ação:** Aguardar teste do usuário com banners desabilitados
