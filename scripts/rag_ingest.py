#!/usr/bin/env python3
"""Script de ingestão RAG adaptado do ai-agent-sales."""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.rag.ingestion import (
    stage_docs_from_dir,
    materialize_chunks_from_staging,
    truncate_kb_tables,
)


load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="RAG ingestion script")
    parser.add_argument("--base", default="kb", help="Base directory with .md files")
    parser.add_argument("--empresa", help="Company name for tagging")
    parser.add_argument("--client-id", help="Client ID (UUID)")
    parser.add_argument("--strategy", default="semantic", choices=["fixed", "markdown", "semantic"],
                       help="Chunking strategy")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap")
    parser.add_argument("--truncate", action="store_true", help="Truncate tables before ingestion")
    
    args = parser.parse_args()
    
    if args.truncate:
        print("Truncating KB tables...")
        truncate_kb_tables()
        print("OK: KB tables truncated.")
    
    # Stage documents
    print(f"Staging documents from {args.base}...")
    staged = stage_docs_from_dir(
        args.base,
        empresa=args.empresa,
        client_id=args.client_id
    )
    print(f"Staged {staged} documents.")
    
    # Materialize chunks
    print(f"Materializing chunks with strategy={args.strategy}...")
    chunked = materialize_chunks_from_staging(
        strategy=args.strategy,
        empresa=args.empresa,
        client_id=args.client_id,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(f"Created {chunked} chunks.")
    
    print("Ingestion complete!")


if __name__ == "__main__":
    main()

