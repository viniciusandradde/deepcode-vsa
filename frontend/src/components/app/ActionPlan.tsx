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
    pending: { icon: "⏳", color: "text-gray-400", bgColor: "bg-gray-800" },
    in_progress: { icon: "🔄", color: "text-blue-400", bgColor: "bg-blue-900/30" },
    completed: { icon: "✅", color: "text-green-400", bgColor: "bg-green-900/30" },
    failed: { icon: "❌", color: "text-red-400", bgColor: "bg-red-900/30" },
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
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-blue-900/30 border border-blue-700/50">
                <span className="text-blue-400 text-xs font-semibold">
                    🎯 Plano de Ação ({steps.length} etapas)
                </span>
            </div>
        );
    }

    return (
        <div className="my-3 p-4 rounded-lg bg-gray-800/80 border border-gray-700 shadow-lg">
            {/* Header */}
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-700">
                <span className="text-xl">🎯</span>
                <div className="flex-1">
                    <h3 className="text-sm font-semibold text-white">Plano de Ação</h3>
                    {methodology && (
                        <p className="text-xs text-gray-400">Metodologia: {methodology}</p>
                    )}
                </div>
                <span className="text-xs text-gray-400 bg-gray-900 px-2 py-1 rounded">
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
                            className={`flex gap-3 p-3 rounded-md transition-colors ${config.bgColor} border border-gray-700/50`}
                        >
                            {/* Step Number + Status Icon */}
                            <div className="flex-shrink-0 flex flex-col items-center gap-1">
                                <div className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-900 text-xs font-bold text-gray-300">
                                    {step.step}
                                </div>
                                <span className="text-sm">{config.icon}</span>
                            </div>

                            {/* Step Content */}
                            <div className="flex-1 min-w-0">
                                <h4 className={`text-sm font-semibold ${config.color}`}>
                                    {step.title}
                                </h4>
                                <p className="text-xs text-gray-300 mt-1 leading-relaxed">
                                    {step.description}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Confirmation Buttons (Task 2.8 - Future) */}
            {requiresConfirmation && (onConfirm || onCancel) && (
                <div className="mt-4 pt-3 border-t border-gray-700 flex items-center justify-between">
                    <p className="text-xs text-gray-400">
                        ⚠️ Confirmação necessária para executar este plano
                    </p>
                    <div className="flex gap-2">
                        {onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-3 py-1.5 text-xs rounded-md bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                            >
                                Cancelar
                            </button>
                        )}
                        {onConfirm && (
                            <button
                                onClick={onConfirm}
                                className="px-3 py-1.5 text-xs rounded-md bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
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
