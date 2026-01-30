"""Document loaders and text splitters for RAG."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

# PDF support
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    PdfReader = None

logger = logging.getLogger(__name__)

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


# =============================================================================
# Document Loading (PDF, MD, TXT support)
# =============================================================================

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        ImportError: If pypdf is not installed
        ValueError: If file cannot be read
    """
    if not HAS_PYPDF or PdfReader is None:
        raise ImportError(
            "pypdf is required for PDF support. Install with: pip install pypdf"
        )
    
    try:
        reader = PdfReader(file_path)
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages_text.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(pages_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF {file_path}: {e}")


def extract_text_from_pdf_bytes(content: bytes, filename: str = "document.pdf") -> str:
    """Extract text from PDF bytes (for file uploads).
    
    Args:
        content: PDF file content as bytes
        filename: Original filename (for error messages)
        
    Returns:
        Extracted text content
    """
    if not HAS_PYPDF or PdfReader is None:
        raise ImportError(
            "pypdf is required for PDF support. Install with: pip install pypdf"
        )
    
    import io
    try:
        reader = PdfReader(io.BytesIO(content))
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages_text.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(pages_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF {filename}: {e}")


def load_document(file_path: str) -> str:
    """Load document and extract text based on file type.
    
    Supports: .md, .txt, .pdf
    
    Args:
        file_path: Path to document file
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file type is not supported
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def load_document_from_bytes(content: bytes, filename: str) -> str:
    """Load document from bytes and extract text.
    
    Supports: .md, .txt, .pdf
    
    Args:
        content: File content as bytes
        filename: Original filename (to determine type)
        
    Returns:
        Extracted text content
    """
    ext = Path(filename).suffix.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )
    
    if ext == ".pdf":
        return extract_text_from_pdf_bytes(content, filename)
    elif ext in (".md", ".txt"):
        return content.decode("utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def get_file_type(filename: str) -> Optional[str]:
    """Get file type from filename.
    
    Args:
        filename: Filename with extension
        
    Returns:
        File type string (pdf, md, txt) or None if unsupported
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".md":
        return "md"
    elif ext == ".txt":
        return "txt"
    return None

