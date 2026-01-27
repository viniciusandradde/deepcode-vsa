"use client";

import React, { useEffect, useState } from "react";
import clsx from "clsx";

/**
 * ThinkingIndicator Component
 * Shows step-by-step progress during AI response generation
 * with VSA agent phases: Classify -> Plan -> Execute -> Analyze -> Integrate
 */

export type ThinkingPhase =
  | "connecting"
  | "classifying"
  | "planning"
  | "executing"
  | "analyzing"
  | "integrating"
  | "responding";

interface PhaseConfig {
  label: string;
  icon: string;
  color: string;
}

const phaseConfig: Record<ThinkingPhase, PhaseConfig> = {
  connecting: {
    label: "Conectando",
    icon: "○",
    color: "text-slate-400",
  },
  classifying: {
    label: "Classificando (ITIL)",
    icon: "◐",
    color: "text-purple-400",
  },
  planning: {
    label: "Planejando ações",
    icon: "◐",
    color: "text-blue-400",
  },
  executing: {
    label: "Executando",
    icon: "◐",
    color: "text-orange-400",
  },
  analyzing: {
    label: "Analisando resultados",
    icon: "◐",
    color: "text-yellow-400",
  },
  integrating: {
    label: "Integrando resposta",
    icon: "◐",
    color: "text-green-400",
  },
  responding: {
    label: "Gerando resposta",
    icon: "●",
    color: "text-vsa-blue-light",
  },
};

const phaseOrder: ThinkingPhase[] = [
  "connecting",
  "classifying",
  "planning",
  "executing",
  "analyzing",
  "integrating",
  "responding",
];

interface ThinkingIndicatorProps {
  phase?: ThinkingPhase;
  currentTool?: string;
  autoProgress?: boolean;
  compact?: boolean;
}

export function ThinkingIndicator({
  phase: externalPhase,
  currentTool,
  autoProgress = true,
  compact = false,
}: ThinkingIndicatorProps) {
  const [internalPhase, setInternalPhase] = useState<ThinkingPhase>("connecting");
  const [dots, setDots] = useState("");

  // Auto-progress through phases if no external phase is provided
  useEffect(() => {
    if (!autoProgress || externalPhase) return;

    const intervals = [800, 1500, 2000, 1500, 1500, 1200, 0]; // Duration for each phase
    let currentIndex = 0;

    const advancePhase = () => {
      if (currentIndex < phaseOrder.length - 1) {
        currentIndex++;
        setInternalPhase(phaseOrder[currentIndex]);
      }
    };

    const timers: NodeJS.Timeout[] = [];
    let elapsed = 0;

    for (let i = 0; i < intervals.length - 1; i++) {
      elapsed += intervals[i];
      const timer = setTimeout(advancePhase, elapsed);
      timers.push(timer);
    }

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [autoProgress, externalPhase]);

  // Animate dots
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 400);
    return () => clearInterval(interval);
  }, []);

  const currentPhase = externalPhase || internalPhase;
  const config = phaseConfig[currentPhase];
  const currentPhaseIndex = phaseOrder.indexOf(currentPhase);

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <div className="flex gap-1">
          <div
            className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse"
            style={{ animationDelay: "0ms" }}
          />
          <div
            className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse"
            style={{ animationDelay: "150ms" }}
          />
          <div
            className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse"
            style={{ animationDelay: "300ms" }}
          />
        </div>
        <span className={`${config.color} animate-pulse`}>
          {config.label}
          {dots}
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Current phase */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          <div
            className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse"
            style={{ animationDelay: "0ms" }}
          />
          <div
            className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse"
            style={{ animationDelay: "150ms" }}
          />
          <div
            className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse"
            style={{ animationDelay: "300ms" }}
          />
        </div>
        <span className={`${config.color} animate-pulse font-medium`}>
          {config.label}
          {dots}
        </span>
      </div>

      {/* Phase progress indicator */}
      <div className="flex items-center gap-1">
        {phaseOrder.map((p, index) => {
          const isCompleted = index < currentPhaseIndex;
          const isCurrent = index === currentPhaseIndex;

          return (
            <div
              key={p}
              className={clsx(
                "h-1 flex-1 rounded-full transition-all duration-300",
                isCompleted && "bg-vsa-orange",
                isCurrent && "bg-vsa-orange/50 animate-pulse",
                !isCompleted && !isCurrent && "bg-slate-700"
              )}
            />
          );
        })}
      </div>

      {/* Tool indicator */}
      {currentTool && (
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="inline-block w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
          <span>
            Chamando: <span className="font-mono text-slate-300">{currentTool}</span>
          </span>
        </div>
      )}

      {/* Phase labels */}
      <div className="flex justify-between text-[9px] uppercase tracking-wider text-slate-500">
        <span className={currentPhaseIndex >= 0 ? "text-slate-400" : ""}>Classificar</span>
        <span className={currentPhaseIndex >= 2 ? "text-slate-400" : ""}>Planejar</span>
        <span className={currentPhaseIndex >= 3 ? "text-slate-400" : ""}>Executar</span>
        <span className={currentPhaseIndex >= 5 ? "text-slate-400" : ""}>Integrar</span>
      </div>
    </div>
  );
}

/**
 * Parse phase from SSE event data
 * The backend can send phase information in the event stream
 */
export function parsePhaseFromEvent(eventData: string): ThinkingPhase | null {
  // Look for phase markers in the event data
  const phasePatterns: Record<string, ThinkingPhase> = {
    "classificando": "classifying",
    "classifying": "classifying",
    "planejando": "planning",
    "planning": "planning",
    "executando": "executing",
    "executing": "executing",
    "analisando": "analyzing",
    "analyzing": "analyzing",
    "integrando": "integrating",
    "integrating": "integrating",
    "respondendo": "responding",
    "responding": "responding",
  };

  const lowerData = eventData.toLowerCase();
  for (const [pattern, phase] of Object.entries(phasePatterns)) {
    if (lowerData.includes(pattern)) {
      return phase;
    }
  }

  return null;
}

export default ThinkingIndicator;
