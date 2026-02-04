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
  embedding_model: string;
  linear_project_id: string | null;
  linear_project_url: string | null;
  stages: Stage[];
  documents: Document[];
  budget_items: BudgetItem[];
  total_budget_estimated: number;
  total_budget_actual: number;
}

interface RagModel {
  id: string;
  name: string;
  dims: number;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [ragModels, setRagModels] = useState<RagModel[]>([]);
  const [embeddingModel, setEmbeddingModel] = useState("openai");
  const [savingEmbedding, setSavingEmbedding] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uniqueRagModels = Array.from(
    new Map(ragModels.map((model) => [model.id, model])).values()
  );

  const fetchProject = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/planning/projects/${projectId}`);
      if (!res.ok) throw new Error("Erro ao carregar projeto");
      const data: Project = await res.json();
      setProject(data);
      setEmbeddingModel(data.embedding_model || "openai");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch(`/api/v1/config/rag-models`);
        if (!res.ok) throw new Error("Erro ao carregar modelos RAG");
        const data: RagModel[] = await res.json();
        if (data && data.length > 0) {
          setRagModels(data);
          return;
        }
      } catch (e) {
        if (process.env.NODE_ENV === "development") {
          console.error("[Planning] RAG models error:", e);
        }
      }
      setRagModels([
        { id: "openai", name: "OpenAI Cloud (Rápido)", dims: 1536 },
      ]);
    };
    fetchModels();
  }, []);

  useEffect(() => {
    if (!project) return;
    if (ragModels.some((m) => m.id === project.embedding_model)) return;
    if (!project.embedding_model) return;
    setRagModels((prev) => [
      ...prev,
      { id: project.embedding_model, name: `${project.embedding_model} (Indisponível)`, dims: 0 },
    ]);
  }, [project, ragModels]);

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

  const handleSaveEmbeddingModel = async () => {
    if (!project) return;
    if (embeddingModel === project.embedding_model) return;
    try {
      setSavingEmbedding(true);
      const res = await fetch(`/api/v1/planning/projects/${projectId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embedding_model: embeddingModel }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erro ao atualizar modelo");
      }
      const updated: Project = await res.json();
      setProject(updated);
      setEmbeddingModel(updated.embedding_model || embeddingModel);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao atualizar modelo");
    } finally {
      setSavingEmbedding(false);
    }
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
            <div className="flex items-center gap-2">
              <select
                value={embeddingModel}
                onChange={(e) => setEmbeddingModel(e.target.value)}
                className="px-2 py-1 bg-white border-2 border-slate-300 rounded-md text-xs text-slate-900"
              >
                {uniqueRagModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.dims})
                  </option>
                ))}
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSaveEmbeddingModel}
                disabled={savingEmbedding || embeddingModel === project.embedding_model}
                className="border-slate-300 text-slate-700"
              >
                {savingEmbedding ? "Salvando..." : "Salvar"}
              </Button>
            </div>
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
        </div>
      </div>
    </div>
  );
}
