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
    color: "text-slate-900 border-purple-300 bg-purple-50",
  },
  zabbix: {
    icon: "📊",
    label: "Zabbix",
    color: "text-slate-900 border-orange-300 bg-orange-50",
  },
  linear: {
    icon: "📋",
    label: "Linear",
    color: "text-slate-900 border-blue-300 bg-blue-50",
  },
};

const operationTypeConfig: Record<
  WriteOperationType,
  { label: string; icon: string; color: string }
> = {
  create: {
    label: "Criar",
    icon: "+",
    color: "text-slate-900",
  },
  update: {
    label: "Atualizar",
    icon: "↻",
    color: "text-slate-900",
  },
  execute: {
    label: "Executar",
    icon: "▶",
    color: "text-slate-900",
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
    <div className="rounded-lg bg-slate-50 border-2 border-slate-200 p-3 max-h-48 overflow-y-auto shadow-sm">
      <table className="w-full text-xs font-mono">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key} className="border-b-2 border-slate-200 last:border-0">
              <td className="py-1.5 pr-3 text-slate-600 align-top whitespace-nowrap">
                {key}:
              </td>
              <td className="py-1.5 text-slate-800 break-all">
                {typeof value === "object" && value !== null ? (
                  <pre className="whitespace-pre-wrap text-[10px] bg-slate-100 rounded p-1.5 mt-1">
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
            className="border-slate-300 text-slate-700 hover:border-slate-400"
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
                ? "bg-blue-100 text-slate-900 hover:bg-blue-200"
                : "bg-vsa-orange/20 text-slate-900 hover:bg-vsa-orange/30"
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
            className={`px-3 py-1.5 rounded-lg border-2 text-sm font-medium ${target.color}`}
          >
            {target.icon} {target.label}
          </span>
          <span className={`text-sm font-medium ${opType.color}`}>
            {opType.icon} {opType.label}
          </span>
        </div>

        {/* Action description */}
        <div className="space-y-1">
          <p className="text-sm text-slate-800 font-medium">{operation.action}</p>
          {operation.description && (
            <p className="text-xs text-slate-500">{operation.description}</p>
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
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border-2 border-slate-200 shadow-sm">
          <div>
            <p className="text-sm text-slate-700">Modo Simulação (Dry-Run)</p>
            <p className="text-xs text-slate-500">
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
          <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 border-2 border-amber-200 text-slate-900 shadow-sm">
            <span className="text-lg">⚠️</span>
            <div className="text-xs">
              <p className="font-medium">Atenção: Execução Real</p>
              <p className="text-slate-900 mt-0.5">
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
