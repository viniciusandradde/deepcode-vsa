"""Planning Agent for NotebookLM-like document analysis and project planning."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


# =============================================================================
# Prompts
# =============================================================================

PLANNING_ANALYSIS_PROMPT = """Você é um Especialista Sênior em Planejamento de Projetos de TI.
Sua função é analisar documentos e gerar planos de projeto estruturados seguindo metodologias ITIL e PMI.

## Contexto
Você receberá documentos de um projeto e deve analisar com foco em: {focus_area}

## Documentos do Projeto
{context}

## Instruções
1. Analise cuidadosamente todos os documentos fornecidos
2. Extraia informações relevantes para planejamento
3. Identifique riscos, requisitos, dependências e custos
4. Sugira etapas/fases realistas com estimativas de tempo
5. Proponha itens de orçamento baseados no conteúdo

## Formato de Saída (JSON obrigatório)
Retorne APENAS um JSON válido, sem texto antes ou depois:

{{
    "executive_summary": "Resumo executivo em 3-5 frases",
    "critical_points": [
        "Ponto crítico 1 relacionado ao foco ({focus_area})",
        "Ponto crítico 2"
    ],
    "suggested_stages": [
        {{
            "title": "Nome da Etapa",
            "description": "Descrição breve",
            "estimated_days": 14
        }}
    ],
    "suggested_budget": [
        {{
            "category": "infra|pessoal|licencas|hardware|software|servicos",
            "description": "Descrição do item",
            "estimated_cost": 1500.00
        }}
    ],
    "risks": [
        "Risco identificado 1",
        "Risco identificado 2"
    ],
    "recommendations": [
        "Recomendação 1",
        "Recomendação 2"
    ]
}}

## Regras
- Retorne APENAS o JSON, sem markdown ou texto adicional
- Use valores numéricos para estimated_days e estimated_cost (não strings)
- Categoria de orçamento deve ser uma das: infra, pessoal, licencas, hardware, software, servicos
- Seja realista nas estimativas de tempo e custo
- Se não houver informação suficiente, indique nos riscos
"""


# =============================================================================
# Model Selection
# =============================================================================

def choose_model_for_context(token_count: int) -> str:
    """Choose appropriate model based on context size.
    
    Args:
        token_count: Estimated token count of the context
        
    Returns:
        Model identifier
    """
    if token_count < 100_000:
        return "google/gemini-2.5-flash"  # Fast, cheap
    elif token_count < 500_000:
        return "google/gemini-1.5-flash"  # Balanced
    else:
        return "google/gemini-1.5-pro"    # Long context (2M tokens)


def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars per token average)."""
    return len(text) // 4


# =============================================================================
# Planning Agent
# =============================================================================

class PlanningAgent:
    """Agent for analyzing documents and generating project plans."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        openrouter_api_key: Optional[str] = None,
    ):
        """Initialize the planning agent.
        
        Args:
            model_name: Specific model to use (None = auto-select based on context)
            temperature: Model temperature (lower = more deterministic)
            openrouter_api_key: OpenRouter API key (or from env)
        """
        self.api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY required")
        
        self.default_model = model_name
        self.temperature = temperature
        self._model_cache: Dict[str, ChatOpenAI] = {}
    
    def _get_model(self, model_name: str) -> ChatOpenAI:
        """Get or create model instance."""
        if model_name not in self._model_cache:
            self._model_cache[model_name] = ChatOpenAI(
                model=model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
                openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            )
        return self._model_cache[model_name]
    
    async def analyze_documents(
        self,
        documents_context: str,
        focus_area: str = "Geral",
    ) -> Dict[str, Any]:
        """Analyze project documents and generate planning insights.
        
        Args:
            documents_context: Combined text from all project documents
            focus_area: Analysis focus (Geral, Riscos, Cronograma, Custos, etc.)
            
        Returns:
            Analysis result with suggested stages, budget, risks, etc.
        """
        if not documents_context.strip():
            return {
                "executive_summary": "Nenhum documento fornecido para análise.",
                "critical_points": ["Faça upload de documentos para análise"],
                "suggested_stages": [],
                "suggested_budget": [],
                "risks": ["Sem documentação disponível"],
                "recommendations": ["Adicione documentos ao projeto"],
                "tokens_used": 0,
                "model_used": None,
            }
        
        # Estimate tokens and choose model
        token_estimate = estimate_tokens(documents_context)
        model_name = self.default_model or choose_model_for_context(token_estimate)
        
        logger.info(
            f"Planning analysis: ~{token_estimate} tokens, using model {model_name}"
        )
        
        # Build prompt
        prompt = PLANNING_ANALYSIS_PROMPT.format(
            focus_area=focus_area,
            context=documents_context,
        )
        
        # Call model
        model = self._get_model(model_name)
        
        try:
            response = await model.ainvoke([
                SystemMessage(content="Você é um assistente de planejamento de projetos. Responda APENAS em JSON válido."),
                HumanMessage(content=prompt),
            ])
            
            # Parse JSON response
            content = response.content.strip()
            
            # Handle markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])  # Remove first and last lines
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}. Raw response: {content[:500]}")
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {
                        "executive_summary": content[:500],
                        "critical_points": ["Erro ao processar resposta do modelo"],
                        "suggested_stages": [],
                        "suggested_budget": [],
                        "risks": ["Resposta do modelo não foi em formato JSON esperado"],
                        "recommendations": [],
                    }
            
            # Add metadata
            result["tokens_used"] = token_estimate
            result["model_used"] = model_name
            
            return result
            
        except Exception as e:
            logger.error(f"Planning analysis failed: {e}", exc_info=True)
            return {
                "executive_summary": f"Erro na análise: {str(e)}",
                "critical_points": ["Falha na análise de documentos"],
                "suggested_stages": [],
                "suggested_budget": [],
                "risks": [f"Erro técnico: {str(e)}"],
                "recommendations": ["Tente novamente ou reduza o tamanho dos documentos"],
                "tokens_used": token_estimate,
                "model_used": model_name,
            }


# =============================================================================
# Factory Function
# =============================================================================

_agent_instance: Optional[PlanningAgent] = None


def get_planning_agent() -> PlanningAgent:
    """Get or create singleton planning agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PlanningAgent()
    return _agent_instance


async def analyze_project_documents(
    documents_context: str,
    focus_area: str = "Geral",
) -> Dict[str, Any]:
    """Convenience function to analyze documents.
    
    Args:
        documents_context: Combined text from all project documents
        focus_area: Analysis focus
        
    Returns:
        Analysis result
    """
    agent = get_planning_agent()
    return await agent.analyze_documents(documents_context, focus_area)
