"use client";

import { useState } from "react";
import clsx from "clsx";
import { GenesisMessage } from "@/state/useGenesisUI";

interface MessageActionsProps {
  message: GenesisMessage;
  onEdit: () => void;
  onResend?: () => void;
  onCopy?: () => void;
}

export function MessageActions({ message, onEdit, onResend, onCopy }: MessageActionsProps) {
  const [isHovered, setIsHovered] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      if (onCopy) onCopy();
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  return (
    <div
      className={clsx(
        "absolute right-2 top-2 flex gap-1 rounded-md border border-white/10 bg-obsidian-800/95 p-1 shadow-vsa-md transition-opacity",
        isHovered ? "opacity-100" : "opacity-0",
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
        <button
          onClick={onEdit}
          className="rounded p-1.5 text-neutral-500 transition-colors hover:bg-brand-primary/10 hover:text-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          aria-label="Editar mensagem"
          title="Editar mensagem (E)"
        >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
          />
        </svg>
      </button>
      {onResend && (
        <button
          onClick={onResend}
          className="rounded p-1.5 text-neutral-500 transition-colors hover:bg-emerald-500/10 hover:text-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/30"
          aria-label="Reenviar mensagem"
          title="Reenviar mensagem"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>
      )}
        <button
          onClick={handleCopy}
          className="rounded p-1.5 text-neutral-500 transition-colors hover:bg-white/10 hover:text-neutral-300 focus:outline-none focus:ring-2 focus:ring-white/20"
          aria-label="Copiar mensagem"
          title="Copiar mensagem"
        >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
      </button>
    </div>
  );
}
