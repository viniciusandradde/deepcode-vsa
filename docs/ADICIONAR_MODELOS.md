# Adicionar novos modelos LLM

Este guia explica como adicionar um novo modelo ao sistema e garantir que ele apareca no frontend.

## Visao geral do fluxo

1) O frontend carrega modelos via `/api/models`.
2) A rota `/api/models` le o arquivo `models.yaml` dentro do container do frontend.
3) Para atualizar a lista, e necessario **rebuild do frontend** e **recriar o container**.

## Passo a passo (resumido)

1) Edite `models.yaml` e adicione o modelo.
2) Valide o YAML:
   ```bash
   make models-validate
   ```
3) Rebuild e recrie o frontend:
   ```bash
   make models-rebuild-frontend
   ```
4) Confirme a lista:
   ```bash
   make models-print
   ```

## Exemplo de entrada no `models.yaml`

```yaml
- id: qwen/qwen-2.5-vl-7b-instruct
  label: Qwen 2.5 VL 7B (vision)
  input_cost: 0.00
  output_cost: 0.00
```

## Problemas comuns

### Nao aparece no frontend

Verifique:
- O frontend foi rebuildado e o container recriado.
- O Service Worker do PWA nao esta servindo cache antigo.

Para limpar o cache do PWA:
1) DevTools > Application > Service Workers > Unregister
2) DevTools > Application > Clear storage
3) Recarregue em aba anonima

### Lista de modelos desatualizada

Confira o que o frontend esta vendo:
```bash
make models-print
```

## Producao

Use os targets de producao:
```bash
make models-rebuild-frontend-prod
```

## Referencias

- `models.yaml`
- `frontend/src/app/api/models/route.ts`
