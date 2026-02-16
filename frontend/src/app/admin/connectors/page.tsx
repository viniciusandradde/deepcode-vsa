"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";

interface Connector {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  category: string;
  is_system: boolean;
}

export default function AdminConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.get("/api/v1/admin/connectors");
        if (res.ok) setConnectors(await res.json());
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="space-y-3">
      {[1, 2, 3].map((i) => <div key={i} className="h-20 animate-pulse rounded-xl bg-obsidian-900" />)}
    </div>;
  }

  const grouped = connectors.reduce<Record<string, Connector[]>>((acc, c) => {
    (acc[c.category] ??= []).push(c);
    return acc;
  }, {});

  const categoryLabels: Record<string, string> = {
    integration: "Integrações",
    search: "Busca",
    utility: "Utilitários",
  };

  return (
    <div className="space-y-8">
      <h2 className="text-lg font-semibold">Conectores do Sistema</h2>
      <p className="text-sm text-neutral-400">
        Conectores são integrações disponíveis para vincular aos agentes.
        Configure as credenciais no arquivo <code className="text-xs text-brand-primary">.env</code>.
      </p>

      {Object.entries(grouped).map(([category, items]) => (
        <section key={category} className="space-y-3">
          <h3 className="text-sm font-medium text-neutral-300">
            {categoryLabels[category] || category}
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((c) => (
              <div
                key={c.id}
                className="rounded-xl border border-white/[0.06] bg-obsidian-900 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/5 text-neutral-400">
                    {c.icon || "🔌"}
                  </div>
                  <div>
                    <h4 className="font-medium text-white">{c.name}</h4>
                    <span className="text-xs text-neutral-500">{c.slug}</span>
                  </div>
                </div>
                {c.description && (
                  <p className="mt-2 text-xs text-neutral-400">{c.description}</p>
                )}
                {c.is_system && (
                  <span className="mt-2 inline-block rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-neutral-500">
                    Sistema
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
