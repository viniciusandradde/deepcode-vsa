"use client";

import { useState } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

export type WriteTarget = "glpi" | "zabbix" | "linear";
export type WriteOperationType = "create" | "update" | "execute";

export interface WriteOperation {
  type: WriteOperationType;
  target: WriteTarget;
  action: string;
  preview: Record<string, unknown>;
  description?: string;
}

interface WriteConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (dryRun: boolean) => void;
  operation: WriteOperation | null;
  isLoading?: boolean;
}

const targetConfig: Record<
  WriteTarget,
  { icon: string; label: string; color: string }
> = {
  glpi: {
    icon: "🎫",
    label: "GLPI",
    color: "text-purple-400 border-purple-500/40 bg-purple-500/10",
  },
  zabbix: {
    icon: "📊",
    label: "Zabbix",
    color: "text-orange-400 border-orange-500/40 bg-orange-500/10",
  },
  linear: {
    icon: "📋",
    label: "Linear",
    color: "text-blue-400 border-blue-500/40 bg-blue-500/10",
  },
};

const operationTypeConfig: Record<
  WriteOperationType,
  { label: string; icon: string; color: string }
> = {
  create: {
    label: "Criar",
    icon: "+",
    color: "text-green-400",
  },
  update: {
    label: "Atualizar",
    icon: "↻",
    color: "text-yellow-400",
  },
  execute: {
    label: "Executar",
    icon: "▶",
    color: "text-blue-400",
  },
};

function JsonPreview({ data }: { data: Record<string, unknown> }) {
  const formatValue = (value: unknown): string => {
    if (value === null) return "null";
    if (value === undefined) return "undefined";
    if (typeof value === "string") return `"${value}"`;
    if (typeof value === "object") return JSON.stringify(value, null, 2);
    return String(value);
  };

  const entries = Object.entries(data);

  return (
    <div className="rounded-lg bg-slate-900/80 border border-white/10 p-3 max-h-48 overflow-y-auto">
      <table className="w-full text-xs font-mono">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key} className="border-b border-white/5 last:border-0">
              <td className="py-1.5 pr-3 text-slate-400 align-top whitespace-nowrap">
                {key}:
              </td>
              <td className="py-1.5 text-slate-200 break-all">
                {typeof value === "object" && value !== null ? (
                  <pre className="whitespace-pre-wrap text-[10px] bg-slate-800/50 rounded p-1.5 mt-1">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                ) : (
                  formatValue(value)
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function WriteConfirmDialog({
  open,
  onClose,
  onConfirm,
  operation,
  isLoading = false,
}: WriteConfirmDialogProps) {
  const [dryRun, setDryRun] = useState(true);

  if (!operation) return null;

  const target = targetConfig[operation.target];
  const opType = operationTypeConfig[operation.type];

  const handleConfirm = () => {
    onConfirm(dryRun);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Confirmar Operação"
      footer={
        <>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={isLoading}
            className="border-slate-400/40 text-slate-300 hover:border-slate-300"
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleConfirm}
            disabled={isLoading}
            className={
              dryRun
                ? "bg-blue-600/80 text-white hover:bg-blue-600"
                : "bg-vsa-orange/80 text-white hover:bg-vsa-orange"
            }
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Executando...
              </span>
            ) : dryRun ? (
              "Simular (Dry-Run)"
            ) : (
              "Confirmar Execução"
            )}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Operation header */}
        <div className="flex items-center gap-3">
          <span
            className={`px-3 py-1.5 rounded-lg border text-sm font-medium ${target.color}`}
          >
            {target.icon} {target.label}
          </span>
          <span className={`text-sm font-medium ${opType.color}`}>
            {opType.icon} {opType.label}
          </span>
        </div>

        {/* Action description */}
        <div className="space-y-1">
          <p className="text-sm text-slate-200 font-medium">{operation.action}</p>
          {operation.description && (
            <p className="text-xs text-slate-400">{operation.description}</p>
          )}
        </div>

        {/* Preview */}
        <div className="space-y-2">
          <h4 className="text-xs uppercase tracking-wider text-slate-500">
            Dados da Operação
          </h4>
          <JsonPreview data={operation.preview} />
        </div>

        {/* Dry-run toggle */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-white/10">
          <div>
            <p className="text-sm text-slate-200">Modo Simulação (Dry-Run)</p>
            <p className="text-xs text-slate-400">
              {dryRun
                ? "Apenas validar, sem executar de fato"
                : "Executar operação real no sistema"}
            </p>
          </div>
          <Switch
            checked={dryRun}
            label=""
            onClick={() => setDryRun(!dryRun)}
          />
        </div>

        {/* Warning for real execution */}
        {!dryRun && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-500/30 text-amber-300">
            <span className="text-lg">⚠️</span>
            <div className="text-xs">
              <p className="font-medium">Atenção: Execução Real</p>
              <p className="text-amber-300/80 mt-0.5">
                Esta operação será executada no {target.label} e não poderá ser
                desfeita automaticamente.
              </p>
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
}

export default WriteConfirmDialog;
