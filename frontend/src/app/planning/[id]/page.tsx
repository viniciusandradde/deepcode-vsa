"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// Using relative URLs - Next.js rewrites proxy to backend

interface Document {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  content_preview: string | null;
  uploaded_at: string;
}

interface Stage {
  id: string;
  title: string;
  description: string | null;
  order_index: number;
  status: string;
  estimated_days: number | null;
  start_date: string | null;
  end_date: string | null;
}

interface BudgetItem {
  id: string;
  category: string;
  description: string | null;
  estimated_cost: number;
  actual_cost: number;
  currency: string;
}

interface Project {
  id: string;
  title: string;
  description: string | null;
  status: string;
  linear_project_id: string | null;
  linear_project_url: string | null;
  stages: Stage[];
  documents: Document[];
  budget_items: BudgetItem[];
  total_budget_estimated: number;
  total_budget_actual: number;
}

interface AnalysisResult {
  executive_summary: string;
  critical_points: string[];
  suggested_stages: { title: string; description?: string; estimated_days?: number }[];
  suggested_budget: { category: string; description: string; estimated_cost: number }[];
  risks: string[];
  recommendations: string[];
  tokens_used?: number;
  model_used?: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [focusArea, setFocusArea] = useState("Geral");
  const [activeTab, setActiveTab] = useState<"docs" | "stages" | "budget">("docs");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchProject = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/planning/projects/${projectId}`);
      if (!res.ok) throw new Error("Erro ao carregar projeto");
      const data: Project = await res.json();
      setProject(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append("file", file);
        
        const res = await fetch(`/api/v1/planning/projects/${projectId}/documents`, {
          method: "POST",
          body: formData,
        });
        
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Erro no upload");
        }
      }
      fetchProject();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro no upload");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("Excluir este documento?")) return;
    
    try {
      const res = await fetch(`/api/v1/planning/projects/${projectId}/documents/${docId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Erro ao excluir");
      fetchProject();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao excluir");
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setAnalysis(null);
    
    try {
      const res = await fetch(`/api/v1/planning/projects/${projectId}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ focus_area: focusArea }),
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erro na análise");
      }
      
      const data: AnalysisResult = await res.json();
      setAnalysis(data);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro na análise");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApplySuggestions = async () => {
    if (!analysis) return;
    if (!confirm("Aplicar etapas e orçamento sugeridos ao projeto?")) return;
    
    try {
      const res = await fetch(`/api/v1/planning/projects/${projectId}/apply-suggestions?stages=true&budget=true`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(analysis),
      });
      
      if (!res.ok) throw new Error("Erro ao aplicar sugestões");
      
      fetchProject();
      alert("Sugestões aplicadas com sucesso!");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao aplicar");
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F6F8] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-vsa-orange"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0f1f35] to-[#0a1628] flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-900 mb-4">{error || "Projeto não encontrado"}</p>
          <Link href="/planning">
            <Button>Voltar</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F6F8] text-slate-900">
      {/* Header */}
      <div className="border-b-2 border-slate-400 bg-white px-6 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Link href="/planning" className="text-slate-500 hover:text-slate-900">
                ← Projetos
              </Link>
              <span className="text-slate-400">/</span>
              <h1 className="text-xl font-semibold">{project.title}</h1>
            </div>
            {project.description && (
              <p className="text-sm text-slate-600 mt-1">{project.description}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            {project.linear_project_url && (
              <a
                href={project.linear_project_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate-900 hover:text-slate-900"
              >
                Ver no Linear ↗
              </a>
            )}
            <Link href="/">
              <Button variant="outline" size="sm" className="border-slate-400 text-slate-700">
                Chat VSA
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Documents */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-slate-900 flex items-center justify-between">
                  <span>Documentos</span>
                  <span className="text-sm font-normal text-slate-500">
                    {project.documents.length} arquivo(s)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Upload Area */}
                <div
                  className="border-2 border-dashed border-slate-400 rounded-lg p-4 text-center mb-4 hover:border-vsa-orange/50 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.add("border-vsa-orange");
                  }}
                  onDragLeave={(e) => {
                    e.currentTarget.classList.remove("border-vsa-orange");
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.remove("border-vsa-orange");
                    handleFileUpload(e.dataTransfer.files);
                  }}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.md,.txt"
                    multiple
                    className="hidden"
                    onChange={(e) => handleFileUpload(e.target.files)}
                  />
                  {uploading ? (
                    <span className="text-slate-500">Enviando...</span>
                  ) : (
                    <span className="text-slate-500">
                      Arraste arquivos ou clique para upload<br />
                      <span className="text-xs">(PDF, MD, TXT)</span>
                    </span>
                  )}
                </div>

                {/* Document List */}
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {project.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-2 bg-slate-50 rounded-lg border-2 border-slate-400 shadow-sm"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-900 truncate">{doc.file_name}</p>
                        <p className="text-xs text-slate-500">
                          {doc.file_type?.toUpperCase()} • {formatFileSize(doc.file_size || 0)}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="text-slate-900 hover:text-slate-900 p-1"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Center: Analysis */}
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-slate-900">Análise de Documentos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 mb-4">
                  <select
                    value={focusArea}
                    onChange={(e) => setFocusArea(e.target.value)}
                    className="px-3 py-2 bg-white border-2 border-slate-400 rounded-lg text-slate-900 shadow-sm"
                  >
                    <option value="Geral">Análise Geral</option>
                    <option value="Riscos">Foco em Riscos</option>
                    <option value="Cronograma">Foco em Cronograma</option>
                    <option value="Custos">Foco em Custos</option>
                    <option value="Requisitos">Foco em Requisitos</option>
                    <option value="Arquitetura">Foco em Arquitetura</option>
                  </select>
                  <Button
                    onClick={handleAnalyze}
                    disabled={analyzing || project.documents.length === 0}
                    className="bg-vsa-orange hover:bg-vsa-orange-dark"
                  >
                    {analyzing ? "Analisando..." : "Analisar com IA"}
                  </Button>
                </div>

                {project.documents.length === 0 && (
                  <p className="text-slate-600 text-sm">
                    Faça upload de documentos para habilitar a análise.
                  </p>
                )}

                {analysis && (
                  <div className="space-y-4">
                    <div className="p-4 bg-slate-50 border-2 border-slate-400 rounded-lg shadow-sm">
                      <h3 className="text-sm font-semibold text-slate-900 mb-2">Resumo Executivo</h3>
                      <p className="text-sm text-slate-700">{analysis.executive_summary}</p>
                    </div>

                    {analysis.critical_points.length > 0 && (
                      <div className="p-4 bg-slate-50 border-2 border-slate-400 rounded-lg shadow-sm">
                        <h3 className="text-sm font-semibold text-slate-900 mb-2">Pontos Críticos</h3>
                        <ul className="text-sm text-slate-900 list-disc list-inside space-y-1">
                          {analysis.critical_points.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {analysis.risks.length > 0 && (
                      <div className="p-4 bg-red-50 border-2 border-red-300 rounded-lg shadow-sm">
                        <h3 className="text-sm font-semibold text-slate-900 mb-2">Riscos Identificados</h3>
                        <ul className="text-sm text-slate-900 list-disc list-inside space-y-1">
                          {analysis.risks.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {(analysis.suggested_stages.length > 0 || analysis.suggested_budget.length > 0) && (
                      <div className="flex justify-end">
                        <Button
                          onClick={handleApplySuggestions}
                          className="bg-emerald-600/80 hover:bg-emerald-600"
                        >
                          Aplicar Sugestões ao Projeto
                        </Button>
                      </div>
                    )}

                    {analysis.model_used && (
                      <p className="text-xs text-slate-500 text-right">
                        Modelo: {analysis.model_used} • ~{analysis.tokens_used} tokens
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tabs: Stages & Budget */}
            <Card>
              <CardHeader>
                <div className="flex gap-4 border-b-2 border-slate-400 pb-2">
                  <button
                    onClick={() => setActiveTab("stages")}
                    className={`pb-2 text-sm font-medium transition-colors ${
                      activeTab === "stages"
                        ? "text-slate-900 border-b-2 border-vsa-orange"
                        : "text-slate-500 hover:text-slate-900"
                    }`}
                  >
                    Etapas ({project.stages.length})
                  </button>
                  <button
                    onClick={() => setActiveTab("budget")}
                    className={`pb-2 text-sm font-medium transition-colors ${
                      activeTab === "budget"
                        ? "text-slate-900 border-b-2 border-vsa-orange"
                        : "text-slate-500 hover:text-slate-900"
                    }`}
                  >
                    Orçamento ({formatCurrency(project.total_budget_estimated)})
                  </button>
                </div>
              </CardHeader>
              <CardContent>
                {activeTab === "stages" && (
                  <div className="space-y-2">
                    {project.stages.length === 0 ? (
                      <p className="text-slate-600 text-sm">
                        Nenhuma etapa definida. Analise os documentos para sugestões.
                      </p>
                    ) : (
                      project.stages.map((stage) => (
                        <div
                          key={stage.id}
                          className="p-3 bg-slate-50 border-2 border-slate-400 rounded-lg flex items-center gap-3 shadow-sm"
                        >
                          <span className="text-xs text-slate-500 w-6">{stage.order_index + 1}</span>
                          <div className="flex-1">
                            <p className="text-sm text-slate-900">{stage.title}</p>
                            {stage.description && (
                              <p className="text-xs text-slate-600">{stage.description}</p>
                            )}
                          </div>
                          <span className={`text-xs px-2 py-1 rounded ${
                            stage.status === "completed"
                              ? "bg-emerald-100 text-slate-900"
                              : stage.status === "in_progress"
                              ? "bg-blue-100 text-slate-900"
                              : "bg-slate-100 text-slate-900"
                          }`}>
                            {stage.status === "completed"
                              ? "Concluído"
                              : stage.status === "in_progress"
                              ? "Em andamento"
                              : "Pendente"}
                          </span>
                          {stage.estimated_days && (
                            <span className="text-xs text-slate-500">{stage.estimated_days}d</span>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {activeTab === "budget" && (
                  <div className="space-y-2">
                    {project.budget_items.length === 0 ? (
                      <p className="text-slate-600 text-sm">
                        Nenhum item de orçamento. Analise os documentos para sugestões.
                      </p>
                    ) : (
                      <>
                        {project.budget_items.map((item) => (
                          <div
                            key={item.id}
                            className="p-3 bg-slate-50 border-2 border-slate-400 rounded-lg flex items-center gap-3 shadow-sm"
                          >
                            <span className="text-xs text-slate-500 uppercase w-20">
                              {item.category}
                            </span>
                            <div className="flex-1">
                              <p className="text-sm text-slate-900">{item.description}</p>
                            </div>
                            <span className="text-sm text-slate-900">
                              {formatCurrency(item.estimated_cost)}
                            </span>
                          </div>
                        ))}
                        <div className="pt-2 border-t-2 border-slate-400 flex justify-between text-sm">
                          <span className="text-slate-600">Total Estimado:</span>
                          <span className="text-slate-900 font-semibold">
                            {formatCurrency(project.total_budget_estimated)}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
