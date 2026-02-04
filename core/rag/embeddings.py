"""Embedding model factory for RAG (model-agnostic)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings


OPENAI_MODEL_ID = "openai"
OPENAI_MODEL_NAME = "OpenAI Cloud (Rápido)"
OPENAI_MODEL_DIMS = 1536
OPENAI_DEFAULT_MODEL = "text-embedding-3-small"

BGE_M3_MODEL_ID = "bge-m3"
BGE_M3_MODEL_NAME = "BGE-M3 Local (Privado)"
BGE_M3_MODEL_DIMS = 1024
BGE_M3_MODEL_REPO = "BAAI/bge-m3"


def _validate_openai_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "RAG embeddings requer OPENAI_API_KEY (chave da OpenAI para api.openai.com). "
            "Chaves do OpenRouter (sk-or-...) não funcionam no endpoint de embeddings."
        )
    if api_key.startswith("sk-or-"):
        raise RuntimeError(
            "RAG embeddings requer uma chave da OpenAI (OPENAI_API_KEY), não do OpenRouter. "
            "Chaves sk-or-... são do OpenRouter e não funcionam em api.openai.com/embeddings. "
            "Defina OPENAI_API_KEY com uma chave de https://platform.openai.com/api-keys"
        )
    return api_key


def _bge_available() -> bool:
    try:
        import langchain_huggingface  # noqa: F401
    except ImportError:
        return False
    return True


class EmbeddingFactory:
    """Factory for embedding models with lazy loading."""

    @classmethod
    @lru_cache(maxsize=None)
    def get_model(cls, model_id: str) -> Embeddings:
        model_id = (model_id or "").strip().lower()
        if not model_id:
            model_id = OPENAI_MODEL_ID

        if model_id == OPENAI_MODEL_ID:
            api_key = _validate_openai_key()
            return OpenAIEmbeddings(model=OPENAI_DEFAULT_MODEL, openai_api_key=api_key)

        if model_id == BGE_M3_MODEL_ID:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError as e:
                raise RuntimeError(
                    "bge-m3 requer langchain_huggingface; não disponível neste ambiente"
                ) from e
            return HuggingFaceEmbeddings(model_name=BGE_M3_MODEL_REPO)

        raise RuntimeError(f"Embedding model não suportado: {model_id}")

    @classmethod
    def list_models(cls) -> List[Dict[str, object]]:
        models: List[Dict[str, object]] = [
            {"id": OPENAI_MODEL_ID, "name": OPENAI_MODEL_NAME, "dims": OPENAI_MODEL_DIMS}
        ]
        if _bge_available():
            models.append(
                {"id": BGE_M3_MODEL_ID, "name": BGE_M3_MODEL_NAME, "dims": BGE_M3_MODEL_DIMS}
            )
        return models
