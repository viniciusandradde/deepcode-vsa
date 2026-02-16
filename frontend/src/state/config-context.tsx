"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useLocalStorageState } from "./use-local-storage-state";
import type { ModelOption } from "./types";

export interface AgentOption {
  id: string;
  slug: string;
  name: string;
  description?: string;
  avatar?: string;
  agentType: string;
  isDefault: boolean;
  connectorCount: number;
  skillCount: number;
}

interface ConfigState {
  models: ModelOption[];
  selectedModelId: string;
  setSelectedModelId: (id: string) => void;
  useTavily: boolean;
  setUseTavily: (value: boolean) => void;
  enableVSA: boolean;
  setEnableVSA: (value: boolean) => void;
  enableGLPI: boolean;
  setEnableGLPI: (value: boolean) => void;
  enableZabbix: boolean;
  setEnableZabbix: (value: boolean) => void;
  enableLinear: boolean;
  setEnableLinear: (value: boolean) => void;
  enablePlanning: boolean;
  setEnablePlanning: (value: boolean) => void;
  // Multi-agent support
  agents: AgentOption[];
  selectedAgentId: string;
  setSelectedAgentId: (id: string) => void;
}

const ConfigContext = createContext<ConfigState | null>(null);

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [useTavily, setUseTavily] = useLocalStorageState('vsa_useTavily', false);
  const [enableVSA, setEnableVSA] = useLocalStorageState('vsa_enableVSA', false);
  const [enableGLPI, setEnableGLPI] = useLocalStorageState('vsa_enableGLPI', false);
  const [enableZabbix, setEnableZabbix] = useLocalStorageState('vsa_enableZabbix', false);
  const [enableLinear, setEnableLinear] = useLocalStorageState('vsa_enableLinear', false);
  const [enablePlanning, setEnablePlanning] = useLocalStorageState('vsa_enablePlanning', false);

  // Multi-agent state
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useLocalStorageState<string>('vsa_selectedAgentId', '');

  useEffect(() => {
    async function loadModels() {
      try {
        const res = await fetch("/api/models", { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        const mapped: ModelOption[] = (data.models ?? []).map((model: any) => ({
          id: model.id,
          label: model.label,
          inputCost: model.input_cost ?? 0,
          outputCost: model.output_cost ?? 0,
          isDefault: model.default ?? false,
        }));
        setModels(mapped);
        const defaultModel = mapped.find(m => m.isDefault) ?? mapped[0];
        if (defaultModel) {
          setSelectedModelId((prev) => prev || defaultModel.id);
        }
      } catch (error) {
        console.error("Error loading models:", error);
      }
    }
    loadModels();
  }, []);

  // Load agents from API
  useEffect(() => {
    async function loadAgents() {
      try {
        const res = await fetch("/api/v1/admin/agents", { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        const mapped: AgentOption[] = (data ?? []).map((agent: any) => ({
          id: agent.id,
          slug: agent.slug,
          name: agent.name,
          description: agent.description,
          avatar: agent.avatar,
          agentType: agent.agent_type,
          isDefault: agent.is_default,
          connectorCount: agent.connector_count ?? 0,
          skillCount: agent.skill_count ?? 0,
        }));
        setAgents(mapped);
        // Auto-select default agent if none selected
        if (!selectedAgentId) {
          const defaultAgent = mapped.find(a => a.isDefault) ?? mapped[0];
          if (defaultAgent) {
            setSelectedAgentId(defaultAgent.id);
          }
        }
      } catch (error) {
        // Agents API not available yet (schema not applied) - silently ignore
        console.debug("Agents API not available:", error);
      }
    }
    loadAgents();
  }, []);

  const value = useMemo<ConfigState>(
    () => ({
      models,
      selectedModelId,
      setSelectedModelId,
      useTavily,
      setUseTavily,
      enableVSA,
      setEnableVSA,
      enableGLPI,
      setEnableGLPI,
      enableZabbix,
      setEnableZabbix,
      enableLinear,
      setEnableLinear,
      enablePlanning,
      setEnablePlanning,
      agents,
      selectedAgentId,
      setSelectedAgentId,
    }),
    [
      models,
      selectedModelId,
      useTavily,
      setUseTavily,
      enableVSA,
      setEnableVSA,
      enableGLPI,
      setEnableGLPI,
      enableZabbix,
      setEnableZabbix,
      enableLinear,
      setEnableLinear,
      enablePlanning,
      setEnablePlanning,
      agents,
      selectedAgentId,
      setSelectedAgentId,
    ],
  );

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
}

export function useConfig() {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error("useConfig must be used within ConfigProvider");
  }
  return context;
}
