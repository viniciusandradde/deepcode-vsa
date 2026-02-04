# Agentes de IA com LangGraph/LangChain — Projeto do Curso (M0–M2)

Bem‑vindo(a)! Este repositório acompanha o curso “Agentes de IA — da ideia à nuvem com LangGraph/LangChain”.

Você está no projeto principal, que evolui por módulos e tags. As versões são pensadas para ensino. Você pode/deve pegar as idéias e adaptar para o seu caso de uso.

## Framework RAG TopHawks

![Framework RAG TopHawks](docs/diagrams/framework-rag-tophawks.svg)

<a href="docs/diagrams/framework-rag-tophawks.svg" target="_blank" rel="noopener noreferrer">Ver maior (SVG)</a>

## Versões Didáticas (Tags)
- M0 — Setup e Fundamentos: `modulo-0`
- M1A — Iniciando o agente `modulo-1A `
- M1B — Primeiras customizações: `modulo-1B`
- M1C — Multi Agentes e Workflow customizado: `modulo-1C`
- M2 — RAG Híbrida/Agêntica (este módulo): `modulo-2`

Como listar e navegar
- `git tag -n9` para listar tags
- `git fetch --tags` (se houver remoto) e `git switch -c aula modulo-escolhido`

## Stack e Pré‑requisitos
- Python 3.11+
- LangGraph/LangChain (versões pinadas em `requirements.txt`)
- OpenAI (LLM, HyDE e juiz LLM)
- Cohere (Rerank, opcional)
- Postgres (pgvector + FTS) — pode ser Supabase
- LangGraph Studio para depuração
- Para Semantic Chunking (opcional na Fase 0):
  - Instale um dos pacotes que expõem `SemanticChunker`:
    - `langchain-experimental>=0.3.4` ou
    - `langchain-text-splitters>=0.3.9`
  - Requer `OPENAI_API_KEY` ativo para gerar embeddings.

Observações de chunking (sem fallback):
- `fixed`: cortes por tamanho/overlap.
- `markdown`: cortes por cabeçalhos (`#`, `##`, `###`) via `MarkdownHeaderTextSplitter`.
- `semantic`: cortes orientados por embeddings via `SemanticChunker`.
Se a estratégia não estiver disponível (ex.: semantic sem pacote/embeddings), a execução falha explicitamente.

Configuração rápida
- `python -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt`
  - `.env` com: `OPENAI_API_KEY`, `DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME`, opcional `COHERE_API_KEY`, `LANGSMITH_API_KEY`
  - Modelos padrão (podem ser sobrescritos por env):
    - `PROPOSAL_LLM_MODEL` (agente) = `gpt-5-nano`
    - `HYDE_LLM_MODEL` (HyDE) = `gpt-4o-mini`
    - `EVAL_LLM_MODEL` (juiz LLM em scripts) = `gpt-4.1-2025-04-14`

## Módulo 2 — RAG Híbrida/Agêntica (propostas)

O que este módulo entrega
- Novo grafo de propostas: `proposal_agent_v2` (app/rag/proposal_agent_v2.py:graph)
  - Usa as tools do Mini‑CRM (get_lead, draft_proposal, add_proposal_item, calculate_proposal_totals)
  - Busca conhecimento com `kb_search_client` (app/rag/tools.py) e filtra por `client_id` ou `empresa` (obrigatório)
  - Resposta cita fontes do KB (doc_path:chunk_ix)
- Pipeline de ingestão de `.md`: `rag_ingest` (app/rag/ingest.py:graph)
  - Splitters: fixed, markdown‑aware e semantic
  - Embeddings: `text-embedding-3-small`
  - Armazenamento: Postgres com `kb_chunks(embedding vector + FTS)`, filtros `empresa/client_id`, índices HNSW/GIN
  - Execução (Studio):
    - Aceita uma única `strategy` ou uma lista `strategies` (ex.: `["fixed", "markdown", "semantic"]`).
    - Parâmetros opcionais: `chunk_size` e `chunk_overlap`.
    - Usa `doc_path_prefix=<strategy>` ao materializar múltiplas estratégias para evitar colisão de `(doc_path, chunk_ix)`.
    - Staging é idempotente: segunda rodada com os mesmos arquivos não duplica (unicidade por `(source_path, source_hash)`).
    - Materialização é idempotente: upsert por `(doc_path, chunk_ix)` em `kb_chunks` (reprocessa sem duplicar).
    - Fallback de diretório: se `base_dir`/`BASE_DIR` não existir, usa `kb/` (se houver) ou `tests/rag/data/`.
- Técnicas de busca/ordenação:
  - Vector (cosine), Text (FTS), Hybrid com RRF no banco (kb_hybrid_search)
  - Hybrid (union) para comparação didática
  - HyDE (query expansion) opcional na tool (use_hyde=True)
  - Rerank Cohere (opcional) após recuperação (top‑N)

Conceitos centrais 
- Similaridade (cosine) e score: usamos `score = 1 - distância_cosine`; thresholds atuam sobre o score.
- Threshold (match_threshold):
  - Parâmetro opcional na tool. Controla o corte mínimo de similaridade na parcela vetorial.
  - Efeito: maior threshold reduz ruído (↑precisão, ↓recall); menor threshold aumenta cobertura (↓precisão, ↑recall).
  - Aplicado em: `kb_vector_search` e na parte vetorial de `kb_hybrid_search`/`kb_hybrid_union`.
- Hybrid (RRF) vs Union:
  - RRF combina listas lexicais e semânticas por Reciprocal Rank Fusion (barato e eficaz para recall); union é só união simples (para comparação).
- HyDE (Hypothetical Document Embeddings):
  - Gera um “documento hipotético” com LLM e embeda esse texto para a busca vetorial; útil quando a consulta é vaga.
  - Não altera a busca textual (que continua usando a query original).
- Rerank (Cohere):
  - Reordena top‑N candidatos com um modelo cross‑encoder; maximiza precisão no topo (hit@1), ao custo de latência.
- Chunking (impacto prático):
  - semantic > markdown >> fixed no nosso dataset (mas sempre teste: depende do corpus/consulta).
  - Overlap/limite de candidatos/threshold mudam o comportamento do pipeline.

Como funciona (alto nível)
- Propostas: o grafo resolve o lead com `get_lead(ref)` e injeta `empresa/client_id` para a tool de busca; recupera trechos do KB e opera as tools do CRM para rascunhar/precificar a proposta.
- Ingestão: `rag_ingest` lê `.md` de `kb/` (ou do dataset didático em `tests/rag/data`), divide, embeda e upserta com filtros e metadados.

## Dataset Didático e Experimentos
- Fonte: `tests/rag/data/`
  - `empresa_x/` e `empresa_y/`: produtos, serviços, políticas e relatórios de leads (lead_reports)
  - `queries.yaml`: conjunto de perguntas (empresa/cliente), com termo “esperado” para avaliação simples
- Matriz de Experimentos: `tests/rag/experiments.yaml`
  - chunking ∈ {markdown, semantic}
  - search_type ∈ {vector, text, hybrid_rrf}
  - use_hyde ∈ {false, true}

Runner de Experimentos
- Configuração (tests/rag/experiments.yaml):
  - chunking ∈ {markdown, semantic}
  - search_type ∈ {vector, text, hybrid_rrf}
  - use_hyde ∈ {false, true}
  - match_threshold ∈ {0.50, 0.75, …} (opcional)

## Métricas e Como Ler os Resultados

Os testes imprimem tabelas comparando configurações (chunking × search_type × HyDE × threshold). As colunas são:

- name: apelido do experimento (do arquivo experiments.yaml)
- chunking: estratégia de recorte do texto fonte (fixed/markdown/semantic)
- search: tipo de busca (vector/text/hybrid_rrf)
- hyde: se HyDE foi aplicado (True/False)
- thr: match_threshold (0–1) aplicado à parcela vetorial; “-” significa sem threshold
- hit@5: razão de consultas cujo “termo esperado” apareceu em algum dos 5 primeiros trechos retornados (proxy de recall no top‑k)
- llm_yes: fração de consultas em que um LLM‑juiz respondeu “sim” à pergunta “os contextos recuperados são suficientes e contêm o conceito esperado?” (proxy de qualidade percebida)

Conceitos de métricas (detalhe):
- hit@k (por exemplo hit@1, hit@5):
  - hit@k = (# consultas em que pelo menos 1 contexto correto aparece entre os k primeiros) / (total de consultas)
  - hit@1 é a taxa de acerto no primeiro resultado (muito relevante em produção, pois resume “acertou de primeira?”)
  - hit@5 mede cobertura (recall) nos 5 primeiros; útil para avaliar candidatos antes de um reranker.
- llm_yes (LLM as a Judge):
  - Um LLM (por padrão “gpt‑4o‑mini”) recebe a pergunta, um “termo esperado” (sinal de avaliação) e os contextos recuperados; responde apenas “sim”/“não”.
  - Vantagem: aproxima a percepção humana (“dá para responder com isso?”). Limitações: custo/latência e alguma variação.

LLM as a Judge nos testes (onde é usado)
- tests/rag/test_experiments_runner.py: roda a matriz (experiments.yaml) e imprime tabela ordenada por llm_yes.
- tests/rag/test_retrieval_eval_llm.py: compara (chunking × search_type) com juiz LLM e imprime tabela.
- tests/rag/test_eval_dataset.py: compara hybrid_rrf vs hybrid_union (empresa e cliente) e usa juiz LLM.
- tests/rag/test_proposal_agent_v2.py: E2E do agente de propostas; o juiz valida se a resposta contempla políticas (ex.: 30/60, 12 meses).

Exemplo prático: medir hit@1 com Rerank (Cohere)
- Pré‑requisito: defina COHERE_API_KEY no `.env`.
- Exemplo (REPL/Python) — comparar top‑1 sem rerank vs com rerank:
```
from app.rag.tools import kb_search_client

q = "Quais as condições de pagamento do Produto A?"

base = kb_search_client.invoke({
    "query": q,
    "empresa": "Empresa X",
    "search_type": "hybrid_rrf",
    "k": 1,
    "reranker": "none",
})
rk = kb_search_client.invoke({
    "query": q,
    "empresa": "Empresa X",
    "search_type": "hybrid_rrf",
    "k": 1,
    "reranker": "cohere",
})

def ok(res, term):
    return bool(res and term.lower() in (res[0]["content"] or "").lower())

print("hit@1 sem rerank:", ok(base, "30/60"))
print("hit@1 com  rerank:", ok(rk,   "30/60"))
```
- Interpretação: se “com rerank” virar True mais vezes que “sem rerank”, houve ganho em hit@1 (acerto no topo).

Interpretação prática:
- chunking impacta fortemente o desempenho; em nosso dataset didático, semantic > markdown >> text‑only.
- thresholds (match_threshold) regulam precisão vs. recall: valores altos cortam ruído, mas derrubam cobertura; valores baixos ampliam cobertura com mais ruído.
- RRF (hybrid_rrf) combina lexical+semântico; melhora recall em muitos cenários. Já o Rerank (Cohere) tende a melhorar hit@1 (ordenação fina) ao custo de latência.
- HyDE é útil quando a consulta é vaga; se a pergunta já é objetiva, pode não trazer ganhos.

Boas práticas:
- Compare sempre múltiplas combinações (não há bala de prata).
- Se o foco for “acerto de primeira”, priorize melhorar hit@1 (ex.: adicionar rerank ou ajustes de prompt/query).
- Se o foco for “não perder evidência”, priorize hit@5 (ex.: thresholds mais baixos e RRF).

## Como rodar (M2)
- Migrações do KB: `python scripts/migrate.py --dir sql/kb`
- Testes RAG (por fases):
  - Fase 0 — staging/materialização do KB: `make rag_phase0`
  - Fase 1 — avaliação semântica (VECTOR only) sobre o KB já materializado: `make rag_phase1`
  - Fase 2 — estratégias de busca/combinações (QA):
    - Runner rápido (tabela na tela): `make rag_phase2_fast`
    - Runner completo (tabela na tela): `make rag_phase2_extra`
    - Salvar CSV/JSON (foreground): `make rag_phase2_save`
    - Salvar CSV/JSON (rápido): `make rag_phase2_save_fast`
    - Salvar CSV/JSON (background/nohup): `make rag_phase2_save_bg`
  - Fase 3 — E2E do agente (melhor combo):
    - Runner rápido (tabela na tela): `make rag_phase3_fast`
    - Runner completo (tabela na tela): `make rag_phase3_extra`
    - Salvar CSV/JSON (foreground): `make rag_phase3_save`
    - Salvar CSV/JSON (rápido): `make rag_phase3_save_fast`
    - Salvar CSV/JSON (background/nohup): `make rag_phase3_save_bg`
  - Completo (todas as fases): `make rag_eval`
  - Nota (Fase 1): imprime "FASE 1 — SEMANTIC QA (VECTOR ONLY)" com sumário por estratégia ([GERAL|EMPRESA|LEAD]) e uma tabela por pergunta mostrando o snippet do chunk top‑1 por estratégia. Usa somente busca vetorial e requer o KB materializado pela Fase 0.
  - Nota (Fase 2): fixa o chunking semantic e compara combinações (vector/text/hybrid_rrf), além de variações HyDE/threshold/rerank definidas em `tests/rag/experiments.yaml`. Usa o mesmo dataset de perguntas da Fase 1 (`tests/rag/rag_queries.yaml`). Para execuções rápidas, defina `RAG_FAST=1` (limita a ~10 perguntas) ou `RAG_MAX_Q=<n>`.
  - Dica: `rag_phase0` limpa o KB (TRUNCATE em `kb_docs` e `kb_chunks`) antes de ingerir, para garantir ambiente limpo.
    `rag_phase0` aceita variáveis: `BASE_DIR`, `EMPRESA`, `CLIENT_ID` (opcional), `STRATEGIES` (ex.: `"fixed markdown semantic"`), `CHUNK_SIZE`, `CHUNK_OVERLAP`, `FIXED_CHUNK_SIZE` (default: 200), `FIXED_CHUNK_OVERLAP` (default: 40), `PATH_PREFIX`, `NO_MIGRATE=1`.
    - Estratégias de chunking (sem fallback):
      - `fixed`: respeita `FIXED_CHUNK_SIZE/FIXED_CHUNK_OVERLAP`.
      - `markdown`: usa cortes por cabeçalhos (`MarkdownHeaderTextSplitter`).
      - `semantic`: usa `SemanticChunker` (requer pacotes acima e embeddings); se indisponível, use `markdown`/`fixed` no `rag_ingest`.
- Studio (grafo `rag_ingest`): para materializar múltiplas estratégias em uma rodada, passe `strategies` como lista e, opcionalmente, `chunk_size`/`chunk_overlap`. Exemplo de inputs (requer `langchain-text-splitters>=0.3.9` para `semantic`):
    - `empresa`: "Empresa X"
    - `strategies`: ["fixed", "markdown", "semantic"]
    - `chunk_size`: 400
    - `chunk_overlap`: 80
    - Para silenciar logs de migração em execuções do Phase 0: defina `MIGRATE_QUIET=1`.

Dataset de perguntas (Fases 1 e 2)
- Arquivo: `tests/rag/rag_queries.yaml`
- Formato de cada entrada:
  - `group`: `empresa` ou `lead`
  - `empresa`: `Empresa X` ou `Empresa Y`
  - `pergunta`: texto da pergunta
  - `expected`: termo esperado (string), ou
  - `expected_all`: lista de termos que devem aparecer juntos (usada para perguntas mais complexas)
- Os testes usam este dataset para comparar estratégias de chunking (Fase 1) e combinações de busca (Fase 2). Campo opcional `answer` pode ser preenchido para orientar o juiz LLM; na ausência, os campos `expected`/`expected_all` são usados para a checagem/julgamento.

Reranker (Cohere) — Limites de Taxa e Boas Práticas
- O reranker via Cohere é opcional e requer `COHERE_API_KEY` e o pacote `langchain-cohere`.
- Chaves Trial da Cohere possuem limite típico de 10 chamadas/minuto. Em execuções completas (Phase 2 extra), é comum atingir `429 TooManyRequests`.
- Comportamento no projeto:
  - Runner de experimentos (Phase 2): quando ocorre 429, apenas o experimento com `reranker=cohere` é pulado e impresso como `[SKIP] ... rate-limited (429)`. Os demais experimentos seguem normalmente.
  - Teste de smoke do rerank (`tests/rag/test_rerank.py`): em 429 o teste é marcado como `skip` para não derrubar a suíte.
- Dicas para evitar 429:
  - Use `make rag_phase2_fast` (ou `RAG_MAX_Q=<n>`) para reduzir o número de consultas.
  - Limite temporariamente os experimentos com `reranker=cohere` no `tests/rag/experiments.yaml`.
  - Reduza `rerank_candidates` nos experimentos.
  - Considere atualizar a chave para um plano com limites mais altos.

Top‑K de busca e pool de candidatos
- A tool `kb_search_client` retorna os top‑`k` chunks (padrão `k=5`).
- Quando `reranker` é usado, a tool pode buscar um pool maior antes de ordenar; isso é controlado por `rerank_candidates` (padrão `24`).
- Definições no código:
  - `app/rag/tools.py:kb_search_client` — parâmetros `k` (default 5) e `rerank_candidates` (default 24).
  - SQL aplica `limit p_k` em `sql/kb/03_functions.sql` nas funções `kb_vector_search`, `kb_text_search`, `kb_hybrid_search`, `kb_hybrid_union`.

Exemplos Phase 0 (ajustes de chunk)
- Rodar com defaults (AUTO, usa tests/rag/data/*):
  - `make rag_phase0`
- Alterar apenas o fixed (200/40 → ex.: 180/36):
- `make rag_phase0 FIXED_CHUNK_SIZE=180 FIXED_CHUNK_OVERLAP=36`
- Alterar apenas o tamanho geral (markdown/semantic) mantendo fixed=200/40:
  - `make rag_phase0 CHUNK_SIZE=480 CHUNK_OVERLAP=96`
- Empresa única a partir de outro diretório:
  - `make rag_phase0 BASE_DIR=kb EMPRESA="Empresa Z"`
- Silenciar logs de migração:
  - `MIGRATE_QUIET=1 make rag_phase0`

 

Resolução de Problemas (Semantic Chunking)
- Erro: “SemanticChunker não está disponível no ambiente”
  - Instale um dos pacotes: `pip install -U langchain-experimental>=0.3.4` ou `pip install -U langchain-text-splitters>=0.3.8`
  - Verifique `OPENAI_API_KEY` no `.env`
  - Relembre: não há fallback; se não quiser semantic, remova `semantic` de `STRATEGIES` no Phase 0 (ex.: `STRATEGIES="fixed markdown"`)
- Erro: “Estratégia de chunking inválida/não informada”
  - Use uma das estratégias suportadas: `fixed`, `markdown`, `semantic`
    - Sem `EMPRESA`, o comando entra em modo AUTO: varre subpastas de `BASE_DIR` e usa o nome da pasta como empresa (ex.: `tests/rag/data/empresa_x` → `Empresa X`).
    - Ex.: `make rag_phase0` (AUTO em `tests/rag/data`), ou `make rag_phase0 BASE_DIR=kb EMPRESA="Empresa X" STRATEGIES="fixed markdown semantic"` (empresa única).
- Execuções longas em background (nohup):
  - Para encerrar, use: `kill $(cat tests/rag/analysis/<nome>.pid)`
- Guia prático do flow (chunking → combinações → agente): `docs/rag_testing_flow.md`
- Template de matriz completa: `tests/rag/experiments.template.yaml`
- Template por fases (copiar/colar): `tests/rag/experiments.flow.example.yaml`

Notas sobre execuções longas (experimentos)
- Em background, o arquivo `*.nohup.log` pode ficar vazio até o fim. Os resultados `*_results.csv/json` são gravados ao finalizar.
- Studio: `langgraph dev` e selecione `proposal_agent_v2` ou `rag_ingest`

## Grafos registrados (langgraph.json)
- workflow (M1) — `app/agent/workflow.py:graph`
- proposal_agent_v2 (M2) — `app/rag/proposal_agent_v2.py:graph`
- rag_ingest (M2) — `app/rag/ingest.py:graph`

### Grafo rag_ingest (Ingestão)
- Objetivo: pipeline simples em 2 nós (stage → chunks) para materializar um KB a partir de arquivos `.md`.
- Base dir padrão (grafo): `kb`.
  - O runner da Fase 0 (`scripts/rag_phase0.py`) usa por padrão `tests/rag/data` e já executa TRUNCATE; o grafo `rag_ingest` não faz TRUNCATE.
- Stage (kb_docs): lê todos os `.md` do `base_dir` e insere 1 linha por arquivo em `kb_docs`.
  - Idempotência: `ON CONFLICT (source_path, source_hash) DO NOTHING` (evita duplicar a mesma versão do arquivo).
- Chunks (kb_chunks): lê do staging filtrando por `empresa/client_id`, divide o conteúdo e grava em `kb_chunks`.
  - Chunking padrão do grafo: `semantic` (pode definir `strategy`= `fixed` | `markdown` | `semantic`).
  - Embeddings: `text-embedding-3-small`.
  - Upsert: `ON CONFLICT (doc_path, chunk_ix) DO UPDATE` (atualiza o mesmo par doc/chunk).
  - Uma execução → uma estratégia (o grafo não aplica múltiplas estratégias de uma vez).
- Flags do estado do grafo: `base_dir`, `strategy`, `empresa`, `client_id`, `skip_stage`, `skip_chunks`.
- Para múltiplas estratégias e ambiente limpo (TRUNCATE + prefixo por estratégia), use `scripts/rag_phase0.py`.

## Módulo 1 — Orquestração Multi‑Intents (resumo)
- Grafo principal em `app/agent/workflow.py` com nós comentados (parse/plan/route/execute/finalize)
- Subgrafos ReAct (leads/propostas), intents e tools do Mini‑CRM
- Testes: `tests/` (tools, intents, roteamento, multi‑intents)

## Makefile (comandos úteis)
- Database: `make db_init`, `make db_apply`, `make db_seed`, `make db_truncate[_yes]`
- Testes M1: `make test_tools`, `make test_quick`, `make test_multi`, `make test_pytest`
- Testes M2 (por fases): `make rag_phase1`, `make rag_phase2_fast`/`make rag_phase2_extra`, `make rag_phase3_fast`/`make rag_phase3_extra` (ou `make rag_eval` para tudo)

Observação: os alvos de experimento utilizam `PYTHONPATH=.` para garantir import do pacote a partir da raiz do projeto.

## Observações e Boas Práticas
- Filtros obrigatórios na tool de busca (client_id > empresa; sem filtro → erro lógico) — evita vazamento entre clientes/tenants
- Preferir chunking semantic/markdown a fixed; demonstre em aula com as tabelas de comparação
- RRF no banco melhora a fusão lex.+semântico; Rerank (Cohere) refina o topo — teste ambos (não há bala de prata)
- Comentários e docstrings em português; simplicidade > abstração; foco em entendimento humano
