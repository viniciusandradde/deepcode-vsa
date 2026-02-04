"""Script de testes automatizados para validar intents do agente CRM.

Uso:
    python scripts/test_intents.py
    python scripts/test_intents.py --domain leads
    python scripts/test_intents.py --verbose
"""
# verificar a maneira correta de passar ID
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import argparse
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import HumanMessage
from app.agent import workflow


@dataclass
class TestCase:
    id: str
    domain: str
    prompt: str
    expected_intent: str
    description: str
    expected_output_contains: List[str] = None  # Palavras-chave esperadas na resposta final


@dataclass
class TestResult:
    case_id: str
    domain: str
    success: bool
    expected_intent: str
    actual_intent: str
    message: str
    prompt: str
    output_check: str = ""  # Resultado da validação de saída
    final_output: str = ""  # Resposta final do grafo


def get_test_cases() -> List[TestCase]:
    """Define todos os casos de teste baseados no cheatsheet."""
    return [
        # Domínio: Leads
        TestCase(
            id="lead_criar_01",
            domain="leads",
            prompt="Cadastre o João da ACME",
            expected_intent="lead_criar",
            description="Criar lead com nome e empresa",
            expected_output_contains=["lead", "criado", "sucesso"]
        ),
        TestCase(
            id="lead_criar_02",
            domain="leads",
            prompt="Criar lead com email maria@acme.com",
            expected_intent="lead_criar",
            description="Criar lead com email"
        ),
        TestCase(
            id="lead_obter_01",
            domain="leads",
            prompt="Selecione o lead do Maria da ACME",
            expected_intent="lead_obter",
            description="Obter lead por nome e empresa"
        ),
        TestCase(
            id="lead_buscar_01",
            domain="leads",
            prompt="Busque leads com ACME",
            expected_intent="lead_buscar",
            description="Buscar leads por termo"
        ),
        TestCase(
            id="lead_buscar_02",
            domain="leads",
            prompt="Procurar por Maria",
            expected_intent="lead_buscar",
            description="Buscar leads por nome"
        ),
        TestCase(
            id="lead_listar_01",
            domain="leads",
            prompt="Liste meus leads",
            expected_intent="lead_listar",
            description="Listar todos os leads"
        ),
        TestCase(
            id="lead_atualizar_01",
            domain="leads",
            prompt="Marque o Maria como qualificado",
            expected_intent="lead_atualizar",
            description="Atualizar status do lead"
        ),
        
        # Domínio: Notas
        TestCase(
            id="nota_adicionar_01",
            domain="notas",
            prompt="Adicione nota: retornar orçamento amanhã",
            expected_intent="nota_adicionar",
            description="Adicionar nota a lead",
            expected_output_contains=["nota", "registrada", "sucesso"]
        ),
        TestCase(
            id="nota_listar_01",
            domain="notas",
            prompt="Liste as notas do Maria",
            expected_intent="nota_listar",
            description="Listar notas de um lead"
        ),
        
        # Domínio: Tarefas
        TestCase(
            id="tarefa_criar_01",
            domain="tarefas",
            prompt="Crie uma tarefa para ligar amanhã",
            expected_intent="tarefa_criar",
            description="Criar tarefa de ligação",
            expected_output_contains=["tarefa", "criada", "sucesso"]
        ),
        TestCase(
            id="tarefa_concluir_01",
            domain="tarefas",
            prompt="Conclua a última tarefa do Maria",
            expected_intent="tarefa_concluir",
            description="Concluir tarefa",
            expected_output_contains=["tarefa", "concluída", "sucesso"]
        ),
        TestCase(
            id="tarefa_listar_01",
            domain="tarefas",
            prompt="Quais tarefas do Maria estão em aberto?",
            expected_intent="tarefa_listar",
            description="Listar tarefas em aberto"
        ),
        
        # Domínio: Propostas
        TestCase(
            id="proposta_rascunhar_01",
            domain="propostas",
            prompt="Rascunhe proposta ACME em BRL",
            expected_intent="proposta_rascunhar",
            description="Criar rascunho de proposta"
        ),
        TestCase(
            id="proposta_adicionar_item_01",
            domain="propostas",
            prompt="Adicione 2x Consultoria a R$ 5000",
            expected_intent="proposta_adicionar_item",
            description="Adicionar item à proposta"
        ),
        TestCase(
            id="proposta_atualizar_corpo_01",
            domain="propostas",
            prompt="Atualize o corpo da proposta com este texto",
            expected_intent="proposta_atualizar_corpo",
            description="Atualizar corpo da proposta"
        ),
        TestCase(
            id="proposta_calcular_totais_01",
            domain="propostas",
            prompt="Recalcule totais da proposta",
            expected_intent="proposta_calcular_totais",
            description="Recalcular totais"
        ),
        TestCase(
            id="proposta_listar_01",
            domain="propostas",
            prompt="Liste propostas do Maria",
            expected_intent="proposta_listar",
            description="Listar propostas de lead"
        ),
        TestCase(
            id="proposta_exportar_01",
            domain="propostas",
            prompt="Exporte a proposta em markdown",
            expected_intent="proposta_exportar",
            description="Exportar proposta"
        ),
        
        # Domínio: Utilidades
        TestCase(
            id="status_listar_01",
            domain="utilidades",
            prompt="Quais são os status de lead válidos?",
            expected_intent="listar_status_lead",
            description="Listar status disponíveis"
        ),
        TestCase(
            id="conversa_geral_01",
            domain="utilidades",
            prompt="Olá, como você está?",
            expected_intent="conversa_geral",
            description="Conversa geral (fallback)"
        ),
    ]


def run_test(case: TestCase, graph, verbose: bool = False) -> TestResult:
    """Executa um caso de teste em uma nova sessão."""
    try:
        # Nova sessão para cada teste
        thread_id = f"test_{case.id}"
        state = {"messages": [HumanMessage(content=case.prompt)]}
        
        if verbose:
            print(f"\n[{case.id}] Executando: {case.prompt}")
        
        result = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
        actual_intent = result.get("intent", "")
        
        # Extrai a resposta final
        final_output = ""
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            final_output = getattr(last_message, "content", "")
        
        # Valida intent
        intent_match = actual_intent == case.expected_intent
        
        # Valida saída final (se esperado)
        output_check = ""
        output_match = True
        if case.expected_output_contains:
            if final_output:
                output_text = final_output.lower()
                
                missing_keywords = []
                for keyword in case.expected_output_contains:
                    if keyword.lower() not in output_text:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    output_match = False
                    output_check = f"Faltam palavras-chave: {', '.join(missing_keywords)}"
                else:
                    output_check = "✓ Saída validada"
                
                if verbose:
                    print(f"  Output: {output_text[:100]}...")
                    print(f"  Output check: {output_check}")
            else:
                output_match = False
                output_check = "Sem mensagem de saída"
        
        if verbose:
            print(f"  Expected intent: {case.expected_intent}")
            print(f"  Got intent: {actual_intent}")
        
        success = intent_match and output_match
        
        if not intent_match:
            message = f"✗ Intent: esperado '{case.expected_intent}', obtido '{actual_intent}'"
        elif not output_match:
            message = f"✗ Output: {output_check}"
        else:
            message = "✓ Passou"
        
        return TestResult(
            case_id=case.id,
            domain=case.domain,
            success=success,
            expected_intent=case.expected_intent,
            actual_intent=actual_intent,
            message=message,
            prompt=case.prompt,
            output_check=output_check,
            final_output=final_output
        )
    
    except Exception as e:
        return TestResult(
            case_id=case.id,
            domain=case.domain,
            success=False,
            expected_intent=case.expected_intent,
            actual_intent="ERROR",
            message=f"✗ Erro: {str(e)}",
            prompt=case.prompt,
            output_check="Erro na execução",
            final_output=""
        )


def print_summary(results: List[TestResult], domain_filter: str = None):
    """Imprime resumo dos resultados por domínio."""
    domains = {}
    for result in results:
        if domain_filter and result.domain != domain_filter:
            continue
        if result.domain not in domains:
            domains[result.domain] = {"passed": 0, "failed": 0, "results": []}
        if result.success:
            domains[result.domain]["passed"] += 1
        else:
            domains[result.domain]["failed"] += 1
        domains[result.domain]["results"].append(result)
    
    print("\n" + "="*70)
    print("RESUMO DOS TESTES POR DOMÍNIO")
    print("="*70)
    
    total_passed = 0
    total_failed = 0
    
    for domain, stats in sorted(domains.items()):
        total = stats["passed"] + stats["failed"]
        total_passed += stats["passed"]
        total_failed += stats["failed"]
        
        print(f"\n📦 {domain.upper()}: {stats['passed']}/{total} aprovados")
        
        for result in stats["results"]:
            if not result.success:
                print(f"  {result.message}")
                print(f"    Prompt: {result.prompt}")
    
    print("\n" + "="*70)
    total = total_passed + total_failed
    percentage = (total_passed / total * 100) if total > 0 else 0
    print(f"TOTAL: {total_passed}/{total} aprovados ({percentage:.1f}%)")
    print("="*70 + "\n")
    
    return total_failed == 0


def save_results_to_json(results: List[TestResult], domain_filter: str = None):
    """Salva os resultados em arquivo JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"
    if domain_filter:
        filename = f"test_results_{domain_filter}_{timestamp}.json"
    
    # Salva na pasta outputs dentro de tests
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename
    
    # Converte resultados para dict
    results_dict = {
        "timestamp": datetime.now().isoformat(),
        "domain_filter": domain_filter,
        "total_tests": len(results),
        "passed": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "results": [asdict(r) for r in results]
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados salvos em: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Testa intents do agente CRM")
    parser.add_argument("--domain", help="Filtrar por domínio (leads, notas, tarefas, propostas, utilidades)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    args = parser.parse_args()
    
    print("Carregando grafo do agente...")
    graph = workflow.compiled_graph
    
    print("Executando testes...")
    cases = get_test_cases()
    
    if args.domain:
        cases = [c for c in cases if c.domain == args.domain]
        print(f"Filtrando por domínio: {args.domain}")
    
    results = []
    for case in cases:
        result = run_test(case, graph, verbose=args.verbose)
        results.append(result)
        if not args.verbose:
            print("." if result.success else "F", end="", flush=True)
    
    if not args.verbose:
        print()
    
    all_passed = print_summary(results, args.domain)
    save_results_to_json(results, args.domain)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
