# Skill: Analytics Dashboard Hospitalar

## Descrição
Define padrões para o dashboard React de indicadores hospitalares do VSA Analytics Health.

## Contexto
- **Framework:** React 18 + TypeScript
- **Estado:** TanStack Query (react-query)
- **UI:** Tailwind CSS
- **Charts:** Recharts
- **API:** FastAPI (backend) com Scalar docs

## Regras Obrigatórias

1. Dados sempre agregados (nunca paciente individual no dashboard)
2. Refresh automático com TanStack Query (staleTime por categoria)
3. Loading states em todos os componentes com dados assíncronos
4. Responsivo (mobile-first para uso em plantão)
5. Cores semafóricas para indicadores críticos (verde/amarelo/vermelho)

## Módulos do Dashboard

| # | Módulo | Indicadores | Refresh |
|---|--------|-------------|---------|
| 1 | Ocupação de Leitos | Disponíveis, ocupados, % por setor | 1 min |
| 2 | Internações | Entradas/saídas, tempo médio, por convênio | 5 min |
| 3 | Agendamentos | Do dia, confirmados, faltas, próximos | 5 min |
| 4 | Faturamento | Receita, glosas, pendências, por convênio | 15 min |
| 5 | Centro Cirúrgico | Cirurgias do dia, tempo médio, ocupação sala | 5 min |
| 6 | CCIH | Taxa infecção, culturas, alertas | 15 min |
| 7 | Pronto-Socorro | Classificação Manchester, tempo espera | 1 min |
| 8 | Estratégico | KPIs consolidados C1-C20 | 1 hora |

## Padrão de Hook com Cache

```typescript
// hooks/useInternacoes.ts
import { useQuery } from '@tanstack/react-query';

export function useInternacoes(periodo: string) {
  return useQuery({
    queryKey: ['internacoes', periodo],
    queryFn: () => api.get(`/api/v1/internacoes?periodo=${periodo}`),
    staleTime: 5 * 60 * 1000,    // 5 minutos
    refetchInterval: 5 * 60 * 1000,
    retry: 2,
  });
}
```

## Padrão de Componente

```typescript
// components/OcupacaoLeitos.tsx
export function OcupacaoLeitos() {
  const { data, isLoading, error } = useOcupacao();
  
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorState message="Erro ao carregar ocupação" />;
  
  return (
    <Card>
      <CardHeader title="Ocupação de Leitos" />
      <div className="grid grid-cols-3 gap-4">
        <Indicator 
          label="Ocupados" 
          value={data.ocupados} 
          color={data.taxa > 90 ? 'red' : data.taxa > 70 ? 'yellow' : 'green'}
        />
        {/* ... */}
      </div>
    </Card>
  );
}
```

## Anti-Padrões

- ❌ Mostrar nome/CPF de paciente individual
- ❌ Fetch sem loading/error state
- ❌ CSS custom (usar Tailwind)
- ❌ Estado global para dados do servidor (usar TanStack Query)
- ❌ Gráficos sem legenda ou unidade
