"use client";

import {
  Ticket,
  AlertTriangle,
  LayoutDashboard,
  ListTodo,
  UserX,
  Clock,
} from "lucide-react";
import clsx from "clsx";

interface Suggestion {
  id: string;
  command: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  variant: "default" | "warning";
}

const SUGGESTIONS: Suggestion[] = [
  {
    id: "glpi",
    command: "Listar tickets",
    label: "Tickets GLPI",
    description: "Últimos chamados",
    icon: <Ticket className="h-5 w-5" />,
    variant: "default",
  },
  {
    id: "zabbix",
    command: "Alertas zabbix",
    label: "Alertas Zabbix",
    description: "Problemas ativos",
    icon: <AlertTriangle className="h-5 w-5" />,
    variant: "default",
  },
  {
    id: "dashboard",
    command: "Dashboard",
    label: "Dashboard",
    description: "Visão geral",
    icon: <LayoutDashboard className="h-5 w-5" />,
    variant: "default",
  },
  {
    id: "linear",
    command: "Issues linear",
    label: "Issues Linear",
    description: "Tarefas do time",
    icon: <ListTodo className="h-5 w-5" />,
    variant: "default",
  },
  {
    id: "new-unassigned",
    command: "Chamados novos sem atribuição",
    label: "Novos s/ Atribuição",
    description: "> 24h sem técnico",
    icon: <UserX className="h-5 w-5" />,
    variant: "warning",
  },
  {
    id: "pending-old",
    command: "Chamados pendentes antigos",
    label: "Pendentes > 7 dias",
    description: "Parados há muito tempo",
    icon: <Clock className="h-5 w-5" />,
    variant: "warning",
  },
];

interface SuggestionChipsProps {
  onSelect: (command: string) => void;
  disabled?: boolean;
}

export function SuggestionChips({ onSelect, disabled }: SuggestionChipsProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-3 max-w-3xl">
      {SUGGESTIONS.map((suggestion) => (
        <button
          key={suggestion.id}
          onClick={() => onSelect(suggestion.command)}
          disabled={disabled}
          className={clsx(
            "group flex flex-col items-start gap-1 rounded-xl p-4 text-left transition-all",
            "border bg-white/5 hover:bg-white/10",
            "disabled:cursor-not-allowed disabled:opacity-50",
            suggestion.variant === "warning"
              ? "border-amber-500/30 hover:border-amber-500/50"
              : "border-white/10 hover:border-white/20"
          )}
        >
          <div
            className={clsx(
              "flex items-center gap-2",
              suggestion.variant === "warning"
                ? "text-amber-400"
                : "text-cyan-400"
            )}
          >
            {suggestion.icon}
            <span className="font-medium text-white">{suggestion.label}</span>
          </div>
          <span className="text-xs text-slate-400 group-hover:text-slate-300">
            {suggestion.description}
          </span>
        </button>
      ))}
    </div>
  );
}
