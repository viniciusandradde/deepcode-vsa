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
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleConfirm}
            className="bg-red-500/15 text-red-400 hover:bg-red-500/25"
          >
            Deletar
          </Button>
        </>
      }
    >
      <p className="mb-2 text-neutral-200">
        Tem certeza que deseja deletar a conversa{" "}
        <span className="font-semibold text-white">
          {sessionTitle || "esta sessão"}
        </span>
        ?
      </p>
      <p className="text-xs text-neutral-500">
        Esta ação não pode ser desfeita. Todas as mensagens desta conversa serão
        permanentemente removidas.
      </p>
    </Dialog>
  );
}
