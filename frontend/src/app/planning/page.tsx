"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// Using relative URLs - Next.js rewrites proxy to backend

interface Project {
  id: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  linear_project_url: string | null;
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
  const [creating, setCreating] = useState(false);

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
        }),
      });
      
      if (!res.ok) throw new Error("Erro ao criar projeto");
      
      setNewProjectTitle("");
      setNewProjectDescription("");
      setShowCreateModal(false);
      fetchProjects();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao criar projeto");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (id: string) => {
    if (!confirm("Tem certeza que deseja excluir este projeto?")) return;
    
    try {
      const res = await fetch(`/api/v1/planning/projects/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Erro ao excluir projeto");
      fetchProjects();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao excluir projeto");
    }
  };

  const statusColors: Record<string, string> = {
    draft: "bg-gray-500/20 text-gray-300",
    active: "bg-emerald-500/20 text-emerald-300",
    completed: "bg-blue-500/20 text-blue-300",
    archived: "bg-slate-500/20 text-slate-400",
  };

  const statusLabels: Record<string, string> = {
    draft: "Rascunho",
    active: "Ativo",
    completed: "Concluído",
    archived: "Arquivado",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0f1f35] to-[#0a1628] text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Planejamento de Projetos</h1>
            <p className="text-slate-400 mt-1">
              Gerencie projetos com análise de documentos estilo NotebookLM
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/">
              <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">
                ← Voltar ao Chat
              </Button>
            </Link>
            <Button 
              onClick={() => setShowCreateModal(true)}
              className="bg-vsa-orange/80 hover:bg-vsa-orange text-white"
            >
              + Novo Projeto
            </Button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/40 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-vsa-orange"></div>
          </div>
        )}

        {/* Projects Grid */}
        {!loading && projects.length === 0 && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-12 text-center">
              <p className="text-slate-400 mb-4">Nenhum projeto encontrado</p>
              <Button 
                onClick={() => setShowCreateModal(true)}
                className="bg-vsa-orange/80 hover:bg-vsa-orange"
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
                className="bg-slate-800/50 border-slate-700 hover:border-vsa-orange/50 transition-colors"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <Link href={`/planning/${project.id}`} className="flex-1">
                      <CardTitle className="text-lg text-white hover:text-vsa-orange transition-colors">
                        {project.title}
                      </CardTitle>
                    </Link>
                    <span className={`text-xs px-2 py-1 rounded ${statusColors[project.status] || statusColors.draft}`}>
                      {statusLabels[project.status] || project.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-400 mb-4 line-clamp-2">
                    {project.description || "Sem descrição"}
                  </p>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Criado em {new Date(project.created_at).toLocaleDateString("pt-BR")}
                    </span>
                    <div className="flex gap-2">
                      {project.linear_project_url && (
                        <a 
                          href={project.linear_project_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300"
                        >
                          Linear ↗
                        </a>
                      )}
                      <button
                        onClick={() => handleDeleteProject(project.id)}
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
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-white mb-4">Novo Projeto</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Título *</label>
                  <input
                    type="text"
                    value={newProjectTitle}
                    onChange={(e) => setNewProjectTitle(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-vsa-orange focus:outline-none"
                    placeholder="Nome do projeto"
                    autoFocus
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Descrição</label>
                  <textarea
                    value={newProjectDescription}
                    onChange={(e) => setNewProjectDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-vsa-orange focus:outline-none resize-none"
                    rows={3}
                    placeholder="Descrição breve do projeto"
                  />
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <Button 
                  variant="outline" 
                  onClick={() => setShowCreateModal(false)}
                  className="border-slate-600 text-slate-300"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCreateProject}
                  disabled={!newProjectTitle.trim() || creating}
                  className="bg-vsa-orange/80 hover:bg-vsa-orange"
                >
                  {creating ? "Criando..." : "Criar Projeto"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
