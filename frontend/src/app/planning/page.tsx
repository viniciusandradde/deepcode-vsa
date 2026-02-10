"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SkeletonProjectCard } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { Dialog } from "@/components/ui/dialog";
import { PageNavBar } from "@/components/app/PageNavBar";
// Using relative URLs - Next.js rewrites proxy to backend

interface Project {
  id: string;
  title: string;
  description: string | null;
  status: string;
  embedding_model: string;
  created_at: string;
  updated_at: string;
  linear_project_url: string | null;
}

interface RagModel {
  id: string;
  name: string;
  dims: number;
}

interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export default function PlanningPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState("");
  const [newProjectDescription, setNewProjectDescription] = useState("");
  const [ragModels, setRagModels] = useState<RagModel[]>([]);
  const [embeddingModel, setEmbeddingModel] = useState("openai");
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null);
  const { addToast } = useToast();

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/planning/projects`);
      if (!res.ok) {
        if (process.env.NODE_ENV === "development") {
          console.error("[Planning] Fetch failed:", res.status, res.statusText);
        }
        throw new Error(`Erro ao carregar projetos: ${res.status}`);
      }
      const data: ProjectListResponse = await res.json();
      setProjects(data.projects);
      setError(null);
    } catch (e) {
      if (process.env.NODE_ENV === "development") {
        console.error("[Planning] Error:", e);
      }
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch(`/api/v1/config/rag-models`);
        if (!res.ok) throw new Error("Erro ao carregar modelos RAG");
        const data: RagModel[] = await res.json();
        if (data && data.length > 0) {
          setRagModels(data);
          setEmbeddingModel(data[0].id);
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
      setEmbeddingModel("openai");
    };
    fetchModels();
  }, []);

  const handleCreateProject = async () => {
    if (!newProjectTitle.trim()) return;
    
    try {
      setCreating(true);
      const res = await fetch(`/api/v1/planning/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newProjectTitle,
          description: newProjectDescription,
          embedding_model: embeddingModel,
        }),
      });
      
      if (!res.ok) throw new Error("Erro ao criar projeto");
      
      setNewProjectTitle("");
      setNewProjectDescription("");
      setShowCreateModal(false);
      addToast("Projeto criado", "success");
      fetchProjects();
    } catch (e) {
      addToast(e instanceof Error ? e.message : "Erro ao criar projeto", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!deleteTarget) return;
    const { id, title } = deleteTarget;
    setDeleteTarget(null);
    try {
      const res = await fetch(`/api/v1/planning/projects/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Erro ao excluir projeto");
      addToast(`Projeto "${title}" excluído`, "success");
      fetchProjects();
    } catch (e) {
      addToast(e instanceof Error ? e.message : "Erro ao excluir projeto", "error");
    }
  };

  const statusColors: Record<string, string> = {
    draft: "bg-white/5 text-neutral-400",
    active: "bg-emerald-500/15 text-emerald-300",
    completed: "bg-blue-500/15 text-blue-300",
    archived: "bg-white/5 text-neutral-500",
  };

  const statusLabels: Record<string, string> = {
    draft: "Rascunho",
    active: "Ativo",
    completed: "Concluído",
    archived: "Arquivado",
  };

  return (
    <div className="min-h-screen bg-obsidian-950 text-white">
      <PageNavBar breadcrumbs={[{ label: "Projetos" }]} />
      <div className="max-w-6xl mx-auto p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Projetos</h1>
            <p className="text-neutral-400 mt-1">
              Gerencie projetos com análise de documentos
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-brand-primary hover:bg-brand-primary/90 text-white hover:shadow-glow-orange"
            >
              + Novo Projeto
            </Button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SkeletonProjectCard />
            <SkeletonProjectCard />
            <SkeletonProjectCard />
            <SkeletonProjectCard />
            <SkeletonProjectCard />
            <SkeletonProjectCard />
          </div>
        )}

        {/* Projects Grid */}
        {!loading && projects.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-neutral-400 mb-4">Nenhum projeto encontrado</p>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-brand-primary hover:bg-brand-primary/90 text-white hover:shadow-glow-orange"
              >
                Criar primeiro projeto
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && projects.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <Card
                key={project.id}
                className="hover:border-brand-primary/40 hover:shadow-glow-orange transition-all"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <Link href={`/planning/${project.id}`} className="flex-1">
                      <CardTitle className="text-lg text-white hover:text-brand-primary transition-colors">
                        {project.title}
                      </CardTitle>
                    </Link>
                    <span className={`text-xs px-2 py-1 rounded ${statusColors[project.status] || statusColors.draft}`}>
                      {statusLabels[project.status] || project.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-neutral-400 mb-4 line-clamp-2">
                    {project.description || "Sem descrição"}
                  </p>
                  <div className="flex items-center justify-between text-xs text-neutral-500">
                    <span>
                      Criado em {new Date(project.created_at).toLocaleDateString("pt-BR")}
                    </span>
                    <div className="flex gap-2">
                      {project.linear_project_url && (
                        <a
                          href={project.linear_project_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-brand-primary hover:text-brand-primary/80"
                        >
                          Linear ↗
                        </a>
                      )}
                      <button
                        onClick={() => setDeleteTarget({ id: project.id, title: project.title })}
                        className="text-red-400 hover:text-red-300"
                      >
                        Excluir
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="glass-panel border border-white/[0.06] rounded-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-white mb-4">Novo Projeto</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Título *</label>
                  <input
                    type="text"
                    value={newProjectTitle}
                    onChange={(e) => setNewProjectTitle(e.target.value)}
                    className="w-full px-3 py-2 bg-obsidian-800 border border-white/10 rounded-lg text-white placeholder:text-neutral-600 focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
                    placeholder="Nome do projeto"
                    autoFocus
                  />
                </div>

                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Descrição</label>
                  <textarea
                    value={newProjectDescription}
                    onChange={(e) => setNewProjectDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-obsidian-800 border border-white/10 rounded-lg text-white placeholder:text-neutral-600 focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/30 resize-none"
                    rows={3}
                    placeholder="Descrição breve do projeto"
                  />
                </div>

                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Modelo de Embeddings</label>
                  <select
                    value={embeddingModel}
                    onChange={(e) => setEmbeddingModel(e.target.value)}
                    className="w-full px-3 py-2 bg-obsidian-800 border border-white/10 rounded-lg text-white focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
                  >
                    {ragModels.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name} ({model.dims})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  className="border-white/10 text-neutral-300"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCreateProject}
                  disabled={!newProjectTitle.trim() || creating}
                  className="bg-brand-primary hover:bg-brand-primary/90 text-white hover:shadow-glow-orange"
                >
                  {creating ? "Criando..." : "Criar Projeto"}
                </Button>
              </div>
            </div>
          </div>
        )}

        <Dialog
          open={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          title="Confirmar exclusão"
          footer={
            <>
              <Button variant="outline" onClick={() => setDeleteTarget(null)} className="border-white/10 text-neutral-300">
                Cancelar
              </Button>
              <Button onClick={handleDeleteProject} className="bg-red-600 hover:bg-red-700 text-white">
                Excluir
              </Button>
            </>
          }
        >
          Tem certeza que deseja excluir o projeto <strong>&quot;{deleteTarget?.title}&quot;</strong>?
        </Dialog>
      </div>
    </div>
  );
}
