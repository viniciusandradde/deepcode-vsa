"""Web search tools using Tavily."""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch


load_dotenv()


@tool
def tavily_search(
    query: str,
    max_results: int = 5,
    include_raw_content: bool = False,
) -> str:
    """Busca conteúdo na Internet com Tavily.

    Parâmetros:
    - query: texto da pesquisa.
    - max_results: quantidade máxima de resultados retornados.
    - include_raw_content: quando True, inclui conteúdo bruto das páginas.

    Retorno:
    - string JSON com os resultados (ou string simples em fallback).
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("Defina TAVILY_API_KEY para usar tavily_search.")

    client = TavilySearch(
        api_key=api_key,
        max_results=max_results,
        topic="general",
        include_raw_content=include_raw_content,
    )
    result = client.invoke(input=query)
    try:
        return json.dumps(result)
    except Exception:
        return str(result)

