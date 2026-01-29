#!/usr/bin/env python3
"""Script para testar criação de projetos no Linear.

Uso:
    python scripts/test_linear_project.py           # dry_run apenas (preview)
    python scripts/test_linear_project.py --create  # cria projeto de teste (dry_run=False)
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_settings
from core.integrations.linear_client import LinearClient


async def test_create_project_dry_run(team_id: str, client: LinearClient) -> bool:
    """Testa create_project em modo dry_run."""
    print("\n1️⃣ create_project (dry_run=True)...")
    result = await client.create_project(
        team_id=team_id,
        name="Teste Projeto VSA",
        description="## Objetivo\nProjeto de teste criado pelo script test_linear_project.py",
        summary="Projeto de teste VSA",
        start_date="2026-02-01",
        target_date="2026-03-31",
        priority=2,
        dry_run=True,
    )
    if not result.success:
        print(f"   ❌ {result.error}")
        return False
    preview = result.output.get("preview", {})
    print(f"   ✅ Preview: {preview.get('name')} (prioridade {preview.get('priority')})")
    return True


async def test_create_project_milestone_dry_run(project_id: str, client: LinearClient) -> bool:
    """Testa create_project_milestone em modo dry_run (requer project_id real)."""
    print("\n2️⃣ create_project_milestone (dry_run=True)...")
    result = await client.create_project_milestone(
        project_id=project_id,
        name="Fase 1 - Planejamento",
        target_date="2026-02-07",
        description="Fase de planejamento do projeto",
        dry_run=True,
    )
    if not result.success:
        print(f"   ❌ {result.error}")
        return False
    preview = result.output.get("preview", {})
    print(f"   ✅ Preview: milestone '{preview.get('name')}' -> {preview.get('target_date')}")
    return True


async def test_create_project_with_plan_dry_run(team_id: str, client: LinearClient) -> bool:
    """Testa create_project_with_plan em modo dry_run."""
    print("\n3️⃣ create_project_with_plan (dry_run=True)...")
    plan = {
        "project": {
            "name": "Teste Projeto Completo VSA",
            "summary": "Projeto de teste com milestones e tarefas",
            "description": "## Objetivo\nValidar criação de projeto completo via API.",
            "startDate": "2026-02-01",
            "targetDate": "2026-03-31",
            "priority": 2,
        },
        "milestones": [
            {"name": "Planejamento", "targetDate": "2026-02-07", "description": ""},
            {"name": "Execução", "targetDate": "2026-03-15", "description": ""},
            {"name": "Conclusão", "targetDate": "2026-03-31", "description": ""},
        ],
        "tasks": [
            {"title": "Tarefa 1 - Levantar requisitos", "description": "", "milestone": "Planejamento", "priority": 2},
            {"title": "Tarefa 2 - Definir cronograma", "description": "", "milestone": "Planejamento", "priority": 3},
            {"title": "Tarefa 3 - Executar plano", "description": "", "milestone": "Execução", "priority": 2},
            {"title": "Tarefa 4 - Validar e entregar", "description": "", "milestone": "Conclusão", "priority": 2},
        ],
    }
    result = await client.create_project_with_plan(team_id=team_id, plan=plan, dry_run=True)
    if not result.success:
        print(f"   ❌ {result.error}")
        return False
    preview = result.output.get("preview", {})
    proj = preview.get("project", {})
    milestones = preview.get("milestones", [])
    tasks = preview.get("tasks", [])
    print(f"   ✅ Preview: projeto '{proj.get('name')}', {len(milestones)} milestones, {len(tasks)} tarefas")
    return True


async def test_create_real(team_id: str, client: LinearClient) -> bool:
    """Cria um projeto real (dry_run=False) para teste manual."""
    print("\n📌 Criando projeto real no Linear...")
    plan = {
        "project": {
            "name": "Teste VSA Script",
            "summary": "Criado por scripts/test_linear_project.py --create",
            "description": "## Teste\nProjeto criado automaticamente pelo script de teste.",
            "startDate": "2026-02-01",
            "targetDate": "2026-02-28",
            "priority": 4,
        },
        "milestones": [
            {"name": "Fase única", "targetDate": "2026-02-28", "description": ""},
        ],
        "tasks": [
            {"title": "Tarefa de teste", "description": "", "milestone": "Fase única", "priority": 4},
        ],
    }
    result = await client.create_project_with_plan(team_id=team_id, plan=plan, dry_run=False)
    if not result.success:
        print(f"   ❌ {result.error}")
        return False
    print(f"   ✅ Projeto criado: {result.output.get('project_url', '')}")
    print(f"   Issues: {result.output.get('issues_created', [])}")
    return True


async def main():
    parser = argparse.ArgumentParser(description="Testar criação de projetos no Linear")
    parser.add_argument("--create", action="store_true", help="Criar projeto real (dry_run=False)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🚀 Teste: Criação de Projetos no Linear")
    print("=" * 60)

    settings = get_settings()
    if not getattr(settings, "linear", None) or not settings.linear.enabled:
        print("❌ Linear não está habilitado. Configure LINEAR_ENABLED e LINEAR_API_KEY.")
        return 1

    api_key = settings.linear.api_key or ""
    if not api_key:
        print("❌ LINEAR_API_KEY não configurada.")
        return 1

    client = LinearClient(api_key)

    try:
        # Obter primeiro team
        result = await client.get_teams()
        if not result.success:
            print(f"❌ Falha ao buscar teams: {result.error}")
            return 1
        teams = result.output.get("teams", [])
        if not teams:
            print("❌ Nenhum team encontrado no workspace.")
            return 1
        team_id = teams[0]["id"]
        team_name = teams[0].get("name", "?")
        print(f"\n📌 Usando team: {team_name} ({team_id[:8]}...)")

        ok = True
        ok &= await test_create_project_dry_run(team_id, client)
        # Para milestone dry_run precisamos de um project_id; usar primeiro projeto existente se houver
        list_res = await client._graphql_query(
            'query { projects(first: 1) { nodes { id } } }'
        )
        if list_res.success and list_res.output.get("projects", {}).get("nodes"):
            proj_id = list_res.output["projects"]["nodes"][0]["id"]
            ok &= await test_create_project_milestone_dry_run(proj_id, client)
        else:
            print("\n2️⃣ create_project_milestone: pulado (nenhum projeto existente para preview)")
        ok &= await test_create_project_with_plan_dry_run(team_id, client)

        if args.create:
            ok &= await test_create_real(team_id, client)

        await client.close()

        print("\n" + "=" * 60)
        if ok:
            print("✅ Todos os testes de projeto Linear passaram.")
            return 0
        print("❌ Alguns testes falharam.")
        return 1
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
