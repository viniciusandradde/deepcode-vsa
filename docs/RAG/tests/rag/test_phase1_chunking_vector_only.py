from pathlib import Path
import uuid
import pytest

# Fase 1 — comparação de chunking usando apenas busca vetorial
pytestmark = pytest.mark.phase0


def test_phase1_chunking_vector_only(tmp_path: Path, db_ready, require_openai):
    """Compara fixed vs markdown vs semantic (VECTOR only).

    Objetivo didático da Fase 1: o aluno deve conseguir ver rapidamente
    como o chunking impacta a recuperação vetorial (sem híbridos, sem juiz LLM).
    """
    from app.rag.ingest import stage_docs_from_dir, materialize_chunks_from_staging
    from app.rag.tools import kb_search_client

    # Constrói um mini‑KB para Empresa X e Empresa Y (ruído)
    kb = tmp_path / "kb"
    # Cria três cópias do conteúdo (por estratégia) para evitar conflitos de (doc_path, chunk_ix)
    (kb / "x_fixed").mkdir(parents=True)
    (kb / "x_markdown").mkdir(parents=True)
    (kb / "x_semantic").mkdir(parents=True)
    (kb / "y_fixed").mkdir(parents=True)
    (kb / "y_markdown").mkdir(parents=True)
    (kb / "y_semantic").mkdir(parents=True)

    def _w(p, txt):
        p.write_text(txt.strip(), encoding="utf-8")

    _w(kb / "x_fixed" / "produto_a.md",
        """
# Produto A — Políticas (Empresa X)
Garantia padrão de 12 meses. Pagamento parcelado em 30/60 dias.
"""
    )
    _w(kb / "x_markdown" / "produto_a.md",
        """
# Produto A — Políticas (Empresa X)
Garantia padrão de 12 meses. Pagamento parcelado em 30/60 dias.
"""
    )
    _w(kb / "x_semantic" / "produto_a.md",
        """
# Produto A — Políticas (Empresa X)
Garantia padrão de 12 meses. Pagamento parcelado em 30/60 dias.
"""
    )

    _w(kb / "x_fixed" / "servico_b.md",
        """
# Serviço B — SLA (Empresa X)
O SLA alvo é de 99.9% de disponibilidade mensal.
"""
    )
    _w(kb / "x_markdown" / "servico_b.md",
        """
# Serviço B — SLA (Empresa X)
O SLA alvo é de 99.9% de disponibilidade mensal.
"""
    )
    _w(kb / "x_semantic" / "servico_b.md",
        """
# Serviço B — SLA (Empresa X)
O SLA alvo é de 99.9% de disponibilidade mensal.
"""
    )

    _w(kb / "x_fixed" / "cancelamento.md",
        """
# Políticas de Cancelamento (Empresa X)
Cancelamento permitido em até 7 dias úteis após assinatura.
"""
    )
    _w(kb / "x_markdown" / "cancelamento.md",
        """
# Políticas de Cancelamento (Empresa X)
Cancelamento permitido em até 7 dias úteis após assinatura.
"""
    )
    _w(kb / "x_semantic" / "cancelamento.md",
        """
# Políticas de Cancelamento (Empresa X)
Cancelamento permitido em até 7 dias úteis após assinatura.
"""
    )

    _w(kb / "x_fixed" / "financeiro.md",
        """
# Condições Financeiras (Empresa X)
Desconto à vista de 5%. Parcelamento em 30/60/90 dias para pedidos acima de R$ 10.000.
"""
    )
    _w(kb / "x_markdown" / "financeiro.md",
        """
# Condições Financeiras (Empresa X)
Desconto à vista de 5%. Parcelamento em 30/60/90 dias para pedidos acima de R$ 10.000.
"""
    )
    _w(kb / "x_semantic" / "financeiro.md",
        """
# Condições Financeiras (Empresa X)
Desconto à vista de 5%. Parcelamento em 30/60/90 dias para pedidos acima de R$ 10.000.
"""
    )

    _w(kb / "x_fixed" / "suporte.md",
        """
# Suporte e Atendimento (Empresa X)
Suporte 24/7 por chat e e-mail. Tempo alvo de primeira resposta: 2 horas.
"""
    )
    _w(kb / "x_markdown" / "suporte.md",
        """
# Suporte e Atendimento (Empresa X)
Suporte 24/7 por chat e e-mail. Tempo alvo de primeira resposta: 2 horas.
"""
    )
    _w(kb / "x_semantic" / "suporte.md",
        """
# Suporte e Atendimento (Empresa X)
Suporte 24/7 por chat e e-mail. Tempo alvo de primeira resposta: 2 horas.
"""
    )

    _w(kb / "x_fixed" / "implantacao.md",
        """
# Implantação (Empresa X)
Prazo de implementação típico: 5 dias úteis. Oferecemos treinamento remoto.
"""
    )
    _w(kb / "x_markdown" / "implantacao.md",
        """
# Implantação (Empresa X)
Prazo de implementação típico: 5 dias úteis. Oferecemos treinamento remoto.
"""
    )
    _w(kb / "x_semantic" / "implantacao.md",
        """
# Implantação (Empresa X)
Prazo de implementação típico: 5 dias úteis. Oferecemos treinamento remoto.
"""
    )

    _w(kb / "x_fixed" / "troca.md",
        """
# Políticas de Troca (Empresa X)
Troca permitida em até 30 dias corridos com nota fiscal.
"""
    )
    _w(kb / "x_markdown" / "troca.md",
        """
# Políticas de Troca (Empresa X)
Troca permitida em até 30 dias corridos com nota fiscal.
"""
    )
    _w(kb / "x_semantic" / "troca.md",
        """
# Políticas de Troca (Empresa X)
Troca permitida em até 30 dias corridos com nota fiscal.
"""
    )

    _w(kb / "x_fixed" / "seguranca.md",
        """
# Segurança e Conformidade (Empresa X)
Criptografia em repouso AES-256. Backups diários por 30 dias.
"""
    )
    _w(kb / "x_markdown" / "seguranca.md",
        """
# Segurança e Conformidade (Empresa X)
Criptografia em repouso AES-256. Backups diários por 30 dias.
"""
    )
    _w(kb / "x_semantic" / "seguranca.md",
        """
# Segurança e Conformidade (Empresa X)
Criptografia em repouso AES-256. Backups diários por 30 dias.
"""
    )
    # Empresa Y (ruído)
    _w(kb / "y_fixed" / "produto_a.md",
        """
# Produto A — Políticas (Empresa Y)
Não há menção à garantia de 12 meses ou parcelamento 30/60.
"""
    )
    _w(kb / "y_markdown" / "produto_a.md",
        """
# Produto A — Políticas (Empresa Y)
Não há menção à garantia de 12 meses ou parcelamento 30/60.
"""
    )
    _w(kb / "y_semantic" / "produto_a.md",
        """
# Produto A — Políticas (Empresa Y)
Não há menção à garantia de 12 meses ou parcelamento 30/60.
"""
    )
    _w(kb / "y_fixed" / "financeiro.md",
        """
# Condições Financeiras (Empresa Y)
Sem menção a desconto à vista ou parcelamentos 30/60/90.
"""
    )
    _w(kb / "y_markdown" / "financeiro.md",
        """
# Condições Financeiras (Empresa Y)
Sem menção a desconto à vista ou parcelamentos 30/60/90.
"""
    )
    _w(kb / "y_semantic" / "financeiro.md",
        """
# Condições Financeiras (Empresa Y)
Sem menção a desconto à vista ou parcelamentos 30/60/90.
"""
    )
    _w(kb / "y_fixed" / "suporte.md",
        """
# Suporte e Atendimento (Empresa Y)
Atendimento em horário comercial.
"""
    )
    _w(kb / "y_markdown" / "suporte.md",
        """
# Suporte e Atendimento (Empresa Y)
Atendimento em horário comercial.
"""
    )
    _w(kb / "y_semantic" / "suporte.md",
        """
# Suporte e Atendimento (Empresa Y)
Atendimento em horário comercial.
"""
    )

    # Isola por empresa única para evitar interferência de execuções anteriores
    empresa = f"Empresa X {str(uuid.uuid4())[:8]}"
    empresa_y = f"Empresa Y {str(uuid.uuid4())[:8]}"

    # 1) Staging: simula mundo real — uma única base por empresa
    #    (usamos apenas o conteúdo semântico como base; os três dirs X_* têm o mesmo conteúdo)
    stage_docs_from_dir(str(kb / "x_markdown"), empresa=empresa)
    stage_docs_from_dir(str(kb / "y_markdown"), empresa=empresa_y)

    # 2) Materializa chunks por estratégia a partir do MESMO staging (empresa base), mas escreve
    #    em empresas diferentes para comparação limpa (sem colisão por doc_path,chunk_ix)
    # Materializa todas as estratégias na MESMA empresa base, diferenciando por meta.chunking e doc_path_prefix
    materialize_chunks_from_staging(strategy="fixed", empresa=empresa, doc_path_prefix="fixed")
    materialize_chunks_from_staging(strategy="markdown", empresa=empresa, doc_path_prefix="markdown")
    materialize_chunks_from_staging(strategy="semantic", empresa=empresa, doc_path_prefix="semantic")

    # Consultas e “gabaritos” (palavras‑chave esperadas)
    cases = [
        ("Qual a garantia do Produto A?", "12 meses"),
        ("Quais as condições de pagamento do Produto A?", "30/60"),
        ("Qual o parcelamento máximo oferecido?", "90"),
        ("Existe desconto à vista?", "5%"),
        ("O suporte é 24/7?", "24/7"),
        ("Qual o tempo de primeira resposta?", "2 horas"),
        ("Qual o prazo de implementação?", "5 dias úteis"),
        ("Há treinamento remoto?", "treinamento remoto"),
        ("Qual a política de cancelamento?", "7 dias"),
        ("Qual a política de troca?", "30 dias"),
        ("Como é a criptografia em repouso?", "AES-256"),
        ("Backups são mantidos por quanto tempo?", "30 dias"),
        ("Qual o SLA do Serviço B?", "99.9%"),
    ]

    strategies = (
        ("fixed", empresa),
        ("markdown", empresa),
        ("semantic", empresa),
    )
    results = []
    # Feedback por pergunta (hit@1) para cada chunking
    feedback = []
    total = len(cases)
    for chunking, empresa_lookup in strategies:
        hits5 = 0
        hits1 = 0
        per_q = []  # guardará (ok1, doc#chunk, content_snippet)
        for q, expected in cases:
            res = kb_search_client.invoke({
                "query": q,
                "k": 5,
                "search_type": "vector",
                "reranker": "none",
                "empresa": empresa_lookup,
                "chunking": chunking,
            })
            norm = expected.lower()
            got5 = any(norm in (it["content"] or "").lower() for it in res)
            got1 = False
            docloc = "-"
            snippet = ""
            if res:
                top = res[0]
                c = (top["content"] or "")
                got1 = norm in c.lower()
                # formata doc:chunk
                from pathlib import Path as _P
                docloc = f"{_P(top['doc_path']).name}:{top['chunk_ix']}"
                snippet = c[:80].replace("\n", " ")
            hits5 += 1 if got5 else 0
            hits1 += 1 if got1 else 0
            per_q.append((got1, docloc, snippet))
        results.append((chunking, hits5 / total, hits1 / total))
        feedback.append((chunking, per_q))

    print("\n=== FASE 1 — COMPARAÇÃO DE CHUNKING (VECTOR ONLY) ===")
    print("chunking  | hit@5 | hit@1")
    print("-" * 34)
    for chunking, hit5, hit1 in results:
        print(f"{chunking:8s}| {hit5:5.2f} | {hit1:5.2f}")

    # Assegura que ao menos uma estratégia funciona razoavelmente
    assert any(hit5 >= 0.5 for _, hit5, _ in results), "Nenhuma estratégia atingiu 50% de acerto em VECTOR"

    # Feedback por pergunta (hit@1) por chunking
    print("\n=== FASE 1 — FEEDBACK POR PERGUNTA (hit@1 por chunking) ===")
    print("ix | pergunta                               | esperado        | fixed        | markdown     | semantic     ")
    print("-" * 106)
    # reorganiza feedback por pergunta (linhas) e chunking (colunas)
    # feedback = [(chunking, [(ok1, docloc, snippet), ...])]
    per_question_rows = []
    for i, (q, expected) in enumerate(cases, start=1):
        row = {"ix": i, "q": q, "expected": expected, "fixed": (False, "-", ""), "markdown": (False, "-", ""), "semantic": (False, "-", "")}
        for chunking, per_q in feedback:
            ok1, docloc, snippet = per_q[i - 1]
            row[chunking] = (ok1, docloc, snippet)
        per_question_rows.append(row)

    def _cell(val):
        ok, docloc, _snip = val
        return ("OK" if ok else " X") + f" {docloc:12s}"

    for row in per_question_rows:
        qshort = (row["q"][:35] + "…") if len(row["q"]) > 35 else row["q"]
        exps = (row["expected"][:14] + "…") if len(row["expected"]) > 14 else row["expected"]
        print(f"{row['ix']:>2d} | {qshort:35s} | {exps:14s} | {_cell(row['fixed'])} | {_cell(row['markdown'])} | {_cell(row['semantic'])}")

    # Debug opcional: imprime contagens por empresa/chunking para confirmar materialização
    try:
        import psycopg
        with psycopg.connect(db_ready) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select coalesce(empresa,'<null>') as empresa, meta->>'chunking' as chunking, count(*)\n"
                    "from public.kb_chunks where lower(empresa)=lower(%s) group by 1,2 order by 1,2",
                    (empresa,),
                )
                rows = cur.fetchall() or []
                print("\n[DEBUG] kb_chunks por empresa/chunking:")
                for emp, strat, c in rows:
                    print(f"  {emp} | {strat} -> {c}")
    except Exception:
        pass
