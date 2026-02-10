"use client";

import React from "react";

export interface ActionPlanStep {
    step: number;
    title: string;
    description: string;
    status?: "pending" | "in_progress" | "completed" | "failed";
}

export interface ActionPlanProps {
    methodology?: string;
    steps: ActionPlanStep[];
    compact?: boolean;
    onConfirm?: () => void;
    onCancel?: () => void;
    requiresConfirmation?: boolean;
}

const statusConfig = {
    pending: { icon: "⏳", color: "text-neutral-300", bgColor: "bg-white/5" },
    in_progress: { icon: "🔄", color: "text-blue-300", bgColor: "bg-blue-500/10" },
    completed: { icon: "✅", color: "text-emerald-300", bgColor: "bg-emerald-500/10" },
    failed: { icon: "❌", color: "text-red-300", bgColor: "bg-red-500/10" },
};

export function ActionPlan({
    methodology,
    steps,
    compact = false,
    onConfirm,
    onCancel,
    requiresConfirmation = false,
}: ActionPlanProps) {
    if (steps.length === 0) return null;

    if (compact) {
        return (
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-blue-500/10 border border-blue-500/20">
                <span className="text-blue-300 text-xs font-semibold">
                    Plano de Ação ({steps.length} etapas)
                </span>
            </div>
        );
    }

    return (
        <div className="my-3 p-4 rounded-lg bg-obsidian-800 border border-white/[0.06]">
            {/* Header */}
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/[0.06]">
                <span className="text-xl">🎯</span>
                <div className="flex-1">
                    <h3 className="text-sm font-semibold text-white">Plano de Ação</h3>
                    {methodology && (
                        <p className="text-xs text-neutral-500">Metodologia: {methodology}</p>
                    )}
                </div>
                <span className="text-xs text-neutral-400 bg-white/5 px-2 py-1 rounded">
                    {steps.length} etapas
                </span>
            </div>

            {/* Steps List */}
            <div className="space-y-2">
                {steps.map((step, index) => {
                    const status = step.status || "pending";
                    const config = statusConfig[status];

                    return (
                        <div
                            key={index}
                            className={`flex gap-3 p-3 rounded-md transition-colors ${config.bgColor} border border-white/[0.06]`}
                        >
                            {/* Step Number + Status Icon */}
                            <div className="flex-shrink-0 flex flex-col items-center gap-1">
                                <div className="w-6 h-6 flex items-center justify-center rounded-full bg-white/5 border border-white/10 text-xs font-bold text-neutral-400">
                                    {step.step}
                                </div>
                                <span className="text-sm">{config.icon}</span>
                            </div>

                            {/* Step Content */}
                            <div className="flex-1 min-w-0">
                                <h4 className={`text-sm font-semibold ${config.color}`}>
                                    {step.title}
                                </h4>
                                <p className="text-xs text-neutral-500 mt-1 leading-relaxed">
                                    {step.description}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Confirmation Buttons */}
            {requiresConfirmation && (onConfirm || onCancel) && (
                <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between">
                    <p className="text-xs text-neutral-500">
                        Confirmação necessária para executar este plano
                    </p>
                    <div className="flex gap-2">
                        {onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-3 py-1.5 text-xs rounded-md bg-white/5 hover:bg-white/10 text-neutral-400 transition-colors"
                            >
                                Cancelar
                            </button>
                        )}
                        {onConfirm && (
                            <button
                                onClick={onConfirm}
                                className="px-3 py-1.5 text-xs rounded-md bg-brand-primary/15 hover:bg-brand-primary/25 text-brand-primary font-semibold transition-colors border border-brand-primary/30"
                            >
                                Confirmar Execução
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export function parseActionPlanFromResponse(text: string): ActionPlanProps | null {
    const planSectionMatch = text.match(
        /###\s*🎯\s*PLANO DE AÇÃO[\s\S]*?(?=###|$)/i
    );
    if (!planSectionMatch) return null;

    const planSection = planSectionMatch[0];

    const methodologyMatch = planSection.match(/\*\*Metodologia:\*\*\s*([^\n]+)/i);
    const methodology = methodologyMatch ? methodologyMatch[1].trim() : undefined;

    const stepRegex = /(\d+)\.\s*\*\*([^*:]+)\*\*:\s*([^\n]+)/g;
    const steps: ActionPlanStep[] = [];
    let match;

    while ((match = stepRegex.exec(planSection)) !== null) {
        steps.push({
            step: parseInt(match[1], 10),
            title: match[2].trim(),
            description: match[3].trim(),
            status: "pending",
        });
    }

    if (steps.length === 0) {
        const simpleStepRegex = /(\d+)\.\s*([^:]+):\s*([^\n]+)/g;
        while ((match = simpleStepRegex.exec(planSection)) !== null) {
            steps.push({
                step: parseInt(match[1], 10),
                title: match[2].trim(),
                description: match[3].trim(),
                status: "pending",
            });
        }
    }

    if (steps.length === 0) return null;

    return {
        methodology,
        steps,
        requiresConfirmation: false,
    };
}

export function hasActionPlan(text: string): boolean {
    return /###\s*🎯\s*PLANO DE AÇÃO/i.test(text);
}

export default ActionPlan;
