"use client";

import * as React from "react";
import clsx from "clsx";

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

export interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function Select({
  value,
  onChange,
  options,
  placeholder = "Selecione...",
  disabled = false,
  className,
}: SelectProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const selectRef = React.useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  React.useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen]);

  return (
    <div ref={selectRef} className={clsx("relative", className)}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={clsx(
          "flex w-full items-center justify-between rounded-lg border px-3 py-2.5 text-left transition-all",
          "border-white/10 bg-white/5 text-slate-200",
          "hover:border-cyan-300/40 hover:bg-white/10",
          "focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:ring-offset-2 focus:ring-offset-[#0d1426]",
          disabled && "cursor-not-allowed opacity-50",
          isOpen && "border-cyan-300/60 bg-cyan-400/10",
        )}
      >
        <div className="flex flex-col">
          <span className="text-sm font-semibold uppercase text-slate-100" style={{ fontFamily: "var(--font-sans)" }}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          {selectedOption && selectedOption.description && (
            <span className="text-[11px] text-slate-400 mt-0.5">
              {selectedOption.description}
            </span>
          )}
        </div>
        <svg
          className={clsx(
            "h-4 w-4 text-slate-400 transition-transform",
            isOpen && "rotate-180",
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-white/10 bg-[#0d1426] shadow-xl ring-1 ring-black/20">
          <div className="max-h-60 overflow-auto p-1">
            {options.map((option) => {
              const isSelected = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  className={clsx(
                    "flex w-full flex-col rounded-md px-3 py-2.5 text-left transition-all",
                    isSelected
                      ? "bg-cyan-400/10 text-cyan-100 border border-cyan-300/30"
                      : "text-slate-200 hover:bg-white/5 hover:border-white/10 border border-transparent",
                  )}
                >
                  <span className="text-sm font-semibold uppercase" style={{ fontFamily: "var(--font-sans)" }}>
                    {option.label}
                  </span>
                  {option.description && (
                    <span className="mt-0.5 text-[11px] text-slate-400">
                      {option.description}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

