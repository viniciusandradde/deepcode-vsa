"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

interface Domain {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  color: string;
  is_active: boolean;
  created_at: string;
}

export default function AdminDomainsPage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formName, setFormName] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formColor, setFormColor] = useState("#6366f1");
  const [saving, setSaving] = useState(false);

  const loadDomains = useCallback(async () => {
    try {
      const res = await apiClient.get("/api/v1/admin/domains");
      if (res.ok) setDomains(await res.json());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDomains();
  }, [loadDomains]);

  const handleCreate = async () => {
    if (!formName.trim() || !formSlug.trim()) return;
    try {
      setSaving(true);
      const res = await apiClient.post("/api/v1/admin/domains", {
        name: formName,
        slug: formSlug,
        description: formDescription || null,
        color: formColor,
      });
      if (res.ok) {
        setShowForm(false);
        setFormName("");
        setFormSlug("");
        setFormDescription("");
        setFormColor("#6366f1");
        await loadDomains();
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    const res = await apiClient.delete(`/api/v1/admin/domains/${id}`);
    if (res.ok) await loadDomains();
  };

  if (loading) {
    return <div className="space-y-3">
      {[1, 2].map((i) => <div key={i} className="h-20 animate-pulse rounded-xl bg-obsidian-900" />)}
    </div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Domínios de Conhecimento</h2>
          <p className="mt-1 text-sm text-neutral-400">
            Domínios isolam a base RAG por área (TI, RH, Financeiro, etc.)
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-medium text-white hover:bg-brand-primary/80 transition-colors"
        >
          Novo Domínio
        </button>
      </div>

      {showForm && (
        <div className="rounded-xl border border-brand-primary/30 bg-obsidian-900 p-5 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs text-neutral-400">Nome</label>
              <input
                value={formName}
                onChange={(e) => {
                  setFormName(e.target.value);
                  if (!formSlug || formSlug === formName.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9_-]/g, "")) {
                    setFormSlug(e.target.value.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9_-]/g, ""));
                  }
                }}
                placeholder="Ex: Recursos Humanos"
                className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary/40 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-neutral-400">Slug</label>
              <input
                value={formSlug}
                onChange={(e) => setFormSlug(e.target.value)}
                placeholder="ex: rh"
                className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary/40 focus:outline-none"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs text-neutral-400">Descrição</label>
            <input
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              placeholder="Descrição do domínio..."
              className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary/40 focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs text-neutral-400">Cor:</label>
            <input
              type="color"
              value={formColor}
              onChange={(e) => setFormColor(e.target.value)}
              className="h-8 w-12 cursor-pointer rounded border border-white/10 bg-transparent"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={saving || !formName.trim() || !formSlug.trim()}
              className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-medium text-white hover:bg-brand-primary/80 transition-colors disabled:opacity-50"
            >
              {saving ? "Criando..." : "Criar Domínio"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-white/[0.06] px-4 py-2 text-sm text-neutral-300 hover:bg-white/5 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {domains.map((d) => (
          <div
            key={d.id}
            className="rounded-xl border border-white/[0.06] bg-obsidian-900 p-4"
          >
            <div className="flex items-center gap-3">
              <div
                className="h-4 w-4 rounded-full"
                style={{ backgroundColor: d.color }}
              />
              <div className="flex-1">
                <h4 className="font-medium text-white">{d.name}</h4>
                <span className="text-xs text-neutral-500">{d.slug}</span>
              </div>
              <button
                onClick={() => handleDelete(d.id)}
                className="rounded p-1 text-neutral-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                title="Remover domínio"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            {d.description && (
              <p className="mt-2 text-xs text-neutral-400">{d.description}</p>
            )}
          </div>
        ))}
        {domains.length === 0 && !showForm && (
          <div className="col-span-full rounded-xl border border-white/[0.06] bg-obsidian-900 p-6 text-center text-sm text-neutral-500">
            Nenhum domínio criado. Clique em "Novo Domínio" para começar.
          </div>
        )}
      </div>
    </div>
  );
}
