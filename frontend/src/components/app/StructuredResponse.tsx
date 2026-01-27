"use client";

import React from "react";
import { ITILBadge, type ITILType, type Priority } from "./ITILBadge";

/**
 * StructuredResponse Component
 * Displays structured VSA agent responses with:
 * - ITIL classification badge
 * - Execution plan with step-by-step progress
 * - Summary and recommendations
 */

export type StepStatus = "pending" | "running" | "done" | "error" | "skipped";

export interface PlanStep {
  id: string;
  description: string;
  status: StepStatus;
  tool?: string;
  result?: string;
  error?: string;
}

export interface Classification {
  type: ITILType;
  category?: string;
  gutScore?: number;
  priority?: Priority;
}

export interface StructuredResponseProps {
  classification?: Classification;
  plan?: {
    title?: string;
    steps: PlanStep[];
  };
  summary?: string;
  recommendations?: string[];
  sources?: Array<{
    system: "glpi" | "zabbix" | "linear" | "rag";
    label: string;
    id?: string;
  }>;
  compact?: boolean;
}

const stepStatusConfig: Record<
  StepStatus,
  { icon: string; color: string; bgColor: string }
> = {
  pending: {
    icon: "○",
    color: "text-slate-400",
    bgColor: "bg-slate-700/50",
  },
  running: {
    icon: "◐",
    color: "text-blue-400",
    bgColor: "bg-blue-900/30",
  },
  done: {
    icon: "●",
    color: "text-green-400",
    bgColor: "bg-green-900/30",
  },
  error: {
    icon: "✕",
    color: "text-red-400",
    bgColor: "bg-red-900/30",
  },
  skipped: {
    icon: "—",
    color: "text-slate-500",
    bgColor: "bg-slate-800/50",
  },
};

const sourceConfig: Record<string, { icon: string; color: string }> = {
  glpi: { icon: "🎫", color: "text-purple-400" },
  zabbix: { icon: "📊", color: "text-orange-400" },
  linear: { icon: "📋", color: "text-blue-400" },
  rag: { icon: "📚", color: "text-green-400" },
};

function StepItem({ step, index }: { step: PlanStep; index: number }) {
  const config = stepStatusConfig[step.status];
  const isExpanded = step.status === "error" || step.status === "running";

  return (
    <div
      className={`rounded-lg border border-white/10 ${config.bgColor} transition-all duration-200`}
    >
      <div className="flex items-start gap-3 p-3">
        {/* Step number and status */}
        <div className="flex flex-col items-center">
          <span className="text-xs text-slate-500 font-mono">{index + 1}</span>
          <span
            className={`text-lg ${config.color} ${step.status === "running" ? "animate-pulse" : ""}`}
          >
            {config.icon}
          </span>
        </div>

        {/* Step content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-200">{step.description}</span>
            {step.tool && (
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-700 text-slate-400 font-mono">
                {step.tool}
              </span>
            )}
          </div>

          {/* Expanded details for running/error states */}
          {isExpanded && (
            <div className="mt-2">
              {step.status === "running" && (
                <div className="flex items-center gap-2 text-xs text-blue-400">
                  <span className="inline-block w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                  Executando...
                </div>
              )}
              {step.status === "error" && step.error && (
                <div className="text-xs text-red-400 bg-red-900/20 rounded p-2 mt-1">
                  {step.error}
                </div>
              )}
            </div>
          )}

          {/* Result preview for completed steps */}
          {step.status === "done" && step.result && (
            <div className="mt-1 text-xs text-slate-400 truncate">
              {step.result}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProgressBar({ steps }: { steps: PlanStep[] }) {
  const total = steps.length;
  const done = steps.filter((s) => s.status === "done").length;
  const running = steps.filter((s) => s.status === "running").length;
  const errors = steps.filter((s) => s.status === "error").length;
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">
          {done}/{total} etapas
          {running > 0 && (
            <span className="text-blue-400 ml-2">({running} em execução)</span>
          )}
          {errors > 0 && (
            <span className="text-red-400 ml-2">({errors} com erro)</span>
          )}
        </span>
        <span className="text-slate-400">{percent}%</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-vsa-blue to-vsa-orange transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

export function StructuredResponse({
  classification,
  plan,
  summary,
  recommendations,
  sources,
  compact = false,
}: StructuredResponseProps) {
  if (compact) {
    return (
      <div className="space-y-2">
        {classification && (
          <ITILBadge
            type={classification.type}
            gutScore={classification.gutScore}
            priority={classification.priority}
            category={classification.category}
            compact
          />
        )}
        {plan && plan.steps.length > 0 && <ProgressBar steps={plan.steps} />}
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-xl border border-white/10 bg-slate-900/50 p-4">
      {/* Classification Header */}
      {classification && (
        <div className="border-b border-white/10 pb-3">
          <ITILBadge
            type={classification.type}
            gutScore={classification.gutScore}
            priority={classification.priority}
            category={classification.category}
          />
        </div>
      )}

      {/* Execution Plan */}
      {plan && plan.steps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs uppercase tracking-wider text-slate-500">
              {plan.title || "Plano de Execução"}
            </h4>
          </div>
          <ProgressBar steps={plan.steps} />
          <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
            {plan.steps.map((step, index) => (
              <StepItem key={step.id} step={step} index={index} />
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {summary && (
        <div className="space-y-2">
          <h4 className="text-xs uppercase tracking-wider text-slate-500">
            Resumo
          </h4>
          <p className="text-sm text-slate-300 leading-relaxed">{summary}</p>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs uppercase tracking-wider text-slate-500">
            Recomendações
          </h4>
          <ul className="space-y-1">
            {recommendations.map((rec, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-slate-300"
              >
                <span className="text-vsa-orange mt-0.5">→</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sources */}
      {sources && sources.length > 0 && (
        <div className="border-t border-white/10 pt-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-500">Fontes:</span>
            {sources.map((source, index) => {
              const config = sourceConfig[source.system] || {
                icon: "📄",
                color: "text-slate-400",
              };
              return (
                <span
                  key={index}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-slate-800 ${config.color}`}
                >
                  {config.icon} {source.label}
                  {source.id && (
                    <span className="text-slate-500">#{source.id}</span>
                  )}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Parse structured response from AI text
 * Looks for markdown-style sections in the response
 */
export function parseStructuredResponse(
  text: string
): Partial<StructuredResponseProps> {
  const result: Partial<StructuredResponseProps> = {};

  // Parse ITIL classification
  const typeMatch = text.match(
    /(?:Tipo|Classificação):\s*(INCIDENT|PROBLEM|CHANGE|REQUEST|CHAT)/i
  );
  if (typeMatch) {
    result.classification = {
      type: typeMatch[1].toLowerCase() as ITILType,
    };

    // Parse GUT score
    const gutMatch = text.match(/GUT\s*(?:Score)?:\s*(\d+)/i);
    if (gutMatch && result.classification) {
      result.classification.gutScore = parseInt(gutMatch[1], 10);
    }

    // Parse category
    const categoryMatch = text.match(/Categoria:\s*([^\n\r|]+)/i);
    if (categoryMatch && result.classification) {
      result.classification.category = categoryMatch[1].trim();
    }
  }

  // Parse plan steps (looks for numbered lists under "Plano" section)
  const planMatch = text.match(
    /(?:Plano|Etapas|Steps)[\s:]*\n((?:\d+\.\s+[^\n]+\n?)+)/i
  );
  if (planMatch) {
    const stepsText = planMatch[1];
    const stepLines = stepsText.match(/\d+\.\s+([^\n]+)/g);
    if (stepLines) {
      result.plan = {
        steps: stepLines.map((line, index) => ({
          id: `step-${index}`,
          description: line.replace(/^\d+\.\s+/, "").trim(),
          status: "pending" as StepStatus,
        })),
      };
    }
  }

  // Parse recommendations (looks for bullet points under "Recomendações" section)
  const recMatch = text.match(
    /(?:Recomendações|Recommendations)[\s:]*\n((?:[-•*]\s+[^\n]+\n?)+)/i
  );
  if (recMatch) {
    const recText = recMatch[1];
    const recLines = recText.match(/[-•*]\s+([^\n]+)/g);
    if (recLines) {
      result.recommendations = recLines.map((line) =>
        line.replace(/^[-•*]\s+/, "").trim()
      );
    }
  }

  return result;
}

export default StructuredResponse;
