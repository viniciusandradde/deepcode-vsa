"use client";

import { memo } from "react";
import clsx from "clsx";
import type { Artifact, ArtifactType } from "@/state/artifact-types";

const TYPE_LABELS: Record<ArtifactType, string> = {
  glpi_report: "GLPI",
  zabbix_report: "Zabbix",
  linear_report: "Linear",
  dashboard: "Dashboard",
  itil_classification: "ITIL",
  rca_analysis: "RCA",
  fivew2h_analysis: "5W2H",
  generic_report: "Relatório",
};

const TYPE_COLORS: Record<ArtifactType, string> = {
  glpi_report: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  zabbix_report: "bg-red-500/15 text-red-300 border-red-500/30",
  linear_report: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  dashboard: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  itil_classification: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  rca_analysis: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  fivew2h_analysis: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
  generic_report: "bg-white/5 text-neutral-300 border-white/10",
};

interface ArtifactCardProps {
  artifact: Artifact;
  onOpen: (id: string) => void;
}

export const ArtifactCard = memo(function ArtifactCard({
  artifact,
  onOpen,
}: ArtifactCardProps) {
  const label = TYPE_LABELS[artifact.type] || "Relatório";
  const colorClass = TYPE_COLORS[artifact.type] || TYPE_COLORS.generic_report;

  // Preview: first ~120 chars of markdown, stripped of formatting
  const preview = artifact.content
    .replace(/#{1,6}\s/g, "")
    .replace(/\|/g, "")
    .replace(/[-*_]{3,}/g, "")
    .replace(/\n+/g, " ")
    .trim()
    .slice(0, 120);

  return (
    <button
      onClick={() => onOpen(artifact.id)}
      className={clsx(
        "group/card w-full max-w-md rounded-xl border px-4 py-3 text-left transition-all",
        "hover:border-brand-primary/40 hover:shadow-glow-orange cursor-pointer",
        "border-white/[0.06] glass-panel",
      )}
    >
      <div className="flex items-center gap-2 mb-1.5">
        {/* Type badge */}
        <span
          className={clsx(
            "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
            colorClass,
          )}
        >
          {label}
        </span>
        {/* Arrow icon */}
        <svg
          className="ml-auto h-4 w-4 text-neutral-600 transition-transform group-hover/card:translate-x-0.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
      <p className="text-sm font-medium text-white leading-snug">
        {artifact.title}
      </p>
      {preview && (
        <p className="mt-1 text-xs text-neutral-500 line-clamp-2 leading-relaxed">
          {preview}...
        </p>
      )}
    </button>
  );
});
