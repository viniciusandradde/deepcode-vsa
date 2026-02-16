"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";

interface Connector {
  slug: string;
  name: string;
  icon: string | null;
  enabled: boolean;
  config: Record<string, any>;
}

interface Skill {
  slug: string;
  name: string;
  icon: string | null;
  enabled: boolean;
}

interface Domain {
  id: string;
  name: string;
  slug: string;
  color: string;
  access_level: string;
}

interface AgentDetail {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  avatar: string | null;
  system_prompt: string | null;
  agent_type: string;
  model_override: string | null;
  is_default: boolean;
  connectors: Connector[];
  skills: Skill[];
  domains: Domain[];
}

interface AvailableConnector {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  category: string;
}

interface AvailableSkill {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  category: string;
}

interface AvailableDomain {
  id: string;
  name: string;
  slug: string;
  color: string;
}

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [allConnectors, setAllConnectors] = useState<AvailableConnector[]>([]);
  const [allSkills, setAllSkills] = useState<AvailableSkill[]>([]);
  const [allDomains, setAllDomains] = useState<AvailableDomain[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [agentType, setAgentType] = useState("simple");
  const [modelOverride, setModelOverride] = useState("");
  const [isDefault, setIsDefault] = useState(false);
  const [selectedConnectors, setSelectedConnectors] = useState<Set<string>>(new Set());
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());
  const [selectedDomains, setSelectedDomains] = useState<Set<string>>(new Set());

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [agentRes, connectorsRes, skillsRes, domainsRes] = await Promise.all([
        apiClient.get(`/api/v1/admin/agents/${agentId}`),
        apiClient.get("/api/v1/admin/connectors"),
        apiClient.get("/api/v1/admin/skills"),
        apiClient.get("/api/v1/admin/domains"),
      ]);

      if (!agentRes.ok) throw new Error("Agent not found");

      const agentData = await agentRes.json();
      setAgent(agentData);
      setName(agentData.name);
      setDescription(agentData.description || "");
      setSystemPrompt(agentData.system_prompt || "");
      setAgentType(agentData.agent_type);
      setModelOverride(agentData.model_override || "");
      setIsDefault(agentData.is_default);
      setSelectedConnectors(new Set(agentData.connectors.map((c: Connector) => c.slug)));
      setSelectedSkills(new Set(agentData.skills.map((s: Skill) => s.slug)));
      setSelectedDomains(new Set(agentData.domains.map((d: Domain) => d.id)));

      if (connectorsRes.ok) setAllConnectors(await connectorsRes.json());
      if (skillsRes.ok) setAllSkills(await skillsRes.json());
      if (domainsRes.ok) setAllDomains(await domainsRes.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSave = async () => {
    try {
      setSaving(true);
      const res = await apiClient.put(`/api/v1/admin/agents/${agentId}`, {
        name,
        description: description || null,
        system_prompt: systemPrompt || null,
        agent_type: agentType,
        model_override: modelOverride || null,
        is_default: isDefault,
        connector_slugs: Array.from(selectedConnectors),
        skill_slugs: Array.from(selectedSkills),
        domain_ids: Array.from(selectedDomains),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to save");
      }

      router.push("/admin");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const toggleConnector = (slug: string) => {
    setSelectedConnectors((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  };

  const toggleSkill = (slug: string) => {
    setSelectedSkills((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  };

  const toggleDomain = (id: string) => {
    setSelectedDomains((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (loading) {
    return <div className="animate-pulse space-y-4">
      {[1, 2, 3].map((i) => <div key={i} className="h-24 rounded-xl bg-obsidian-900" />)}
    </div>;
  }

  if (error && !agent) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl">
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Basic Info */}
      <section className="space-y-4 rounded-xl border border-white/[0.06] bg-obsidian-900 p-6">
        <h2 className="text-lg font-semibold">Informações Básicas</h2>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs text-neutral-400">Nome</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white focus:border-brand-primary/40 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-neutral-400">Descrição</label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white focus:border-brand-primary/40 focus:outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs text-neutral-400">Tipo</label>
              <select
                value={agentType}
                onChange={(e) => setAgentType(e.target.value)}
                className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white focus:border-brand-primary/40 focus:outline-none"
              >
                <option value="simple">Simple</option>
                <option value="unified">Unified (ITIL)</option>
                <option value="vsa">VSA</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-neutral-400">Modelo (override)</label>
              <input
                value={modelOverride}
                onChange={(e) => setModelOverride(e.target.value)}
                placeholder="Usa modelo padrão"
                className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary/40 focus:outline-none"
              />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-neutral-300">
            <input
              type="checkbox"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="h-4 w-4 rounded border-white/10 bg-obsidian-800 text-brand-primary"
            />
            Agente padrão da organização
          </label>
        </div>
      </section>

      {/* System Prompt */}
      <section className="space-y-4 rounded-xl border border-white/[0.06] bg-obsidian-900 p-6">
        <h2 className="text-lg font-semibold">System Prompt</h2>
        <textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={8}
          placeholder="Deixe vazio para usar o prompt padrão do VSA..."
          className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary/40 focus:outline-none font-mono"
        />
      </section>

      {/* Connectors */}
      <section className="space-y-4 rounded-xl border border-white/[0.06] bg-obsidian-900 p-6">
        <h2 className="text-lg font-semibold">Conectores</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          {allConnectors.map((c) => (
            <button
              key={c.slug}
              onClick={() => toggleConnector(c.slug)}
              className={`flex items-center gap-3 rounded-lg border p-3 text-left text-sm transition-all ${
                selectedConnectors.has(c.slug)
                  ? "border-brand-primary/40 bg-brand-primary/10 text-white"
                  : "border-white/[0.06] bg-obsidian-800 text-neutral-400 hover:border-white/10"
              }`}
            >
              <div className={`h-2 w-2 rounded-full ${selectedConnectors.has(c.slug) ? "bg-emerald-500" : "bg-neutral-600"}`} />
              <div>
                <div className="font-medium">{c.name}</div>
                {c.description && <div className="text-xs text-neutral-500">{c.description}</div>}
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Skills */}
      <section className="space-y-4 rounded-xl border border-white/[0.06] bg-obsidian-900 p-6">
        <h2 className="text-lg font-semibold">Habilidades</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          {allSkills.map((s) => (
            <button
              key={s.slug}
              onClick={() => toggleSkill(s.slug)}
              className={`flex items-center gap-3 rounded-lg border p-3 text-left text-sm transition-all ${
                selectedSkills.has(s.slug)
                  ? "border-blue-500/40 bg-blue-500/10 text-white"
                  : "border-white/[0.06] bg-obsidian-800 text-neutral-400 hover:border-white/10"
              }`}
            >
              <div className={`h-2 w-2 rounded-full ${selectedSkills.has(s.slug) ? "bg-blue-500" : "bg-neutral-600"}`} />
              <div>
                <div className="font-medium">{s.name}</div>
                {s.description && <div className="text-xs text-neutral-500">{s.description}</div>}
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Domains */}
      <section className="space-y-4 rounded-xl border border-white/[0.06] bg-obsidian-900 p-6">
        <h2 className="text-lg font-semibold">Domínios de Conhecimento</h2>
        {allDomains.length === 0 ? (
          <p className="text-sm text-neutral-500">Nenhum domínio criado ainda.</p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            {allDomains.map((d) => (
              <button
                key={d.id}
                onClick={() => toggleDomain(d.id)}
                className={`flex items-center gap-3 rounded-lg border p-3 text-left text-sm transition-all ${
                  selectedDomains.has(d.id)
                    ? "border-purple-500/40 bg-purple-500/10 text-white"
                    : "border-white/[0.06] bg-obsidian-800 text-neutral-400 hover:border-white/10"
                }`}
              >
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: selectedDomains.has(d.id) ? d.color : "#525252" }}
                />
                <div>
                  <div className="font-medium">{d.name}</div>
                  <div className="text-xs text-neutral-500">{d.slug}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-brand-primary px-6 py-2.5 text-sm font-medium text-white hover:bg-brand-primary/80 transition-colors disabled:opacity-50"
        >
          {saving ? "Salvando..." : "Salvar Agente"}
        </button>
        <button
          onClick={() => router.push("/admin")}
          className="rounded-lg border border-white/[0.06] bg-obsidian-800 px-6 py-2.5 text-sm text-neutral-300 hover:bg-white/5 transition-colors"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
