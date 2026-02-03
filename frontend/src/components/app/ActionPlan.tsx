"use client";

import React from "react";

/**
 * Action Plan Component (Task 2.6)
 * Displays structured action plans for ITIL-based workflows
 */

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
    pending: { icon: "⏳", color: "text-slate-900", bgColor: "bg-slate-100" },
    in_progress: { icon: "🔄", color: "text-slate-900", bgColor: "bg-blue-50" },
    completed: { icon: "✅", color: "text-slate-900", bgColor: "bg-green-50" },
    failed: { icon: "❌", color: "text-slate-900", bgColor: "bg-red-50" },
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
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-blue-50 border-2 border-blue-300 shadow-sm">
                <span className="text-slate-900 text-xs font-semibold">
                    🎯 Plano de Ação ({steps.length} etapas)
                </span>
            </div>
        );
    }

    return (
        <div className="my-3 p-4 rounded-lg bg-white border-2 border-slate-300 shadow-sm">
            {/* Header */}
            <div className="flex items-center gap-2 mb-3 pb-2 border-b-2 border-slate-300">
                <span className="text-xl">🎯</span>
                <div className="flex-1">
                    <h3 className="text-sm font-semibold text-slate-800">Plano de Ação</h3>
                    {methodology && (
                        <p className="text-xs text-slate-500">Metodologia: {methodology}</p>
                    )}
                </div>
                <span className="text-xs text-slate-600 bg-slate-100 px-2 py-1 rounded">
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
                            className={`flex gap-3 p-3 rounded-md transition-colors ${config.bgColor} border-2 border-slate-300 shadow-sm`}
                        >
                            {/* Step Number + Status Icon */}
                            <div className="flex-shrink-0 flex flex-col items-center gap-1">
                                <div className="w-6 h-6 flex items-center justify-center rounded-full bg-white border-2 border-slate-300 text-xs font-bold text-slate-600">
                                    {step.step}
                                </div>
                                <span className="text-sm">{config.icon}</span>
                            </div>

                            {/* Step Content */}
                            <div className="flex-1 min-w-0">
                                <h4 className={`text-sm font-semibold ${config.color}`}>
                                    {step.title}
                                </h4>
                                <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                                    {step.description}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Confirmation Buttons (Task 2.8 - Future) */}
            {requiresConfirmation && (onConfirm || onCancel) && (
                <div className="mt-4 pt-3 border-t-2 border-slate-300 flex items-center justify-between">
                    <p className="text-xs text-slate-600">
                        ⚠️ Confirmação necessária para executar este plano
                    </p>
                    <div className="flex gap-2">
                        {onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-3 py-1.5 text-xs rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                            >
                                Cancelar
                            </button>
                        )}
                        {onConfirm && (
                            <button
                                onClick={onConfirm}
                                className="px-3 py-1.5 text-xs rounded-md bg-vsa-orange/20 hover:bg-vsa-orange/30 text-slate-900 font-semibold transition-colors border-2 border-vsa-orange/30"
                            >
                                ✓ Confirmar Execução
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

/**
 * Parse Action Plan from response text (Task 2.6)
 * Looks for the "🎯 PLANO DE AÇÃO" section
 */
export function parseActionPlanFromResponse(text: string): ActionPlanProps | null {
    // Look for "### 🎯 PLANO DE AÇÃO" section
    const planSectionMatch = text.match(
        /###\s*🎯\s*PLANO DE AÇÃO[\s\S]*?(?=###|$)/i
    );
    if (!planSectionMatch) return null;

    const planSection = planSectionMatch[0];

    // Extract methodology
    const methodologyMatch = planSection.match(/\*\*Metodologia:\*\*\s*([^\n]+)/i);
    const methodology = methodologyMatch ? methodologyMatch[1].trim() : undefined;

    // Extract steps (numbered list pattern)
    // Matches: 1. **Title**: Description
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

    // Alternative pattern without bold:
    // 1. Title: Description
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
        requiresConfirmation: false, // Future: detect WRITE operations
    };
}

/**
 * Detect if text contains an action plan section
 */
export function hasActionPlan(text: string): boolean {
    return /###\s*🎯\s*PLANO DE AÇÃO/i.test(text);
}

export default ActionPlan;
