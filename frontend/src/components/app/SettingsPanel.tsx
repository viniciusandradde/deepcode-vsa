"use client";

import { useState } from "react";
import clsx from "clsx";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

export function SettingsPanel() {
  const { useTavily, setUseTavily, selectedModelId, models, setSelectedModelId } = useGenesisUI();
  const [isOpen, setIsOpen] = useState(false);
  const [enableStreaming, setEnableStreaming] = useState(true);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [temperature, setTemperature] = useState(0.7);

  return (
    <>
      <Button
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        size="sm"
        className="mb-4 border-vsa-blue/40 text-vsa-blue-light hover:bg-vsa-blue/10"
      >
        {isOpen ? "Ocultar" : "Mostrar"} Configurações Avançadas
      </Button>

      {isOpen && (
        <Card className="mb-4 border-white/10 bg-white/5">
          <CardHeader>
            <h3 className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-200">
              Configurações Avançadas
            </h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="block text-xs uppercase tracking-[0.35em] text-slate-400">
                Streaming de Respostas
              </label>
              <Switch
                checked={enableStreaming}
                label={enableStreaming ? "Ativado" : "Desativado"}
                onClick={() => setEnableStreaming(!enableStreaming)}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs uppercase tracking-[0.35em] text-slate-400">
                Máximo de Tokens: {maxTokens}
              </label>
              <input
                type="range"
                min="100"
                max="4000"
                step="100"
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs uppercase tracking-[0.35em] text-slate-400">
                Temperatura: {temperature.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="pt-2 text-xs text-slate-400">
              <p>Modelo atual: {selectedModelId}</p>
              <p>Busca Web: {useTavily ? "Ativa" : "Inativa"}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}

