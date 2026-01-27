# Fix: Persistência dos Toggles VSA

## 🐛 Problema Reportado
Os toggles (VSA, GLPI, Zabbix, Linear) não persistem ao recarregar a página - sempre voltam para o estado desativado.

## 🔍 Análise da Causa Raiz

### Causa 1: Hidratação SSR (Server-Side Rendering)
O hook `useLocalStorageState` tinha lógica que tentava ler localStorage no `useState` inicial, causando inconsistência entre renderização do servidor e cliente.

**Problema:**
```typescript
const [state, setState] = useState<boolean>(() => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(key);
    return saved === 'true';  // ❌ Pode causar mismatch SSR/CSR
  }
  return defaultValue;
});
```

### Causa 2: Event Propagation
Os switches não estavam usando `preventDefault()`, o que poderia causar comportamento inesperado do submit do formulário.

## ✅ Correções Aplicadas

### Fix 1: Refatorar `useLocalStorageState` Hook

**Arquivo:** `frontend/src/state/useGenesisUI.tsx` (linhas 6-32)

**ANTES:**
```typescript
function useLocalStorageState(key: string, defaultValue: boolean): [boolean, (value: boolean) => void] {
  const [state, setState] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(key);
      console.log(`[useLocalStorageState] Init ${key}:`, saved);
      return saved === 'true';
    }
    return defaultValue;
  });

  const setValue = useCallback((value: boolean) => {
    setState(value);
    if (typeof window !== 'undefined') {
      localStorage.setItem(key, String(value));
      console.log(`[useLocalStorageState] Saved ${key}:`, value);
    }
  }, [key]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(key);
      console.log(`[useLocalStorageState] Mount sync ${key}:`, saved);
      if (saved !== null && (saved === 'true') !== state) {
        setState(saved === 'true');
      }
    }
  }, [key]);

  return [state, setValue];
}
```

**DEPOIS:**
```typescript
function useLocalStorageState(key: string, defaultValue: boolean): [boolean, (value: boolean) => void] {
  // Always start with defaultValue for SSR
  const [state, setState] = useState<boolean>(defaultValue);
  const [isHydrated, setIsHydrated] = useState(false);

  // Hydrate from localStorage on mount (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(key);
      console.log(`[useLocalStorageState] Hydrating ${key}:`, saved);

      if (saved !== null) {
        const parsedValue = saved === 'true';
        setState(parsedValue);
        console.log(`[useLocalStorageState] Restored ${key}:`, parsedValue);
      }

      setIsHydrated(true);
    }
  }, [key]);

  const setValue = useCallback((value: boolean) => {
    setState(value);
    if (typeof window !== 'undefined') {
      localStorage.setItem(key, String(value));
      console.log(`[useLocalStorageState] Saved ${key}:`, value);
    }
  }, [key]);

  return [state, setValue];
}
```

**Mudanças:**
- ✅ Sempre inicia com `defaultValue` (consistente para SSR)
- ✅ Hidrata do localStorage **somente** no `useEffect` (client-side)
- ✅ Remove lógica complexa de sincronização condicional
- ✅ Adiciona flag `isHydrated` para tracking (futuro uso)
- ✅ Logs mais claros ("Hydrating" vs "Restored")

### Fix 2: Adicionar `preventDefault` nos Switches

**Arquivo:** `frontend/src/components/app/SettingsPanel.tsx`

**ANTES:**
```tsx
<Switch
  checked={enableVSA}
  label={enableVSA ? "Ativo" : "Inativo"}
  onClick={() => setEnableVSA(!enableVSA)}
/>
```

**DEPOIS:**
```tsx
<Switch
  checked={enableVSA}
  label={enableVSA ? "Ativo" : "Inativo"}
  onClick={(e) => {
    e.preventDefault();
    setEnableVSA(!enableVSA);
  }}
/>
```

**Mudanças:**
- ✅ Adiciona `e.preventDefault()` em todos os 4 switches (VSA, GLPI, Zabbix, Linear)
- ✅ Previne comportamento default de submit/navigation
- ✅ Garante que apenas o toggle state seja alterado

## 📊 Impacto

### Arquivos Modificados
1. `frontend/src/state/useGenesisUI.tsx` - Hook de persistência
2. `frontend/src/components/app/SettingsPanel.tsx` - 4 switches

### Linhas Alteradas
- useGenesisUI.tsx: ~30 linhas refatoradas
- SettingsPanel.tsx: 16 linhas modificadas (4 switches × 4 linhas cada)

## 🧪 Como Testar

Ver `TESTE-TOGGLES.md` para script completo de teste.

**Teste Rápido:**
1. Reiniciar frontend: `cd frontend && npm run dev`
2. Abrir http://localhost:3000
3. Ativar "Modo VSA" + todas integrações
4. Recarregar página (F5)
5. **Verificar:** Toggles devem permanecer ativados ✅

## 🎯 Resultado Esperado

✅ **Toggles persistem corretamente ao recarregar**
✅ **localStorage sincroniza automaticamente**
✅ **Console logs indicam hidratação bem-sucedida**
✅ **Sem warnings de hidratação no console**

## 📝 Notas Técnicas

### Por que useEffect em vez de useState(() => ...)?

**Problema com useState inicial:**
- SSR renderiza no servidor (sem `window`)
- CSR renderiza no cliente (com `window`)
- Se o valor inicial for diferente, React emite warning de hidratação

**Solução com useEffect:**
- SSR sempre usa `defaultValue` (consistente)
- useEffect roda **somente no cliente** após montagem
- Não há mismatch entre server/client render
- Padrão recomendado pelo Next.js para localStorage

### Storage Keys Usados
```
vsa_enableVSA    → Modo VSA principal
vsa_enableGLPI   → Integração GLPI
vsa_enableZabbix → Integração Zabbix
vsa_enableLinear → Integração Linear
```

### Debug Console Logs
Após a correção, você deve ver no console:
```
[useLocalStorageState] Hydrating vsa_enableVSA: true
[useLocalStorageState] Restored vsa_enableVSA: true
[useLocalStorageState] Hydrating vsa_enableGLPI: true
[useLocalStorageState] Restored vsa_enableGLPI: true
...
```

## 🔄 Próximos Passos

1. ✅ Testar em ambiente dev
2. ⏳ Testar em build de produção (`npm run build`)
3. ⏳ Testar em múltiplos navegadores (Chrome, Firefox, Safari, Edge)
4. ⏳ Validar que não há memory leaks
5. ⏳ Criar commit com as mudanças

## 📚 Referências

- [Next.js - Client-side data fetching](https://nextjs.org/docs/pages/building-your-application/data-fetching/client-side)
- [React - Hydration](https://react.dev/reference/react-dom/client/hydrateRoot)
- [MDN - localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)

---

**Fix aplicado em:** 2026-01-27 14:45 BRT
**Autor:** Claude Code
**Status:** ✅ Pronto para teste
**Issue:** Toggles VSA não persistem ao recarregar
