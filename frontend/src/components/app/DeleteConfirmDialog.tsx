"use client";

import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  sessionTitle?: string;
}

export function DeleteConfirmDialog({
  open,
  onClose,
  onConfirm,
  sessionTitle,
}: DeleteConfirmDialogProps) {
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Deletar Conversa"
      footer={
        <>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="border-slate-300 text-slate-700 hover:border-slate-400"
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleConfirm}
            className="bg-red-200 text-slate-900 hover:bg-red-300"
          >
            Deletar
          </Button>
        </>
      }
    >
      <p className="mb-2">
        Tem certeza que deseja deletar a conversa{" "}
        <span className="font-semibold text-slate-900">
          {sessionTitle || "esta sessão"}
        </span>
        ?
      </p>
      <p className="text-xs text-slate-500">
        Esta ação não pode ser desfeita. Todas as mensagens desta conversa serão
        permanentemente removidas.
      </p>
    </Dialog>
  );
}
