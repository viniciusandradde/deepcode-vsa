"use client";

import React from "react";

/**
 * ITIL Badge Component
 * Displays ITIL classification, GUT score, and priority badges
 * for IT service management responses.
 *
 * Updated: 2026-01-27 - Portuguese (Brazil) terms
 */

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
        color: "bg-red-500 hover:bg-red-600",
        icon: "🔥",
        label: "INCIDENTE",
    },
    problema: {
        color: "bg-orange-500 hover:bg-orange-600",
        icon: "🔍",
        label: "PROBLEMA",
    },
    mudanca: {
        color: "bg-blue-500 hover:bg-blue-600",
        icon: "🔄",
        label: "MUDANÇA",
    },
    requisicao: {
        color: "bg-green-500 hover:bg-green-600",
        icon: "📋",
        label: "REQUISIÇÃO",
    },
    conversa: {
        color: "bg-gray-500 hover:bg-gray-600",
        icon: "💬",
        label: "CONVERSA",
    },
};

const priorityConfig: Record<Priority, { color: string; label: string }> = {
    critico: { color: "bg-red-600", label: "CRÍTICO" },
    alto: { color: "bg-orange-600", label: "ALTO" },
    medio: { color: "bg-yellow-600", label: "MÉDIO" },
    baixo: { color: "bg-gray-600", label: "BAIXO" },
};

/**
 * Get priority based on GUT score
 */
function getPriorityFromGUT(gutScore: number): Priority {
    if (gutScore >= 100) return "critico";
    if (gutScore >= 64) return "alto";
    if (gutScore >= 27) return "medio";
    return "baixo";
}

/**
 * Get GUT score color based on value
 */
function getGUTColor(gutScore: number): string {
    if (gutScore >= 100) return "bg-red-700";
    if (gutScore >= 64) return "bg-orange-700";
    if (gutScore >= 27) return "bg-yellow-700";
    return "bg-gray-700";
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
                    className={`px-2 py-0.5 rounded text-white text-xs font-semibold ${config.color} transition-colors`}
                >
                    {config.icon} {config.label}
                </span>
                {gutScore && (
                    <span
                        className={`px-1.5 py-0.5 rounded text-white text-xs font-mono ${getGUTColor(gutScore)}`}
                    >
                        {gutScore}
                    </span>
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-wrap items-center gap-2 p-2 rounded-lg bg-gray-800/50 border border-gray-700">
            {/* ITIL Type Badge */}
            <span
                className={`px-3 py-1 rounded-md text-white text-xs font-semibold ${config.color} transition-colors shadow-sm`}
            >
                {config.icon} {config.label}
            </span>

            {/* Category Badge */}
            {category && (
                <span className="px-2 py-1 rounded-md bg-gray-600 text-gray-200 text-xs">
                    📁 {category}
                </span>
            )}

            {/* GUT Score Badge */}
            {gutScore !== undefined && (
                <span
                    className={`px-2 py-1 rounded-md text-white text-xs font-mono ${getGUTColor(gutScore)}`}
                    title={`GUT Score: Gravidade × Urgência × Tendência = ${gutScore}`}
                >
                    📊 GUT: {gutScore}
                </span>
            )}

            {/* Priority Badge */}
            {effectivePriority && (
                <span
                    className={`px-2 py-1 rounded-md text-white text-xs ${priorityConfig[effectivePriority].color}`}
                >
                    ⚡ {priorityConfig[effectivePriority].label}
                </span>
            )}
        </div>
    );
}

/**
 * Parse ITIL classification from response text
 * Looks for patterns like:
 * - Tipo: INCIDENTE
 * - GUT Score: 75
 * - Categoria: Infraestrutura
 *
 * Updated: 2026-01-27 - Portuguese terms
 */
export function parseITILFromResponse(text: string): ITILBadgeProps | null {
    // Match type (Portuguese terms)
    const typeMatch = text.match(/Tipo:\s*(INCIDENTE|PROBLEMA|MUDANÇA|REQUISIÇÃO|CONVERSA|INCIDENT|PROBLEM|CHANGE|REQUEST|CHAT)/i);
    if (!typeMatch) return null;

    // Normalize to Portuguese lowercase
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

    // Match GUT Score
    const gutMatch = text.match(/GUT\s*(?:Score)?:\s*(\d+)/i);
    const gutScore = gutMatch ? parseInt(gutMatch[1], 10) : undefined;

    // Match Category
    const categoryMatch = text.match(/Categoria:\s*([^\n\r]+)/i);
    const category = categoryMatch ? categoryMatch[1].trim() : undefined;

    return { type, gutScore, category };
}

export default ITILBadge;
