"use client";

import { useState } from "react";
import clsx from "clsx";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

export function SettingsPanel() {
    const {
        useTavily,
        setUseTavily,
        selectedModelId,
        models,
        setSelectedModelId,
        // VSA Integration states (Task 1.2, 1.3)
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
    } = useGenesisUI();
    const [isOpen, setIsOpen] = useState(false);
    const [enableStreaming, setEnableStreaming] = useState(true);
    const [maxTokens, setMaxTokens] = useState(1000);
    const [temperature, setTemperature] = useState(0.7);

    return (
        <>
            <div className="flex flex-col gap-2 mb-4">
                <Button
                    onClick={() => setIsOpen(!isOpen)}
                    variant="outline"
                    size="sm"
                >
                    {isOpen ? "Ocultar" : "Mostrar"} Configurações
                </Button>
            </div>

            {isOpen && (
                <Card className="mb-4">
                    <CardHeader>
                        <h3 className="text-sm font-semibold uppercase tracking-[0.35em] text-neutral-400">
                            Configurações
                        </h3>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* VSA Mode Toggle (Task 1.2, 1.3) */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-semibold text-sm text-neutral-300">Modo VSA (Gestão de TI)</h4>
                                    <p className="text-xs text-neutral-500">
                                        Ativa integrações GLPI, Zabbix e Linear
                                    </p>
                                </div>
                                <Switch
                                    checked={enableVSA}
                                    label={enableVSA ? "Ativo" : "Inativo"}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        setEnableVSA(!enableVSA);
                                    }}
                                />
                            </div>

                            {/* Integration toggles - only shown when VSA mode is enabled */}
                            {enableVSA && (
                                <div className="border-l-2 border-brand-primary/30 pl-4 space-y-3 ml-2">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="text-sm text-neutral-300">GLPI</span>
                                            <p className="text-xs text-neutral-500">Tickets e chamados</p>
                                        </div>
                                        <Switch
                                            checked={enableGLPI}
                                            label=""
                                            onClick={(e) => {
                                                e.preventDefault();
                                                setEnableGLPI(!enableGLPI);
                                            }}
                                        />
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="text-sm text-neutral-300">Zabbix</span>
                                            <p className="text-xs text-neutral-500">Alertas e monitoramento</p>
                                        </div>
                                        <Switch
                                            checked={enableZabbix}
                                            label=""
                                            onClick={(e) => {
                                                e.preventDefault();
                                                setEnableZabbix(!enableZabbix);
                                            }}
                                        />
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="text-sm text-neutral-300">Linear</span>
                                            <p className="text-xs text-neutral-500">Issues e projetos</p>
                                        </div>
                                        <Switch
                                            checked={enableLinear}
                                            label=""
                                            onClick={(e) => {
                                                e.preventDefault();
                                                setEnableLinear(!enableLinear);
                                            }}
                                        />
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="text-sm text-neutral-300">Planejamento</span>
                                            <p className="text-xs text-neutral-500">Projetos, documentos e análise no chat</p>
                                        </div>
                                        <Switch
                                            checked={enablePlanning}
                                            label=""
                                            onClick={(e) => {
                                                e.preventDefault();
                                                setEnablePlanning(!enablePlanning);
                                            }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="border-t border-white/[0.06] pt-4 space-y-4">
                            {/* Model Selection Dropdown */}
                            <div className="space-y-2">
                                <label className="block text-xs uppercase tracking-[0.35em] text-neutral-500">
                                    Modelo de IA
                                </label>
                                <select
                                    value={selectedModelId}
                                    onChange={(e) => setSelectedModelId(e.target.value)}
                                    className="w-full rounded-lg border border-white/10 bg-obsidian-800 px-3 py-2 text-sm text-white focus:border-brand-primary focus:outline-none"
                                >
                                    {models.map((model) => (
                                        <option key={model.id} value={model.id}>
                                            {model.label} {model.isDefault && "(Padrão)"}
                                        </option>
                                    ))}
                                </select>
                                <p className="text-xs text-neutral-500">
                                    Custo: ${models.find(m => m.id === selectedModelId)?.inputCost?.toFixed(2) ?? "0.00"}/1M tokens
                                </p>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-xs uppercase tracking-[0.35em] text-neutral-500">
                                    Busca Web (Tavily)
                                </label>
                                <Switch
                                    checked={useTavily}
                                    label={useTavily ? "Ativado" : "Desativado"}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        setUseTavily(!useTavily);
                                    }}
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="block text-xs uppercase tracking-[0.35em] text-neutral-500">
                                    Streaming de Respostas
                                </label>
                                <Switch
                                    checked={enableStreaming}
                                    label={enableStreaming ? "Ativado" : "Desativado"}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        setEnableStreaming(!enableStreaming);
                                    }}
                                />
                            </div>

                            <div className="pt-2 text-xs text-neutral-500">
                                <p>Modelo: {selectedModelId}</p>
                                <p>Busca Web: {useTavily ? "Ativa" : "Inativa"}</p>
                                {enableVSA && (
                                    <p className="text-neutral-400">
                                        VSA: {[
                                            enableGLPI && "GLPI",
                                            enableZabbix && "Zabbix",
                                            enableLinear && "Linear",
                                            enablePlanning && "Planejamento"
                                        ].filter(Boolean).join(", ") || "Nenhum"}
                                    </p>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </>
    );
}
