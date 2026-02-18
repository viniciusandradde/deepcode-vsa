"use client";

import { useEffect, useRef, useState } from "react";
import type { KnowledgeSource } from "@/state/types";

interface MentionSelectorProps {
  sources: KnowledgeSource[];
  filter: string;
  onSelect: (source: KnowledgeSource) => void;
  onClose: () => void;
}

export function MentionSelector({ sources, filter, onSelect, onClose }: MentionSelectorProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  const filtered = sources.filter((s) => {
    const q = filter.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.slug.toLowerCase().includes(q) ||
      s.provider.toLowerCase().includes(q)
    );
  });

  // Group by provider
  const grouped = filtered.reduce<Record<string, KnowledgeSource[]>>((acc, s) => {
    if (!acc[s.provider]) acc[s.provider] = [];
    acc[s.provider].push(s);
    return acc;
  }, {});

  // Flat list for keyboard navigation
  const flatList = Object.values(grouped).flat();

  useEffect(() => {
    setActiveIndex(0);
  }, [filter]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, flatList.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (flatList[activeIndex]) {
          onSelect(flatList[activeIndex]);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [activeIndex, flatList, onSelect, onClose]);

  // Scroll active item into view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-index="${activeIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  if (flatList.length === 0) {
    return (
      <div className="absolute bottom-full left-0 mb-2 w-72 rounded-xl border border-white/10 bg-obsidian-900 p-3 shadow-lg">
        <p className="text-xs text-neutral-500">Nenhuma fonte encontrada</p>
      </div>
    );
  }

  let globalIndex = 0;

  return (
    <div
      ref={listRef}
      className="absolute bottom-full left-0 mb-2 w-80 max-h-64 overflow-y-auto rounded-xl border border-white/10 bg-obsidian-900 shadow-lg z-50"
    >
      {Object.entries(grouped).map(([provider, items]) => (
        <div key={provider}>
          <div className="sticky top-0 bg-obsidian-900/95 backdrop-blur px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-neutral-500 border-b border-white/5">
            {provider}
          </div>
          {items.map((source) => {
            const idx = globalIndex++;
            return (
              <button
                key={source.id}
                data-index={idx}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors ${
                  idx === activeIndex
                    ? "bg-white/10 text-white"
                    : "text-neutral-300 hover:bg-white/5"
                }`}
                onClick={() => onSelect(source)}
                onMouseEnter={() => setActiveIndex(idx)}
              >
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: source.color }}
                />
                <span className="font-medium">{source.name}</span>
                {source.meta?.table_count != null && (
                  <span className="ml-auto text-[10px] text-neutral-500">
                    {source.meta.table_count} tabelas
                  </span>
                )}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
