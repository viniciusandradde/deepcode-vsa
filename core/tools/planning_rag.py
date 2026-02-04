"""RAG tool for project-scoped knowledge search (DeepCode Projects)."""

from langchain_core.tools import tool

from core.rag.tools import kb_search_client


@tool
def search_project_knowledge(query: str, project_id: str) -> str:
    """
    Consulta a base de conhecimento do PROJETO ATUAL.
    Use para responder perguntas sobre especificações, riscos, arquitetura
    ou detalhes técnicos contidos nos arquivos do projeto.

    Args:
        query: Pergunta ou termos de busca.
        project_id: ID do projeto (UUID).
    """
    try:
        results = kb_search_client.invoke({
            "query": query,
            "project_id": project_id,
            "k": 7,
            "search_type": "hybrid",
            "reranker": "none",
        })

        if not results:
            return "Nenhuma informação encontrada nos documentos do projeto."

        context = "\n\n".join([
            f"[Fonte: {r.get('meta', {}).get('file', 'N/A')}]\n{r['content']}"
            for r in results
        ])
        return f"Contexto recuperado do projeto:\n{context}"

    except Exception as e:
        return f"Erro na busca: {str(e)}"
