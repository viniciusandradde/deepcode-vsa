"""Document loaders and text splitters for RAG."""

from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

try:
    from langchain_experimental.text_splitter import SemanticChunker
    HAS_SEMANTIC = True
except ImportError:
    try:
        from langchain_text_splitters import SemanticChunker
        HAS_SEMANTIC = True
    except ImportError:
        HAS_SEMANTIC = False
        SemanticChunker = None


def split_text(
    text: str,
    strategy: str = "fixed",
    embedder: Optional[OpenAIEmbeddings] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
) -> tuple[List[Dict[str, Any]], str]:
    """Split text into chunks using specified strategy.
    
    Args:
        text: Text to split
        strategy: Chunking strategy ("fixed", "markdown", "semantic")
        embedder: Embeddings model (required for semantic)
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        Tuple of (chunks_list, resolved_strategy_name)
    """
    chunks: List[Dict[str, Any]] = []
    resolved = strategy
    
    if strategy == "fixed":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        texts = splitter.split_text(text)
        for i, chunk_text in enumerate(texts):
            chunks.append({
                "content": chunk_text,
                "meta": {"chunking": "fixed", "chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
            })
    
    elif strategy == "markdown":
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = splitter.split_text(text)
        for i, split in enumerate(md_header_splits):
            chunks.append({
                "content": split.page_content,
                "meta": {
                    "chunking": "markdown",
                    "headers": split.metadata,
                },
            })
    
    elif strategy == "semantic":
        if embedder is None:
            raise ValueError("semantic chunking requires embedder")
        if not HAS_SEMANTIC or SemanticChunker is None:
            # Fallback to fixed if semantic chunking not available
            resolved = "fixed"
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            texts = splitter.split_text(text)
            for i, chunk_text in enumerate(texts):
                chunks.append({
                    "content": chunk_text,
                    "meta": {"chunking": "fixed"},
                })
        else:
            semantic_splitter = SemanticChunker(
                embeddings=embedder,
                breakpoint_threshold_type="percentile",
            )
            texts = semantic_splitter.split_text(text)
            for i, chunk_text in enumerate(texts):
                chunks.append({
                    "content": chunk_text,
                    "meta": {"chunking": "semantic"},
                })
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    return chunks, resolved


def load_and_split_dir(
    base_dir: str,
    strategy: str = "semantic",
    embedder: Optional[OpenAIEmbeddings] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """Load markdown files from directory and split into chunks.
    
    Args:
        base_dir: Base directory containing .md files
        strategy: Chunking strategy
        embedder: Embeddings model (for semantic)
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dictionaries with doc_path, chunk_ix, content, meta
    """
    base = Path(base_dir)
    files = sorted([p for p in base.rglob("*.md") if p.is_file()])
    
    all_chunks: List[Dict[str, Any]] = []
    
    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8")
            chunks, _ = split_text(
                text,
                strategy=strategy,
                embedder=embedder,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            
            doc_path = str(file_path.as_posix())
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "doc_path": doc_path,
                    "chunk_ix": i,
                    "content": chunk["content"],
                    "meta": chunk.get("meta", {}),
                })
        except Exception as e:
            # Log error but continue processing other files
            print(f"Error processing {file_path}: {e}")
            continue
    
    return all_chunks

