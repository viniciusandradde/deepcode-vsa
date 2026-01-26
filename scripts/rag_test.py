#!/usr/bin/env python3
"""Scripts de teste e validação RAG."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.rag.tools import kb_search_client


load_dotenv()


def test_search():
    """Teste básico de busca RAG."""
    print("Testando busca RAG...")
    
    try:
        results = kb_search_client.invoke({
            "query": "teste",
            "k": 3,
            "search_type": "hybrid",
            "empresa": "Teste",
        })
        
        print(f"✅ Busca OK: {len(results)} resultados")
        for i, r in enumerate(results, 1):
            print(f"  {i}. Score: {r.get('score', 0):.3f}")
            print(f"     Content: {r.get('content', '')[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return False


def test_hyde():
    """Teste de HyDE."""
    print("\nTestando HyDE...")
    
    try:
        from core.rag.tools import hyde
        expanded = hyde("Como funciona o sistema?")
        print(f"✅ HyDE OK: {len(expanded)} caracteres")
        print(f"   Expanded: {expanded[:200]}...")
        return True
    except Exception as e:
        print(f"❌ Erro no HyDE: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Testes RAG")
    parser.add_argument("--test", choices=["search", "hyde", "all"], default="all")
    parser.add_argument("--empresa", default="Teste", help="Empresa para filtro")
    
    args = parser.parse_args()
    
    results = []
    
    if args.test in ("search", "all"):
        results.append(test_search())
    
    if args.test in ("hyde", "all"):
        results.append(test_hyde())
    
    if all(results):
        print("\n✅ Todos os testes passaram!")
        return 0
    else:
        print("\n❌ Alguns testes falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())

