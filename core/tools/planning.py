"""Planning tools for LangChain agent integration."""

import json
import logging
from typing import Optional

from langchain_core.tools import tool
from psycopg.rows import dict_row

from core.database import get_conn

logger = logging.getLogger(__name__)


def _get_conn_with_dict_row():
    """Get connection with dict row factory."""
    conn = get_conn()
    conn.row_factory = dict_row
    return conn


@tool
def planning_list_projects(
    status: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Lista projetos de planejamento.
    
    Args:
        status: Filtrar por status (draft, active, completed, archived)
        limit: Número máximo de projetos (padrão 10)
    
    Returns:
        Lista de projetos em formato JSON
    """
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                if status:
                    cur.execute(
                        """
                        SELECT id, title, status, created_at,
                               (SELECT COUNT(*) FROM planning_documents d WHERE d.project_id = p.id) as docs_count,
                               (SELECT COUNT(*) FROM planning_stages s WHERE s.project_id = p.id) as stages_count
                        FROM planning_projects p
                        WHERE status = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (status, limit)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, title, status, created_at,
                               (SELECT COUNT(*) FROM planning_documents d WHERE d.project_id = p.id) as docs_count,
                               (SELECT COUNT(*) FROM planning_stages s WHERE s.project_id = p.id) as stages_count
                        FROM planning_projects p
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (limit,)
                    )
                rows = cur.fetchall()
                
                if not rows:
                    return json.dumps({"projects": [], "message": "Nenhum projeto encontrado"})
                
                projects = []
                for row in rows:
                    projects.append({
                        "id": str(row["id"]),
                        "title": row["title"],
                        "status": row["status"],
                        "docs_count": row["docs_count"],
                        "stages_count": row["stages_count"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    })
                
                return json.dumps({"projects": projects}, ensure_ascii=False)
                
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        return json.dumps({"error": f"Erro ao listar projetos: {e}"})


@tool
def planning_get_project(project_id: str) -> str:
    """Obtém detalhes de um projeto de planejamento específico.
    
    Args:
        project_id: ID do projeto (UUID)
    
    Returns:
        Detalhes do projeto em formato JSON incluindo etapas, documentos e orçamento
    """
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Get project
                cur.execute(
                    """
                    SELECT id, title, description, status, linear_project_id, linear_project_url
                    FROM planning_projects WHERE id = %s
                    """,
                    (project_id,)
                )
                project = cur.fetchone()
                if not project:
                    return json.dumps({"error": "Projeto não encontrado"})
                
                # Get stages
                cur.execute(
                    """
                    SELECT title, description, order_index, status, estimated_days
                    FROM planning_stages WHERE project_id = %s ORDER BY order_index
                    """,
                    (project_id,)
                )
                stages = [dict(row) for row in cur.fetchall()]
                
                # Get budget summary
                cur.execute(
                    """
                    SELECT category, SUM(estimated_cost) as total
                    FROM planning_budget_items WHERE project_id = %s
                    GROUP BY category
                    """,
                    (project_id,)
                )
                budget = {row["category"]: float(row["total"]) for row in cur.fetchall()}
                
                result = {
                    "id": str(project["id"]),
                    "title": project["title"],
                    "description": project["description"],
                    "status": project["status"],
                    "linear_project_id": project["linear_project_id"],
                    "linear_project_url": project["linear_project_url"],
                    "stages": stages,
                    "budget_by_category": budget,
                    "total_budget": sum(budget.values()),
                }
                
                return json.dumps(result, ensure_ascii=False, default=str)
                
    except Exception as e:
        logger.error(f"Error getting project: {e}", exc_info=True)
        return json.dumps({"error": f"Erro ao obter projeto: {e}"})


@tool
def planning_create_project(
    title: str,
    description: Optional[str] = None,
    dry_run: bool = True,
) -> str:
    """Cria um novo projeto de planejamento.
    
    Args:
        title: Título do projeto
        description: Descrição do projeto (opcional)
        dry_run: Se True, apenas mostra preview sem criar (padrão True)
    
    Returns:
        Resultado da criação ou preview
    """
    try:
        if dry_run:
            return json.dumps({
                "dry_run": True,
                "preview": {
                    "title": title,
                    "description": description,
                    "status": "draft",
                },
                "message": "Preview do projeto. Confirme com dry_run=False para criar."
            }, ensure_ascii=False)
        
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO planning_projects (title, description)
                    VALUES (%s, %s)
                    RETURNING id, title, status, created_at
                    """,
                    (title, description)
                )
                row = cur.fetchone()
                conn.commit()
                
                return json.dumps({
                    "success": True,
                    "project": {
                        "id": str(row["id"]),
                        "title": row["title"],
                        "status": row["status"],
                    },
                    "message": f"Projeto '{title}' criado com sucesso!",
                    "url": f"/planning/{row['id']}",
                }, ensure_ascii=False)
                
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        return json.dumps({"error": f"Erro ao criar projeto: {e}"})


@tool
def planning_analyze_project(
    project_id: str,
    focus_area: str = "Geral",
) -> str:
    """Analisa documentos de um projeto e gera insights usando IA.
    
    Args:
        project_id: ID do projeto (UUID)
        focus_area: Área de foco (Geral, Riscos, Cronograma, Custos, Requisitos, Arquitetura)
    
    Returns:
        Resultado da análise com resumo executivo, riscos, sugestões
    """
    try:
        import asyncio
        from core.agents.planning import analyze_project_documents as analyze_docs
        
        # Get documents context
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT get_planning_documents_context(%s)",
                    (project_id,)
                )
                result = cur.fetchone()
                documents_context = result["get_planning_documents_context"] if result else ""
        
        if not documents_context or not documents_context.strip():
            return json.dumps({
                "error": "Nenhum documento encontrado no projeto. Faça upload de documentos primeiro."
            }, ensure_ascii=False)
        
        # Run async analysis
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new task for nested async
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    analyze_docs(documents_context, focus_area)
                )
                analysis = future.result()
        else:
            analysis = asyncio.run(analyze_docs(documents_context, focus_area))
        
        return json.dumps(analysis, ensure_ascii=False, default=str)
        
    except Exception as e:
        logger.error(f"Error analyzing project: {e}", exc_info=True)
        return json.dumps({"error": f"Erro na análise: {e}"})


@tool
def planning_sync_to_linear(
    project_id: str,
    team_id: str,
    dry_run: bool = True,
) -> str:
    """Sincroniza projeto com Linear.app, criando projeto e milestones.
    
    Args:
        project_id: ID do projeto de planejamento (UUID)
        team_id: ID do time no Linear
        dry_run: Se True, apenas mostra preview sem criar (padrão True)
    
    Returns:
        Resultado da sincronização ou preview
    """
    try:
        import asyncio
        from core.integrations.linear_client import LinearClient
        from core.config import get_settings
        
        settings = get_settings()
        if not settings.linear.enabled or not settings.linear.api_key:
            return json.dumps({
                "error": "Linear não está configurado. Configure LINEAR_API_KEY."
            })
        
        # Get project with stages
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, description, linear_project_id FROM planning_projects WHERE id = %s",
                    (project_id,)
                )
                project = cur.fetchone()
                if not project:
                    return json.dumps({"error": "Projeto não encontrado"})
                
                if project["linear_project_id"]:
                    return json.dumps({
                        "error": "Projeto já está sincronizado com Linear",
                        "linear_project_id": project["linear_project_id"],
                    })
                
                cur.execute(
                    "SELECT title, description, estimated_days, end_date FROM planning_stages WHERE project_id = %s ORDER BY order_index",
                    (project_id,)
                )
                stages = list(cur.fetchall())
        
        # Build plan
        plan = {
            "project": {
                "name": project["title"][:50],
                "description": project["description"] or "",
                "summary": (project["description"] or "")[:255],
            },
            "milestones": [
                {
                    "name": s["title"],
                    "targetDate": str(s["end_date"]) if s["end_date"] else None,
                    "description": s["description"] or "",
                }
                for s in stages
            ],
            "tasks": [],
        }
        
        if dry_run:
            return json.dumps({
                "dry_run": True,
                "preview": plan,
                "message": f"Preview: Criar projeto '{project['title']}' no Linear com {len(stages)} milestones. Confirme com dry_run=False.",
            }, ensure_ascii=False, default=str)
        
        # Sync to Linear
        async def do_sync():
            client = LinearClient(settings.linear.api_key)
            try:
                result = await client.create_project_with_plan(
                    team_id=team_id,
                    plan=plan,
                    dry_run=False,
                )
                return result
            finally:
                await client.close()
        
        result = asyncio.run(do_sync())
        
        if not result.success:
            return json.dumps({"error": f"Erro no Linear: {result.error}"})
        
        # Update project with Linear ID
        linear_project_id = result.output.get("project_id")
        linear_project_url = result.output.get("project_url")
        
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE planning_projects SET linear_project_id = %s, linear_project_url = %s WHERE id = %s",
                    (linear_project_id, linear_project_url, project_id)
                )
                conn.commit()
        
        return json.dumps({
            "success": True,
            "project_id": linear_project_id,
            "project_url": linear_project_url,
            "milestones_created": result.output.get("milestones_created", 0),
            "message": "Projeto sincronizado com Linear com sucesso!",
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error syncing to Linear: {e}", exc_info=True)
        return json.dumps({"error": f"Erro ao sincronizar: {e}"})


# Export all tools for agent integration
PLANNING_TOOLS = [
    planning_list_projects,
    planning_get_project,
    planning_create_project,
    planning_analyze_project,
    planning_sync_to_linear,
]
