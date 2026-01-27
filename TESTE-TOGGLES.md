# Teste de Persistência dos Toggles VSA

## Problema Reportado
Os toggles (VSA, GLPI, Zabbix, Linear) não persistem ao recarregar a página.

## Correção Aplicada
Refatorado `useLocalStorageState` em `frontend/src/state/useGenesisUI.tsx` para corrigir problema de hidratação SSR.

### O que foi mudado:
- **ANTES:** Tentava ler localStorage no `useState` inicial (causava inconsistência SSR)
- **DEPOIS:** Sempre inicia com `defaultValue`, depois hidrata do localStorage no `useEffect`

## Como Testar

### 1. Reiniciar o Frontend
```bash
cd frontend
npm run dev
```

### 2. Abrir o DevTools do Navegador
```
F12 → Console
```

### 3. Testar Persistência

#### Passo 1: Ativar Toggles
1. Abra http://localhost:3000
2. Clique em "Mostrar Configurações"
3. Ative "Modo VSA"
4. Ative "GLPI", "Zabbix", "Linear"

#### Passo 2: Verificar localStorage
No Console do navegador, execute:
```javascript
console.log('enableVSA:', localStorage.getItem('vsa_enableVSA'));
console.log('enableGLPI:', localStorage.getItem('vsa_enableGLPI'));
console.log('enableZabbix:', localStorage.getItem('vsa_enableZabbix'));
console.log('enableLinear:', localStorage.getItem('vsa_enableLinear'));
```

**Resultado esperado:**
```
enableVSA: true
enableGLPI: true
enableZabbix: true
enableLinear: true
```

#### Passo 3: Recarregar Página (F5)
1. Pressione F5 para recarregar
2. Abra "Configurações" novamente
3. **Verificar:** Todos os toggles devem estar ATIVADOS ✅

#### Passo 4: Verificar Console Logs
Procure por mensagens do tipo:
```
[useLocalStorageState] Hydrating vsa_enableVSA: true
[useLocalStorageState] Restored vsa_enableVSA: true
```

### 4. Teste de Desativação

#### Passo 1: Desativar Tudo
1. Desative "GLPI", "Zabbix", "Linear"
2. Desative "Modo VSA"

#### Passo 2: Verificar localStorage
```javascript
console.log('Após desativar:');
console.log('enableVSA:', localStorage.getItem('vsa_enableVSA'));
console.log('enableGLPI:', localStorage.getItem('vsa_enableGLPI'));
console.log('enableZabbix:', localStorage.getItem('vsa_enableZabbix'));
console.log('enableLinear:', localStorage.getItem('vsa_enableLinear'));
```

**Resultado esperado:**
```
enableVSA: false
enableGLPI: false
enableZabbix: false
enableLinear: false
```

#### Passo 3: Recarregar (F5)
1. Recarregar página
2. Abrir "Configurações"
3. **Verificar:** Todos os toggles devem estar DESATIVADOS ✅

## Casos de Teste

### ✅ Caso 1: Primeira Visita
- Todos os toggles começam DESATIVADOS (defaultValue = false)
- localStorage está vazio

### ✅ Caso 2: Ativar e Recarregar
- Ativar toggles
- localStorage salvo com 'true'
- Recarregar página
- Toggles devem estar ATIVADOS

### ✅ Caso 3: Desativar e Recarregar
- Desativar toggles
- localStorage salvo com 'false'
- Recarregar página
- Toggles devem estar DESATIVADOS

### ✅ Caso 4: Abrir em Nova Aba
- Configurar toggles na Aba 1
- Abrir http://localhost:3000 em Nova Aba (Aba 2)
- Toggles na Aba 2 devem ter os mesmos valores da Aba 1

## Debug Adicional

### Se ainda não funcionar:

#### 1. Verificar se localStorage está funcionando
```javascript
// No Console
localStorage.setItem('test', 'value');
console.log(localStorage.getItem('test')); // Deve retornar 'value'
localStorage.removeItem('test');
```

#### 2. Limpar localStorage completamente
```javascript
localStorage.clear();
location.reload();
```

#### 3. Verificar Console Logs
Procure por mensagens:
- `[useLocalStorageState] Hydrating ...`
- `[useLocalStorageState] Restored ...`
- `[useLocalStorageState] Saved ...`

#### 4. Verificar Application Tab
1. DevTools → Application
2. Storage → Local Storage
3. http://localhost:3000
4. Procurar por chaves: `vsa_enableVSA`, `vsa_enableGLPI`, etc.

## Resultado Esperado

✅ **Todos os toggles devem persistir corretamente ao recarregar a página**

## Se o Problema Persistir

Se após a correção ainda não funcionar, capture:
1. Screenshot do console com os logs
2. Screenshot do Application → Local Storage
3. Versão do navegador

## Código Modificado

**Arquivo:** `frontend/src/state/useGenesisUI.tsx`
**Linhas:** 6-32
**Commit:** [pendente]

### Diff da Mudança:
```diff
function useLocalStorageState(key: string, defaultValue: boolean): [boolean, (value: boolean) => void] {
- const [state, setState] = useState<boolean>(() => {
-   if (typeof window !== 'undefined') {
-     const saved = localStorage.getItem(key);
-     return saved === 'true';
-   }
-   return defaultValue;
- });
+ // Always start with defaultValue for SSR
+ const [state, setState] = useState<boolean>(defaultValue);
+ const [isHydrated, setIsHydrated] = useState(false);

+ // Hydrate from localStorage on mount (client-side only)
+ useEffect(() => {
+   if (typeof window !== 'undefined') {
+     const saved = localStorage.getItem(key);
+     if (saved !== null) {
+       const parsedValue = saved === 'true';
+       setState(parsedValue);
+     }
+     setIsHydrated(true);
+   }
+ }, [key]);

  const setValue = useCallback((value: boolean) => {
    setState(value);
    if (typeof window !== 'undefined') {
      localStorage.setItem(key, String(value));
    }
  }, [key]);

  return [state, setValue];
}
```

---

**Teste criado em:** 2026-01-27
**Autor:** Claude Code
**Status:** Aguardando validação
