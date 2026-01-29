"""ITIL block formatters: classification header to markdown."""

from typing import Optional

PRIORITY_LABELS = {
    "critico": "CRÍTICO",
    "alto": "ALTO",
    "medio": "MÉDIO",
    "baixo": "BAIXO",
}


def format_itil_classification_block(
    category: str,
    gut_score: int,
    priority: str,
    gut_details: Optional[dict] = None,
) -> str:
    """Formata bloco de classificação ITIL (tabela markdown)."""
    priority_upper = PRIORITY_LABELS.get(priority.lower(), priority.upper())
    g = u = t = "?"
    if gut_details:
        g = gut_details.get("gravidade", "?")
        u = gut_details.get("urgencia", "?")
        t = gut_details.get("tendencia", "?")

    return f"""### Classificação ITIL

| Campo      | Valor        |
|------------|--------------|
| Tipo       | {category.upper()} |
| GUT Score  | {gut_score} (G×U×T: {g}×{u}×{t}) |
| Prioridade | {priority_upper} |
"""
