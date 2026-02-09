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
  glpi_report: "bg-blue-100 text-blue-800 border-blue-300",
  zabbix_report: "bg-red-100 text-red-800 border-red-300",
  linear_report: "bg-violet-100 text-violet-800 border-violet-300",
  dashboard: "bg-amber-100 text-amber-800 border-amber-300",
  itil_classification: "bg-emerald-100 text-emerald-800 border-emerald-300",
  rca_analysis: "bg-orange-100 text-orange-800 border-orange-300",
  fivew2h_analysis: "bg-cyan-100 text-cyan-800 border-cyan-300",
  generic_report: "bg-slate-100 text-slate-800 border-slate-300",
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
        "group/card w-full max-w-md rounded-xl border-2 px-4 py-3 text-left transition-all",
        "hover:shadow-md hover:border-vsa-orange/50 cursor-pointer",
        "border-slate-300 bg-white",
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
          className="ml-auto h-4 w-4 text-slate-400 transition-transform group-hover/card:translate-x-0.5"
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
      <p className="text-sm font-medium text-slate-900 leading-snug">
        {artifact.title}
      </p>
      {preview && (
        <p className="mt-1 text-xs text-slate-500 line-clamp-2 leading-relaxed">
          {preview}...
        </p>
      )}
    </button>
  );
});
