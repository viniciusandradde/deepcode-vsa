"use client";

import { useEffect, useState, useCallback } from "react";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useGenesisUI } from "@/state/useGenesisUI";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const {
    createSession,
    enableVSA,
    setEnableVSA,
    enableGLPI,
    setEnableGLPI,
    enableZabbix,
    setEnableZabbix,
    enableLinear,
    setEnableLinear,
    enablePlanning,
    setEnablePlanning,
    useTavily,
    setUseTavily,
  } = useGenesisUI();

  const [search, setSearch] = useState("");

  const runAction = useCallback(
    (fn: () => void) => {
      fn();
      onOpenChange(false);
      setSearch("");
    },
    [onOpenChange],
  );

  // Reset search when opening
  useEffect(() => {
    if (open) setSearch("");
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="relative flex items-start justify-center pt-[20vh]">
        <Command
          className="w-full max-w-lg rounded-xl border border-white/[0.06] bg-obsidian-800 shadow-vsa-2xl overflow-hidden"
          label="Command Palette"
          onKeyDown={(e) => {
            if (e.key === "Escape") onOpenChange(false);
          }}
        >
          {/* Input */}
          <div className="flex items-center gap-3 border-b border-white/[0.06] px-4">
            <svg
              className="h-4 w-4 shrink-0 text-neutral-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Digite um comando..."
              className="h-12 w-full bg-transparent text-sm text-white placeholder:text-neutral-600 outline-none"
            />
            <kbd className="hidden sm:inline-flex shrink-0 items-center rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-neutral-500">
              ESC
            </kbd>
          </div>

          {/* List */}
          <Command.List className="max-h-72 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-neutral-500">
              Nenhum resultado encontrado.
            </Command.Empty>

            {/* Navigation */}
            <Command.Group
              heading="Navegar"
              className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-neutral-500"
            >
              <CommandItem
                onSelect={() => runAction(() => router.push("/"))}
                icon={
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                }
                label="Chat"
                shortcut="/"
              />
              <CommandItem
                onSelect={() => runAction(() => router.push("/planning"))}
                icon={
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                }
                label="Planejamento"
              />
              <CommandItem
                onSelect={() => runAction(() => router.push("/automation/scheduler"))}
                icon={
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                }
                label="Automacao / Scheduler"
              />
              <CommandItem
                onSelect={() => runAction(() => router.push("/design"))}
                icon={
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                  />
                }
                label="Design System"
              />
            </Command.Group>

            {/* Actions */}
            <Command.Group
              heading="Acoes"
              className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-neutral-500"
            >
              <CommandItem
                onSelect={() =>
                  runAction(() => {
                    createSession().catch(console.error);
                  })
                }
                icon={
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 4v16m8-8H4"
                  />
                }
                label="Nova Sessao"
                shortcut="Ctrl+N"
              />
            </Command.Group>

            {/* Toggles */}
            <Command.Group
              heading="Integracoes"
              className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-neutral-500"
            >
              <CommandToggle
                label="VSA Agent"
                enabled={enableVSA}
                onSelect={() => runAction(() => setEnableVSA(!enableVSA))}
              />
              <CommandToggle
                label="GLPI"
                enabled={enableGLPI}
                onSelect={() => runAction(() => setEnableGLPI(!enableGLPI))}
              />
              <CommandToggle
                label="Zabbix"
                enabled={enableZabbix}
                onSelect={() => runAction(() => setEnableZabbix(!enableZabbix))}
              />
              <CommandToggle
                label="Linear"
                enabled={enableLinear}
                onSelect={() => runAction(() => setEnableLinear(!enableLinear))}
              />
              <CommandToggle
                label="Planejamento"
                enabled={enablePlanning}
                onSelect={() => runAction(() => setEnablePlanning(!enablePlanning))}
              />
              <CommandToggle
                label="Busca Web (Tavily)"
                enabled={useTavily}
                onSelect={() => runAction(() => setUseTavily(!useTavily))}
              />
            </Command.Group>
          </Command.List>

          {/* Footer */}
          <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-2">
            <span className="text-[11px] text-neutral-600">
              VSA Nexus AI
            </span>
            <div className="flex items-center gap-2 text-[11px] text-neutral-600">
              <span>
                <kbd className="rounded border border-white/10 bg-white/5 px-1 py-0.5">↑↓</kbd> navegar
              </span>
              <span>
                <kbd className="rounded border border-white/10 bg-white/5 px-1 py-0.5">↵</kbd> selecionar
              </span>
            </div>
          </div>
        </Command>
      </div>
    </div>
  );
}

/* ---- Sub-components ---- */

function CommandItem({
  onSelect,
  icon,
  label,
  shortcut,
}: {
  onSelect: () => void;
  icon: React.ReactNode;
  label: string;
  shortcut?: string;
}) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-neutral-300 transition-colors data-[selected=true]:bg-brand-primary/10 data-[selected=true]:text-white"
    >
      <svg
        className="h-4 w-4 shrink-0 text-neutral-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        {icon}
      </svg>
      <span className="flex-1">{label}</span>
      {shortcut && (
        <kbd className="hidden sm:inline-flex shrink-0 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-neutral-600">
          {shortcut}
        </kbd>
      )}
    </Command.Item>
  );
}

function CommandToggle({
  label,
  enabled,
  onSelect,
}: {
  label: string;
  enabled: boolean;
  onSelect: () => void;
}) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-neutral-300 transition-colors data-[selected=true]:bg-brand-primary/10 data-[selected=true]:text-white"
    >
      <span
        className={`h-2 w-2 shrink-0 rounded-full ${
          enabled ? "bg-emerald-400" : "bg-neutral-600"
        }`}
      />
      <span className="flex-1">
        {enabled ? "Desativar" : "Ativar"} {label}
      </span>
      <span
        className={`text-[10px] rounded px-1.5 py-0.5 ${
          enabled
            ? "bg-emerald-500/15 text-emerald-300"
            : "bg-white/5 text-neutral-500"
        }`}
      >
        {enabled ? "ON" : "OFF"}
      </span>
    </Command.Item>
  );
}
