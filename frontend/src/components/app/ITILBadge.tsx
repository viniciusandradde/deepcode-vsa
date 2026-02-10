"use client";

import React from "react";

export type ITILType = "incidente" | "problema" | "mudanca" | "requisicao" | "conversa";
export type Priority = "critico" | "alto" | "medio" | "baixo";

export interface ITILBadgeProps {
    type: ITILType;
    gutScore?: number;
    priority?: Priority;
    category?: string;
    compact?: boolean;
}

const typeConfig: Record<
    ITILType,
    { color: string; icon: string; label: string }
> = {
    incidente: {
        color: "bg-red-500/15 text-red-300 hover:bg-red-500/25",
        icon: "🔥",
        label: "INCIDENTE",
    },
    problema: {
        color: "bg-orange-500/15 text-orange-300 hover:bg-orange-500/25",
        icon: "🔍",
        label: "PROBLEMA",
    },
    mudanca: {
        color: "bg-blue-500/15 text-blue-300 hover:bg-blue-500/25",
        icon: "🔄",
        label: "MUDANÇA",
    },
    requisicao: {
        color: "bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25",
        icon: "📋",
        label: "REQUISIÇÃO",
    },
    conversa: {
        color: "bg-white/5 text-neutral-300 hover:bg-white/10",
        icon: "💬",
        label: "CONVERSA",
    },
};

const priorityConfig: Record<Priority, { color: string; label: string }> = {
    critico: { color: "bg-red-500/15 text-red-300", label: "CRÍTICO" },
    alto: { color: "bg-orange-500/15 text-orange-300", label: "ALTO" },
    medio: { color: "bg-yellow-500/15 text-yellow-300", label: "MÉDIO" },
    baixo: { color: "bg-white/5 text-neutral-300", label: "BAIXO" },
};

function getPriorityFromGUT(gutScore: number): Priority {
    if (gutScore >= 100) return "critico";
    if (gutScore >= 64) return "alto";
    if (gutScore >= 27) return "medio";
    return "baixo";
}

function getGUTColor(gutScore: number): string {
    if (gutScore >= 100) return "bg-red-500/15 text-red-300";
    if (gutScore >= 64) return "bg-orange-500/15 text-orange-300";
    if (gutScore >= 27) return "bg-yellow-500/15 text-yellow-300";
    return "bg-white/5 text-neutral-300";
}

export function ITILBadge({
    type,
    gutScore,
    priority,
    category,
    compact = false,
}: ITILBadgeProps) {
    const config = typeConfig[type] || typeConfig.conversa;
    const effectivePriority = priority || (gutScore ? getPriorityFromGUT(gutScore) : undefined);

    if (compact) {
        return (
            <div className="inline-flex items-center gap-1">
                <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold ${config.color} transition-colors`}
                >
                    {config.icon} {config.label}
                </span>
                {gutScore && (
                    <span
                        className={`px-1.5 py-0.5 rounded text-xs font-mono ${getGUTColor(gutScore)}`}
                    >
                        {gutScore}
                    </span>
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-wrap items-center gap-2 p-2 rounded-lg bg-white/5 border border-white/[0.06]">
            {/* ITIL Type Badge */}
            <span
                className={`px-3 py-1 rounded-md text-xs font-semibold ${config.color} transition-colors`}
            >
                {config.icon} {config.label}
            </span>

            {/* Category Badge */}
            {category && (
                <span className="px-2 py-1 rounded-md bg-white/5 text-neutral-400 text-xs">
                    {category}
                </span>
            )}

            {/* GUT Score Badge */}
            {gutScore !== undefined && (
                <span
                    className={`px-2 py-1 rounded-md text-xs font-mono ${getGUTColor(gutScore)}`}
                    title={`GUT Score: Gravidade × Urgência × Tendência = ${gutScore}`}
                >
                    GUT: {gutScore}
                </span>
            )}

            {/* Priority Badge */}
            {effectivePriority && (
                <span
                    className={`px-2 py-1 rounded-md text-xs ${priorityConfig[effectivePriority].color}`}
                >
                    {priorityConfig[effectivePriority].label}
                </span>
            )}
        </div>
    );
}

export function parseITILFromResponse(text: string): ITILBadgeProps | null {
    const typeMatch = text.match(/Tipo:\s*(INCIDENTE|PROBLEMA|MUDANÇA|REQUISIÇÃO|CONVERSA|INCIDENT|PROBLEM|CHANGE|REQUEST|CHAT)/i);
    if (!typeMatch) return null;

    const typeMap: Record<string, ITILType> = {
        'incidente': 'incidente',
        'incident': 'incidente',
        'problema': 'problema',
        'problem': 'problema',
        'mudança': 'mudanca',
        'mudanca': 'mudanca',
        'change': 'mudanca',
        'requisição': 'requisicao',
        'requisicao': 'requisicao',
        'request': 'requisicao',
        'conversa': 'conversa',
        'chat': 'conversa',
    };

    const type = typeMap[typeMatch[1].toLowerCase()] || 'conversa';

    const gutMatch = text.match(/GUT\s*(?:Score)?:\s*(\d+)/i);
    const gutScore = gutMatch ? parseInt(gutMatch[1], 10) : undefined;

    const categoryMatch = text.match(/Categoria:\s*([^\n\r]+)/i);
    const category = categoryMatch ? categoryMatch[1].trim() : undefined;

    return { type, gutScore, category };
}

export default ITILBadge;
