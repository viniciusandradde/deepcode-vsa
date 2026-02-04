"""Planning API routes - NotebookLM-like project planning functionality."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Body, File, HTTPException, Query, UploadFile
from psycopg.rows import dict_row

from api.models.planning import (
    AnalyzeDocsRequest,
    AnalyzeDocsResponse,
    BudgetItemCreate,
    BudgetItemResponse,
    BudgetItemUpdate,
    DocumentListResponse,
    DocumentResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    StageCreate,
    StageResponse,
    StageUpdate,
    SyncLinearRequest,
    SyncLinearResponse,
)
from core.database import get_conn
from core.rag.loaders import get_file_type, load_document_from_bytes
from core.rag.planning_ingestion import ingest_project_document_task

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================

def _get_conn_with_dict_row():
    """Get connection with dict row factory."""
    conn = get_conn()
    conn.row_factory = dict_row
    return conn


# =============================================================================
# Projects CRUD
# =============================================================================

@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    empresa: Optional[str] = Query(None, description="Filter by empresa"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all planning projects."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                where_parts = []
                params = []
                
                if status:
                    where_parts.append("status = %s")
                    params.append(status)
                if empresa:
                    where_parts.append("lower(empresa) = lower(%s)")
                    params.append(empresa)
                
                where_clause = " AND ".join(where_parts) if where_parts else "1=1"
                
                # Count total
                cur.execute(f"SELECT COUNT(*) FROM planning_projects WHERE {where_clause}", params)
                total = cur.fetchone()["count"]
                
                # Fetch projects
                cur.execute(
                    f"""
                    SELECT id, title, description, status, empresa, client_id,
                           linear_project_id, linear_project_url, created_at, updated_at
                    FROM planning_projects
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [limit, offset]
                )
                rows = cur.fetchall()
                
                projects = [ProjectResponse(**row) for row in rows]
                return ProjectListResponse(projects=projects, total=total)
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar projetos: {e}")


@router.post("/projects", response_model=ProjectResponse)
async def create_project(request: ProjectCreate):
    """Create a new planning project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO planning_projects (title, description, empresa, client_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title, description, status, empresa, client_id,
                              linear_project_id, linear_project_url, created_at, updated_at
                    """,
                    (request.title, request.description, request.empresa, request.client_id)
                )
                row = cur.fetchone()
                conn.commit()
                return ProjectResponse(**row)
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar projeto: {e}")


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: UUID):
    """Get project details with stages, documents, and budget."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Get project
                cur.execute(
                    """
                    SELECT id, title, description, status, empresa, client_id,
                           linear_project_id, linear_project_url, created_at, updated_at
                    FROM planning_projects
                    WHERE id = %s
                    """,
                    (str(project_id),)
                )
                project = cur.fetchone()
                if not project:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                # Get stages
                cur.execute(
                    """
                    SELECT id, project_id, title, description, order_index, status,
                           estimated_days, start_date, end_date, linear_milestone_id,
                           created_at, updated_at
                    FROM planning_stages
                    WHERE project_id = %s
                    ORDER BY order_index
                    """,
                    (str(project_id),)
                )
                stages = [StageResponse(**row) for row in cur.fetchall()]
                
                # Get documents
                cur.execute(
                    """
                    SELECT id, project_id, file_name, file_type, file_size,
                           LEFT(content, 500) as content_preview, uploaded_at
                    FROM planning_documents
                    WHERE project_id = %s
                    ORDER BY uploaded_at DESC
                    """,
                    (str(project_id),)
                )
                documents = [DocumentResponse(**row) for row in cur.fetchall()]
                
                # Get budget items
                cur.execute(
                    """
                    SELECT id, project_id, stage_id, category, description,
                           estimated_cost, actual_cost, currency, created_at, updated_at
                    FROM planning_budget_items
                    WHERE project_id = %s
                    ORDER BY category, created_at
                    """,
                    (str(project_id),)
                )
                budget_items = [BudgetItemResponse(**row) for row in cur.fetchall()]
                
                # Calculate totals
                total_estimated = sum(b.estimated_cost for b in budget_items)
                total_actual = sum(b.actual_cost for b in budget_items)
                
                return ProjectDetailResponse(
                    **project,
                    stages=stages,
                    documents=documents,
                    budget_items=budget_items,
                    total_budget_estimated=total_estimated,
                    total_budget_actual=total_actual,
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar projeto: {e}")


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, request: ProjectUpdate):
    """Update a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                updates = []
                params = []
                
                if request.title is not None:
                    updates.append("title = %s")
                    params.append(request.title)
                if request.description is not None:
                    updates.append("description = %s")
                    params.append(request.description)
                if request.status is not None:
                    updates.append("status = %s")
                    params.append(request.status)
                
                if not updates:
                    raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
                
                params.append(str(project_id))
                
                cur.execute(
                    f"""
                    UPDATE planning_projects
                    SET {", ".join(updates)}
                    WHERE id = %s
                    RETURNING id, title, description, status, empresa, client_id,
                              linear_project_id, linear_project_url, created_at, updated_at
                    """,
                    params
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                conn.commit()
                return ProjectResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar projeto: {e}")


@router.delete("/projects/{project_id}")
async def delete_project(project_id: UUID):
    """Delete a project and all related data."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM planning_projects WHERE id = %s RETURNING id",
                    (str(project_id),)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                conn.commit()
                return {"message": "Projeto excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir projeto: {e}")


# =============================================================================
# Documents
# =============================================================================

@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
async def list_documents(project_id: UUID):
    """List documents for a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, file_name, file_type, file_size,
                           LEFT(content, 500) as content_preview, uploaded_at
                    FROM planning_documents
                    WHERE project_id = %s
                    ORDER BY uploaded_at DESC
                    """,
                    (str(project_id),)
                )
                rows = cur.fetchall()
                documents = [DocumentResponse(**row) for row in rows]
                return DocumentListResponse(documents=documents, total=len(documents))
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {e}")


@router.post("/projects/{project_id}/documents", response_model=DocumentResponse)
async def upload_document(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a document to a project. RAG ingestion runs in background."""
    try:
        # Validate file type
        file_type = get_file_type(file.filename or "")
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail="Tipo de arquivo não suportado. Use: .pdf, .md, .txt"
            )
        
        # Read and extract content
        content_bytes = await file.read()
        file_size = len(content_bytes)
        
        try:
            extracted_text = load_document_from_bytes(content_bytes, file.filename or "doc")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao extrair texto: {e}")
        
        # Save to database
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Check if project exists
                cur.execute(
                    "SELECT id FROM planning_projects WHERE id = %s",
                    (str(project_id),)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                cur.execute(
                    """
                    INSERT INTO planning_documents (project_id, file_name, file_type, content, file_size)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, project_id, file_name, file_type, file_size,
                              LEFT(content, 500) as content_preview, uploaded_at
                    """,
                    (str(project_id), file.filename, file_type, extracted_text, file_size)
                )
                row = cur.fetchone()
                conn.commit()
                document_id = row["id"]

        # RAG ingestion in background (chunking + embedding + kb_chunks with project_id)
        background_tasks.add_task(
            ingest_project_document_task,
            project_id=project_id,
            document_id=document_id,
            content_bytes=content_bytes,
            filename=file.filename or "doc",
        )

        return DocumentResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {e}")


@router.delete("/projects/{project_id}/documents/{document_id}")
async def delete_document(project_id: UUID, document_id: UUID):
    """Delete a document from a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM planning_documents WHERE id = %s AND project_id = %s RETURNING id",
                    (str(document_id), str(project_id))
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Documento não encontrado")
                conn.commit()
                return {"message": "Documento excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir documento: {e}")


# =============================================================================
# Stages
# =============================================================================

@router.post("/projects/{project_id}/stages", response_model=StageResponse)
async def create_stage(project_id: UUID, request: StageCreate):
    """Create a stage in a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Check if project exists
                cur.execute(
                    "SELECT id FROM planning_projects WHERE id = %s",
                    (str(project_id),)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                cur.execute(
                    """
                    INSERT INTO planning_stages 
                    (project_id, title, description, order_index, estimated_days, start_date, end_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, project_id, title, description, order_index, status,
                              estimated_days, start_date, end_date, linear_milestone_id,
                              created_at, updated_at
                    """,
                    (
                        str(project_id), request.title, request.description,
                        request.order_index, request.estimated_days,
                        request.start_date, request.end_date
                    )
                )
                row = cur.fetchone()
                conn.commit()
                return StageResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar etapa: {e}")


@router.put("/projects/{project_id}/stages/{stage_id}", response_model=StageResponse)
async def update_stage(project_id: UUID, stage_id: UUID, request: StageUpdate):
    """Update a stage."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                updates = []
                params = []
                
                if request.title is not None:
                    updates.append("title = %s")
                    params.append(request.title)
                if request.description is not None:
                    updates.append("description = %s")
                    params.append(request.description)
                if request.order_index is not None:
                    updates.append("order_index = %s")
                    params.append(request.order_index)
                if request.status is not None:
                    updates.append("status = %s")
                    params.append(request.status)
                if request.estimated_days is not None:
                    updates.append("estimated_days = %s")
                    params.append(request.estimated_days)
                if request.start_date is not None:
                    updates.append("start_date = %s")
                    params.append(request.start_date)
                if request.end_date is not None:
                    updates.append("end_date = %s")
                    params.append(request.end_date)
                
                if not updates:
                    raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
                
                params.extend([str(stage_id), str(project_id)])
                
                cur.execute(
                    f"""
                    UPDATE planning_stages
                    SET {", ".join(updates)}
                    WHERE id = %s AND project_id = %s
                    RETURNING id, project_id, title, description, order_index, status,
                              estimated_days, start_date, end_date, linear_milestone_id,
                              created_at, updated_at
                    """,
                    params
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Etapa não encontrada")
                conn.commit()
                return StageResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar etapa: {e}")


@router.delete("/projects/{project_id}/stages/{stage_id}")
async def delete_stage(project_id: UUID, stage_id: UUID):
    """Delete a stage from a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM planning_stages WHERE id = %s AND project_id = %s RETURNING id",
                    (str(stage_id), str(project_id))
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Etapa não encontrada")
                conn.commit()
                return {"message": "Etapa excluída com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir etapa: {e}")


# =============================================================================
# Budget Items
# =============================================================================

@router.post("/projects/{project_id}/budget", response_model=BudgetItemResponse)
async def create_budget_item(project_id: UUID, request: BudgetItemCreate):
    """Create a budget item for a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Check if project exists
                cur.execute(
                    "SELECT id FROM planning_projects WHERE id = %s",
                    (str(project_id),)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                cur.execute(
                    """
                    INSERT INTO planning_budget_items 
                    (project_id, stage_id, category, description, estimated_cost, actual_cost, currency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, project_id, stage_id, category, description,
                              estimated_cost, actual_cost, currency, created_at, updated_at
                    """,
                    (
                        str(project_id),
                        str(request.stage_id) if request.stage_id else None,
                        request.category, request.description,
                        request.estimated_cost, request.actual_cost, request.currency
                    )
                )
                row = cur.fetchone()
                conn.commit()
                return BudgetItemResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating budget item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar item de orçamento: {e}")


@router.put("/projects/{project_id}/budget/{item_id}", response_model=BudgetItemResponse)
async def update_budget_item(project_id: UUID, item_id: UUID, request: BudgetItemUpdate):
    """Update a budget item."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                updates = []
                params = []
                
                if request.category is not None:
                    updates.append("category = %s")
                    params.append(request.category)
                if request.description is not None:
                    updates.append("description = %s")
                    params.append(request.description)
                if request.estimated_cost is not None:
                    updates.append("estimated_cost = %s")
                    params.append(request.estimated_cost)
                if request.actual_cost is not None:
                    updates.append("actual_cost = %s")
                    params.append(request.actual_cost)
                if request.stage_id is not None:
                    updates.append("stage_id = %s")
                    params.append(str(request.stage_id))
                
                if not updates:
                    raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
                
                params.extend([str(item_id), str(project_id)])
                
                cur.execute(
                    f"""
                    UPDATE planning_budget_items
                    SET {", ".join(updates)}
                    WHERE id = %s AND project_id = %s
                    RETURNING id, project_id, stage_id, category, description,
                              estimated_cost, actual_cost, currency, created_at, updated_at
                    """,
                    params
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Item de orçamento não encontrado")
                conn.commit()
                return BudgetItemResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating budget item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar item de orçamento: {e}")


@router.delete("/projects/{project_id}/budget/{item_id}")
async def delete_budget_item(project_id: UUID, item_id: UUID):
    """Delete a budget item from a project."""
    try:
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM planning_budget_items WHERE id = %s AND project_id = %s RETURNING id",
                    (str(item_id), str(project_id))
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Item de orçamento não encontrado")
                conn.commit()
                return {"message": "Item de orçamento excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting budget item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir item de orçamento: {e}")


# =============================================================================
# Analysis (NotebookLM-like)
# =============================================================================

@router.post("/projects/{project_id}/analyze", response_model=AnalyzeDocsResponse)
async def analyze_project_documents(project_id: UUID, request: AnalyzeDocsRequest):
    """Analyze all project documents using Gemini (NotebookLM-like functionality).
    
    This endpoint reads all documents from the project and uses a large context
    LLM (Gemini) to analyze them and generate planning insights including:
    - Executive summary
    - Critical points based on focus area
    - Suggested stages/phases
    - Suggested budget items
    - Risks and recommendations
    """
    try:
        # Get all document content
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Check if project exists
                cur.execute(
                    "SELECT id, title FROM planning_projects WHERE id = %s",
                    (str(project_id),)
                )
                project = cur.fetchone()
                if not project:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                # Get all document content
                cur.execute(
                    "SELECT get_planning_documents_context(%s)",
                    (str(project_id),)
                )
                result = cur.fetchone()
                documents_context = result["get_planning_documents_context"] if result else ""
        
        if not documents_context or not documents_context.strip():
            return AnalyzeDocsResponse(
                executive_summary="Nenhum documento encontrado no projeto.",
                critical_points=["Faça upload de documentos antes de analisar"],
                suggested_stages=[],
                suggested_budget=[],
                risks=["Projeto sem documentação"],
                recommendations=["Adicione especificações, requisitos ou outros documentos"],
            )
        
        # Analyze with planning agent
        from core.agents.planning import analyze_project_documents as analyze_docs
        
        analysis = await analyze_docs(
            documents_context=documents_context,
            focus_area=request.focus_area,
        )
        
        # Convert to response model
        from api.models.planning import SuggestedBudgetItem, SuggestedStage
        
        suggested_stages = [
            SuggestedStage(**s) for s in analysis.get("suggested_stages", [])
        ]
        suggested_budget = [
            SuggestedBudgetItem(**b) for b in analysis.get("suggested_budget", [])
        ]
        
        return AnalyzeDocsResponse(
            executive_summary=analysis.get("executive_summary", ""),
            critical_points=analysis.get("critical_points", []),
            suggested_stages=suggested_stages,
            suggested_budget=suggested_budget,
            risks=analysis.get("risks", []),
            recommendations=analysis.get("recommendations", []),
            tokens_used=analysis.get("tokens_used"),
            model_used=analysis.get("model_used"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na análise: {e}")


@router.post("/projects/{project_id}/apply-suggestions")
async def apply_analysis_suggestions(
    project_id: UUID,
    stages: bool = True,
    budget: bool = True,
    body: AnalyzeDocsResponse = Body(...),
):
    """Apply suggestions from analysis to the project.
    
    Creates stages and budget items based on analysis results.
    """
    try:
        created_stages = []
        created_budget = []
        
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                # Check if project exists
                cur.execute(
                    "SELECT id FROM planning_projects WHERE id = %s",
                    (str(project_id),)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                # Create stages
                if stages and body.suggested_stages:
                    for i, stage in enumerate(body.suggested_stages):
                        cur.execute(
                            """
                            INSERT INTO planning_stages 
                            (project_id, title, description, order_index, estimated_days)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id, title
                            """,
                            (
                                str(project_id), stage.title, stage.description,
                                i, stage.estimated_days if stage.estimated_days is not None else 0,
                            )
                        )
                        row = cur.fetchone()
                        created_stages.append(row)
                
                # Create budget items
                if budget and body.suggested_budget:
                    for item in body.suggested_budget:
                        cur.execute(
                            """
                            INSERT INTO planning_budget_items 
                            (project_id, category, description, estimated_cost)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id, category, estimated_cost
                            """,
                            (
                                str(project_id), item.category, item.description,
                                item.estimated_cost,
                            )
                        )
                        row = cur.fetchone()
                        created_budget.append(row)
                
                conn.commit()
        
        return {
            "message": "Sugestões aplicadas com sucesso",
            "stages_created": len(created_stages),
            "budget_items_created": len(created_budget),
            "stages": created_stages,
            "budget_items": created_budget,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar sugestões: {e}")


# =============================================================================
# Linear Sync
# =============================================================================

@router.post("/projects/{project_id}/sync-linear", response_model=SyncLinearResponse)
async def sync_project_to_linear(project_id: UUID, request: SyncLinearRequest):
    """Sync project to Linear.app - creates project with milestones.
    
    Uses the existing linear_client.create_project_with_plan() functionality.
    """
    try:
        # Get project with stages
        with _get_conn_with_dict_row() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, description, linear_project_id
                    FROM planning_projects WHERE id = %s
                    """,
                    (str(project_id),)
                )
                project = cur.fetchone()
                if not project:
                    raise HTTPException(status_code=404, detail="Projeto não encontrado")
                
                if project["linear_project_id"]:
                    return SyncLinearResponse(
                        success=False,
                        project_id=project["linear_project_id"],
                        message="Projeto já está sincronizado com Linear",
                    )
                
                # Get stages
                cur.execute(
                    """
                    SELECT title, description, estimated_days, start_date, end_date
                    FROM planning_stages
                    WHERE project_id = %s
                    ORDER BY order_index
                    """,
                    (str(project_id),)
                )
                stages = cur.fetchall()
        
        # Build plan for Linear
        plan = {
            "project": {
                "name": project["title"][:50],  # Linear limit
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
            "tasks": [],  # Can be extended to create issues
        }
        
        # Call Linear client
        from core.integrations.linear_client import LinearClient
        from core.config import get_settings
        
        settings = get_settings()
        if not settings.linear.enabled or not settings.linear.api_key:
            raise HTTPException(
                status_code=400,
                detail="Linear não está configurado. Configure LINEAR_API_KEY."
            )
        
        client = LinearClient(settings.linear.api_key)
        
        try:
            result = await client.create_project_with_plan(
                team_id=request.team_id,
                plan=plan,
                dry_run=False,
            )
            
            if not result.success:
                raise HTTPException(status_code=500, detail=f"Erro no Linear: {result.error}")
            
            # Update project with Linear IDs
            linear_project_id = result.output.get("project_id")
            linear_project_url = result.output.get("project_url")
            
            with _get_conn_with_dict_row() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE planning_projects
                        SET linear_project_id = %s, linear_project_url = %s
                        WHERE id = %s
                        """,
                        (linear_project_id, linear_project_url, str(project_id))
                    )
                    conn.commit()
            
            return SyncLinearResponse(
                success=True,
                project_id=linear_project_id,
                project_url=linear_project_url,
                milestones_created=result.output.get("milestones_created", 0),
                issues_created=len(result.output.get("issues_created", [])),
                message="Projeto sincronizado com Linear com sucesso",
            )
            
        finally:
            await client.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing to Linear: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar com Linear: {e}")
