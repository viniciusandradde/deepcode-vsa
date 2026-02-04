"""
Agente de Propostas (v2) — versão de teste isolada (somente RAG):
- Sem ferramentas do CRM; foca em recuperar informações dinamicamente do KB.
- Exponha uma ferramenta de busca do KB com chunking fixo (didático). O único parâmetro variável é o `match_threshold`.
- O agente pode ajustar `match_threshold` on‑the‑fly conforme a necessidade de recall/precisão.
"""

from langchain_openai import ChatOpenAI
import os

from app.agent.new_react import create_react_executor
from app.rag.tools import kb_search_client


def build_model():
    return ChatOpenAI(
        model=os.getenv("PROPOSAL_LLM_MODEL", "gpt-5-nano"),
        output_version="responses/v1",
        reasoning={"effort": "high"},
        verbosity="medium",
    )


def defaults_kb() -> dict:
    return {
        "search_type": "hybrid_rrf",
        "chunking": "semantic",
        "use_hyde": False,
        "reranker": "none",
        "match_threshold": 0.5,
        "rerank_candidates": None,
    }


def system_prompt() -> str:
    d = defaults_kb()
    thr = d.get("match_threshold")
    return (
        "Você é um agente de propostas focado em RAG (recuperação aumentada).\n"
        "- Use a ferramenta agent_kb_search para recuperar contexto.\n"
        "- Por padrão (didático), utilize os seguintes parâmetros nas chamadas (apenas ajuste match_threshold se necessário):\n"
        f"  • search_type={d['search_type']}\n"
        f"  • chunking fixo={d['chunking']} (já aplicado pela ferramenta).\n"
        f"  • match_threshold inicial {thr}; ajuste dinamicamente (↓ para ↑cobertura, ↑ para ↓ruído).\n"
        f"  • reranker={d['reranker']}\n"
        "- Chame a ferramenta quantas vezes forem necessárias até ter evidências suficientes.\n"
        "- Construa a resposta final apenas com base nas evidências recuperadas; não invente.\n"
        "\n"
        "Orientações para maximizar objetividade e aprovação do juiz:\n"
        "- Quando a pergunta pedir um valor objetivo (ex.: SLA, canal prioritário, janela de manutenção, pagamento, garantia), responda DIRETAMENTE com UM valor.\n"
        "- Se houver variações por empresa (X/Y) e a pergunta não especificar, assuma Empresa X como padrão e declare isso de forma concisa (Assunção: Empresa X). Em seguida, inclua uma nota curta com a alternativa: ‘Se for Empresa Y: <valor>’.\n"
        "- Evite devolver perguntas como resposta principal. Se precisar pedir esclarecimento, primeiro responda com a melhor evidência e só depois ofereça esclarecer.\n"
        "- Reproduza termos exatamente como no KB (por exemplo: ‘30/60’, ‘12 meses’, ‘99.9%’, ‘portal do cliente’).\n"
        "- Cite fontes do KB (doc_path#chunk_ix) para cada afirmação chave, no formato: ‘… [arquivo.md#12]’.\n"
        "- Se a evidência estiver insuficiente, reduza temporariamente o match_threshold e tente nova busca; se ainda assim faltar base, declare objetivamente que não há evidência suficiente no KB."
    )


def build_agent_kb_tool():
    """Tool fina com chunking fixo; apenas match_threshold é variável (didático)."""
    from langchain_core.tools import tool

    defaults = defaults_kb()
    fixed_chunking = defaults["chunking"]
    fixed_search = defaults["search_type"]
    fixed_reranker = defaults["reranker"]

    @tool
    def agent_kb_search(query: str, k: int = 5, match_threshold: float | None = None):
        """Busca no KB com chunking fixo e threshold ajustável.

        Parâmetros:
        - query: pergunta do usuário
        - k: top-K a retornar (default 5)
        - match_threshold: limiar de similaridade (float opcional)
        """
        args = {
            "query": query,
            "k": k,
            "search_type": fixed_search,
            "chunking": fixed_chunking,
            "reranker": fixed_reranker,
            "use_hyde": False,
        }
        if match_threshold is not None:
            try:
                args["match_threshold"] = float(match_threshold)
            except Exception:
                pass
        return kb_search_client.invoke(args)

    return agent_kb_search


def build_graph():
    tools = [build_agent_kb_tool()]
    graph = create_react_executor(
        build_model(),
        tools=tools,
        prompt=system_prompt(),
    )
    return graph


graph = build_graph()
