"use client";

import type { KnowledgeSource } from "@/state/types";

interface SourceChipProps {
  source: KnowledgeSource;
  onRemove: () => void;
}

export function SourceChip({ source, onRemove }: SourceChipProps) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border"
      style={{
        borderColor: source.color + "40",
        backgroundColor: source.color + "15",
        color: source.color,
      }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: source.color }}
      />
      @{source.name}
      <button
        type="button"
        className="ml-0.5 hover:opacity-70 transition-opacity"
        onClick={onRemove}
        aria-label={`Remover ${source.name}`}
      >
        &times;
      </button>
    </span>
  );
}
