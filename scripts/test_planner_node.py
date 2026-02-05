#!/usr/bin/env python3
"""
Script de teste para verificar o Planner Node do UnifiedAgent.

Testa:
1. Classificação ITIL
2. Geração de plano estruturado
3. Parsing JSON
4. Fallback plan
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from langchain_core.messages import HumanMessage
from core.agents.unified import UnifiedAgent


async def test_planner_incident():
    """Test planner with incident scenario."""
    print("\n" + "="*60)
    print("TEST 1: INCIDENT - Servidor web01 com problemas")
    print("="*60)
    
    # Use GLM 4.5 AIR for testing
    model_name = "z-ai/glm-4.5-air"  # GLM 4.5 AIR on OpenRouter (106B params, 12B active via MoE)
    fast_model = model_name  # Same model for router/classifier
    
    agent = UnifiedAgent(
        model_name=model_name,
        tools=[],  # No tools for planning test
        enable_itil=True,
        enable_planning=True,
        enable_confirmation=False,
        fast_model_name=fast_model,
    )
    
    # Create input
    input_data = {
        "messages": [HumanMessage(content="O servidor web01 está com problemas e usuários não conseguem acessar")]
    }
    
    # Run agent
    try:
        result = await agent.ainvoke(input_data, config={"configurable": {"thread_id": "test-incident"}})
        
        # Check if plan was created
        plan = result.get("plan", [])
        task_category = result.get("task_category")
        gut_score = result.get("gut_score")
        
        print(f"\n✅ Categoria ITIL: {task_category}")
        print(f"✅ GUT Score: {gut_score}")
        print(f"\n📋 Plano gerado ({len(plan)} passos):")
        
        for i, step in enumerate(plan, 1):
            print(f"\n  Passo {i}:")
            print(f"    Tool: {step.get('tool')}")
            print(f"    Params: {step.get('params')}")
            print(f"    Requires Confirm: {step.get('requires_confirm')}")
            print(f"    Description: {step.get('description')}")
        
        if len(plan) > 0:
            print("\n✅ Planner Node funcionando corretamente!")
        else:
            print("\n⚠️ Planner retornou plano vazio")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def test_planner_problem():
    """Test planner with problem scenario."""
    print("\n" + "="*60)
    print("TEST 2: PROBLEM - Banco de dados lento toda segunda")
    print("="*60)
    
    agent = UnifiedAgent(
        model_name=os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.0-flash-exp"),
        tools=[],
        enable_itil=True,
        enable_planning=True,
        enable_confirmation=False,
        fast_model_name="google/gemini-2.0-flash-exp",
    )
    
    input_data = {
        "messages": [HumanMessage(content="Preciso entender por que o banco de dados fica lento toda segunda-feira de manhã")]
    }
    
    try:
        result = await agent.ainvoke(input_data, config={"configurable": {"thread_id": "test-problem"}})
        
        plan = result.get("plan", [])
        task_category = result.get("task_category")
        
        print(f"\n✅ Categoria ITIL: {task_category}")
        print(f"\n📋 Plano gerado ({len(plan)} passos):")
        
        for i, step in enumerate(plan, 1):
            print(f"\n  Passo {i}:")
            print(f"    Tool: {step.get('tool')}")
            print(f"    Description: {step.get('description')}")
        
        if task_category == "problema" and len(plan) > 0:
            print("\n✅ Planner detectou PROBLEMA corretamente!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def test_planner_change():
    """Test planner with change scenario."""
    print("\n" + "="*60)
    print("TEST 3: CHANGE - Atualizar sistema ERP")
    print("="*60)
    
    agent = UnifiedAgent(
        model_name=os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.0-flash-exp"),
        tools=[],
        enable_itil=True,
        enable_planning=True,
        enable_confirmation=False,
        fast_model_name="google/gemini-2.0-flash-exp",
    )
    
    input_data = {
        "messages": [HumanMessage(content="Preciso atualizar o sistema ERP para a versão 2.5")]
    }
    
    try:
        result = await agent.ainvoke(input_data, config={"configurable": {"thread_id": "test-change"}})
        
        plan = result.get("plan", [])
        task_category = result.get("task_category")
        
        print(f"\n✅ Categoria ITIL: {task_category}")
        print(f"\n📋 Plano gerado ({len(plan)} passos):")
        
        # Check if any step requires confirmation
        requires_confirm_steps = [s for s in plan if s.get("requires_confirm", False)]
        
        for i, step in enumerate(plan, 1):
            confirm_flag = "🔒" if step.get("requires_confirm") else "✓"
            print(f"\n  {confirm_flag} Passo {i}: {step.get('description')}")
        
        if len(requires_confirm_steps) > 0:
            print(f"\n✅ Plano tem {len(requires_confirm_steps)} passo(s) que requerem confirmação!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("\n🧪 TESTES DO PLANNER NODE - UnifiedAgent")
    print("="*60)
    
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n❌ OPENROUTER_API_KEY não configurada!")
        print("Configure no .env antes de executar os testes.")
        return
    
    await test_planner_incident()
    await test_planner_problem()
    await test_planner_change()
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
