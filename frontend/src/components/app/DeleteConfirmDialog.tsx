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
            className="border-slate-400/40 text-slate-300 hover:border-slate-300"
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleConfirm}
            className="bg-red-600/80 text-white hover:bg-red-600"
          >
            Deletar
          </Button>
        </>
      }
    >
      <p className="mb-2">
        Tem certeza que deseja deletar a conversa{" "}
        <span className="font-semibold text-vsa-orange-light">
          {sessionTitle || "esta sessão"}
        </span>
        ?
      </p>
      <p className="text-xs text-slate-400">
        Esta ação não pode ser desfeita. Todas as mensagens desta conversa serão
        permanentemente removidas.
      </p>
    </Dialog>
  );
}

