"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

interface Agent {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  avatar: string | null;
  agent_type: string;
  is_default: boolean;
  is_active: boolean;
  connector_count: number;
  skill_count: number;
  domain_count: number;
}

export default function AdminAgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAgents = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/api/v1/admin/agents");
      if (!res.ok) throw new Error(`Failed to load agents: ${res.status}`);
      const data = await res.json();
      setAgents(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-48 animate-pulse rounded-xl border border-white/[0.06] bg-obsidian-900" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
        <p className="text-red-400">{error}</p>
        <p className="mt-2 text-sm text-neutral-400">
          Verifique se o schema de multi-agente foi aplicado:{" "}
          <code className="text-xs">psql -f sql/kb/12_multi_agent_schema.sql</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Agentes ({agents.length})</h2>
        <Link
          href="/admin/agents/new"
          className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-medium text-white hover:bg-brand-primary/80 transition-colors"
        >
          Novo Agente
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <Link
            key={agent.id}
            href={`/admin/agents/${agent.id}`}
            className="group rounded-xl border border-white/[0.06] bg-obsidian-900 p-5 transition-all hover:border-brand-primary/30 hover:bg-obsidian-800"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-primary/10 text-lg">
                {agent.avatar || "🤖"}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-white truncate">{agent.name}</h3>
                  {agent.is_default && (
                    <span className="shrink-0 rounded-full bg-brand-primary/20 px-2 py-0.5 text-[10px] font-medium text-brand-primary">
                      Padrão
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-neutral-500">{agent.slug}</p>
              </div>
            </div>

            {agent.description && (
              <p className="mt-3 text-sm text-neutral-400 line-clamp-2">{agent.description}</p>
            )}

            <div className="mt-4 flex gap-3 text-xs text-neutral-500">
              <span className="flex items-center gap-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                {agent.connector_count} conectores
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500" />
                {agent.skill_count} habilidades
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-purple-500" />
                {agent.domain_count} domínios
              </span>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-wider text-neutral-500">
                {agent.agent_type}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
