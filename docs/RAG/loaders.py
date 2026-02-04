"""
Carregadores e splitters para documentos .md do KB.

Regras:
- KISS/YAGNI: três estratégias de chunking (fixed, markdown, semantic).
- Comentários em português para favorecer entendimento humano.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

# Suporte a SemanticChunker em múltiplos pacotes (compat):
_HAS_SEMANTIC = False
SemanticChunker = None  # type: ignore
try:  # langchain-text-splitters (algumas versões expõem aqui)
    from langchain_text_splitters import SemanticChunker as _SC  # type: ignore
    SemanticChunker = _SC  # type: ignore
    _HAS_SEMANTIC = True
except Exception:
    try:  # langchain-experimental (versões mais novas)
        from langchain_experimental.text_splitter import SemanticChunker as _SC  # type: ignore
        SemanticChunker = _SC  # type: ignore
        _HAS_SEMANTIC = True
    except Exception:
        SemanticChunker = None  # type: ignore
        _HAS_SEMANTIC = False


def list_md_files(base_dir: str | Path) -> List[Path]:
    """Lista arquivos .md recursivamente a partir de base_dir."""
    base = Path(base_dir)
    return sorted([p for p in base.rglob("*.md") if p.is_file()])


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_fixed(text: str, chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)


def split_markdown(text: str, *, chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
    """Markdown awareness: usa apenas cabeçalhos (sem fallback para fixed).

    Se a divisão por cabeçalhos produzir trechos longos, retorna-os como estão.
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
    )
    docs = splitter.split_text(text)
    return [d.page_content for d in docs]


def split_semantic(text: str, embedder=None) -> List[str]:
    """Semantic chunking orientado por embeddings (sem fallback).

    - Requer um embedder compatível (ex.: OpenAIEmbeddings) e suporte à classe SemanticChunker.
    - Se indisponível, lança erro explícito.
    """
    if not _HAS_SEMANTIC:
        raise RuntimeError("SemanticChunker não está disponível no ambiente")
    if embedder is None:
        raise RuntimeError("Semantic chunking requer 'embedder' válido (ex.: OpenAIEmbeddings)")
    splitter = SemanticChunker(embedder, breakpoint_threshold_type="interquartile")
    return splitter.split_text(text)


def split_text(text: str, strategy: str = "fixed", *, embedder=None, chunk_size: int = 800, chunk_overlap: int = 200) -> Tuple[List[str], str]:
    """Divide texto em chunks conforme a estratégia.

    Retorna (chunks, strategy_resolvida).
    """
    s = (strategy or "").lower()
    if not s:
        raise RuntimeError("Estratégia de chunking não informada (fixed/markdown/semantic)")
    if s == "fixed":
        return split_fixed(text, chunk_size, chunk_overlap), "fixed"
    if s == "markdown":
        return split_markdown(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap), "markdown"
    if s == "semantic":
        return split_semantic(text, embedder), "semantic"
    # sem fallback: falha explicitamente
    raise RuntimeError(f"Estratégia de chunking inválida: {strategy}")


def load_and_split_dir(base_dir: str | Path, strategy: str = "fixed", *, embedder=None, chunk_size: int = 800, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """Carrega todos .md do diretório e retorna lista de chunks com metadados.

    Saída: [{doc_path, chunk_ix, content, meta}]
    meta inclui: {chunking: fixed|markdown|semantic}
    """
    items: List[Dict[str, Any]] = []
    for path in list_md_files(base_dir):
        text = read_text(path)
        chunks, resolved = split_text(text, strategy, embedder=embedder, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for i, c in enumerate(chunks):
            items.append({
                "doc_path": str(path.as_posix()),
                "chunk_ix": i,
                "content": c,
                "meta": {"chunking": resolved},
            })
    return items
