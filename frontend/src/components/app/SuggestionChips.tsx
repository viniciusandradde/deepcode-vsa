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

export interface Suggestion {
  id: string;
  command: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  variant: "default" | "warning";
}

export const SUGGESTIONS: Suggestion[] = [
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
  {
    id: "excel-cost-center",
    command: "Gerar relatório Excel de atendimentos por centro de custo do mês anterior",
    label: "Relatório C. Custo",
    description: "Mês Anterior (Excel)",
    icon: <LayoutDashboard className="h-5 w-5" />,
    variant: "default",
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
            "glass-panel border border-white/[0.06] hover:border-brand-primary/40 hover:shadow-glow-orange",
            "disabled:cursor-not-allowed disabled:opacity-50",
            suggestion.variant === "warning"
              ? "border-amber-500/20 hover:border-amber-500/40"
              : ""
          )}
        >
          <div className="flex items-center gap-2 text-white">
            <span className="text-brand-primary group-hover:text-brand-primary/80 transition-colors">
              {suggestion.icon}
            </span>
            <span className="font-medium">{suggestion.label}</span>
          </div>
          <span className="text-xs text-neutral-500 group-hover:text-neutral-400">
            {suggestion.description}
          </span>
        </button>
      ))}
    </div>
  );
}
