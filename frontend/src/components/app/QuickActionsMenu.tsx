"use client";

import { Popover, PopoverButton, PopoverPanel } from "@headlessui/react";
import { Zap } from "lucide-react";
import clsx from "clsx";
import { SUGGESTIONS } from "./SuggestionChips";

interface QuickActionsMenuProps {
  onSelect: (command: string) => void;
  disabled?: boolean;
}

export function QuickActionsMenu({ onSelect, disabled }: QuickActionsMenuProps) {
  return (
    <Popover className="relative">
      <PopoverButton
        disabled={disabled}
        className={clsx(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border-2 border-slate-300 bg-white text-slate-500 shadow-sm transition hover:border-vsa-orange hover:bg-vsa-orange/5 hover:text-vsa-orange-600 focus:outline-none focus:ring-2 focus:ring-vsa-orange/40",
          disabled && "cursor-not-allowed opacity-50"
        )}
        aria-label="Ações rápidas"
      >
        <Zap className="h-5 w-5" />
      </PopoverButton>
      <PopoverPanel
        anchor="bottom end"
        className="z-50 mt-2 w-72 rounded-xl border-2 border-slate-300 bg-white p-2 shadow-xl"
      >
        {({ close }) => (
          <>
            <div className="mb-2 px-2 py-1 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Ações rápidas
            </div>
            <ul className="space-y-0.5">
              {SUGGESTIONS.map((suggestion) => (
                <li key={suggestion.id}>
                  <button
                    type="button"
                    onClick={() => {
                      close();
                      onSelect(suggestion.command);
                    }}
                    className={clsx(
                      "flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition",
                      suggestion.variant === "warning"
                        ? "text-slate-900 hover:bg-amber-50"
                        : "text-slate-700 hover:bg-vsa-orange/5 hover:text-vsa-orange-700"
                    )}
                  >
                    <span className="shrink-0 [&>svg]:h-4 [&>svg]:w-4">
                      {suggestion.icon}
                    </span>
                    <span className="truncate font-medium">{suggestion.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </PopoverPanel>
    </Popover>
  );
}
