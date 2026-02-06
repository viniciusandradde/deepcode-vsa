"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useLocalStorageState } from "./use-local-storage-state";
import type { ModelOption } from "./types";

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
