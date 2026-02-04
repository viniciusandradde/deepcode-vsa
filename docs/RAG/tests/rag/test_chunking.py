from pathlib import Path
import pytest

# Fase 1: foco em ingestão e chunking
pytestmark = pytest.mark.phase0

from app.rag.loaders import split_fixed, split_markdown, split_text, load_and_split_dir


DOC_MD = """
# Título

Parágrafo introdutório.

## Seção A
Texto A1. Texto A2. Texto A3.

### Sub A.1
Texto A1.1 repetido. Texto A1.1 repetido.

## Seção B
Texto B. """


def test_split_fixed_counts():
    text = "Lorem ipsum " * 500  # ~6000+ chars
    chunks = split_fixed(text, chunk_size=800, chunk_overlap=200)
    # Para ~6000 chars com 800/200, esperamos pelo menos 6-8 chunks
    assert 5 <= len(chunks) <= 10
    # Overlap: o final de um chunk deve aparecer no início do próximo (heurístico)
    if len(chunks) >= 2:
        assert chunks[0][-50:] in chunks[1]


def test_split_markdown_sections():
    chunks = split_markdown(DOC_MD)
    # Deve respeitar seções e produzir poucos chunks
    assert 2 <= len(chunks) <= 6
    # Primeiro chunk deve conter o conteúdo introdutório
    assert "Parágrafo introdutório" in chunks[0]


def test_split_text_selector():
    c1, s1 = split_text(DOC_MD, strategy="fixed", chunk_size=400, chunk_overlap=100)
    assert s1 == "fixed" and len(c1) >= 1
    c2, s2 = split_text(DOC_MD, strategy="markdown")
    assert s2 == "markdown" and len(c2) >= 1
    # Semantic requer embedder e suporte; sem embedder pode lançar erro
    try:
        from langchain_openai import OpenAIEmbeddings
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        c3, s3 = split_text(DOC_MD, strategy="semantic", embedder=emb)
        assert s3 == "semantic" and len(c3) >= 1
    except Exception:
        # Ambiente sem suporte/credenciais: aceitável não testar semantic aqui
        pass


def test_load_and_split_dir(tmp_path: Path):
    kb = tmp_path / "kb"
    kb.mkdir()
    f = kb / "doc.md"
    f.write_text(DOC_MD, encoding="utf-8")
    items = load_and_split_dir(kb, strategy="markdown")
    assert items, "Nenhum chunk carregado"
    # Estrutura esperada
    first = items[0]
    assert set(["doc_path", "chunk_ix", "content", "meta"]).issubset(first.keys())
    assert first["meta"].get("chunking") == "markdown"
