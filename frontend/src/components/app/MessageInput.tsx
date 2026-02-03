"use client";

import { FormEvent, useRef, useState } from "react";
import clsx from "clsx";
import { Button } from "@/components/ui/button";
import { AudioRecorderButton } from "./AudioRecorderButton";
import { QuickActionsMenu } from "./QuickActionsMenu";

interface MessageInputProps {
  onSubmit: (message: string, streaming: boolean) => Promise<void>;
  isLoading: boolean;
  isSending: boolean;
  onCancel: () => void;
  currentSessionId: string | null;
}

/**
 * Isolated input component to prevent re-renders of parent ChatPane
 * when user types. This significantly improves typing performance.
 */
export function MessageInput({
  onSubmit,
  isLoading,
  isSending,
  onCancel,
  currentSessionId
}: MessageInputProps) {
  const [draft, setDraft] = useState("");
  const [useStreaming, setUseStreaming] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || isLoading || isSending) return;

    const currentDraft = trimmed;
    setDraft("");

    try {
      await onSubmit(currentDraft, useStreaming);
    } catch (error) {
      setDraft(currentDraft);
      console.error("Erro ao enviar mensagem:", error);
    }
  }

  async function handleQuickAction(command: string) {
    if (isLoading || isSending) return;
    try {
      await onSubmit(command, true);
    } catch (error) {
      console.error("Erro ao enviar ação rápida:", error);
    }
  }

  return (
    <footer className="border-t-2 border-slate-300 bg-white px-10 py-5 shadow-sm">
      <form onSubmit={handleSubmit} className="flex w-full items-start gap-4">
        <div className="flex-1">
          <div className="flex items-start gap-2">
            <textarea
              id="message-input"
              ref={textareaRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={isLoading ? "Carregando..." : "Digite sua mensagem ou use o microfone..."}
              className="h-[90px] w-full resize-none rounded-xl border-2 border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-vsa-orange focus:outline-none focus:ring-2 focus:ring-vsa-orange/40"
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSubmit();
                }
              }}
              disabled={isLoading || isSending}
              aria-label="Campo de entrada de mensagem"
              aria-describedby="message-hint"
            />
            <div className="flex items-center gap-2 pt-2">
              <QuickActionsMenu
                onSelect={handleQuickAction}
                disabled={isLoading || isSending}
              />
              <AudioRecorderButton
                onTranscript={(transcript) => {
                  if (transcript) {
                    setDraft((prev) => {
                      const prevText = prev.trim();
                      if (prevText && transcript.startsWith(prevText)) {
                        return transcript;
                      } else if (prevText) {
                        return `${prevText} ${transcript}`;
                      } else {
                        return transcript;
                      }
                    });
                    setTimeout(() => {
                      textareaRef.current?.focus();
                      if (textareaRef.current) {
                        const length = textareaRef.current.value.length;
                        textareaRef.current.setSelectionRange(length, length);
                      }
                    }, 0);
                  }
                }}
                onError={(error) => {
                  console.error("Erro de gravação:", error);
                }}
                silenceTimeout={3000}
              />
            </div>
          </div>
          <p id="message-hint" className="sr-only">
            Pressione Ctrl+Enter ou Cmd+Enter para enviar, ou use o botão de microfone para gravar áudio
          </p>
        </div>
        <div className="flex items-end pt-[30px]">
          <Button
            type={isSending ? "button" : "submit"}
            disabled={isLoading || (!draft.trim() && !isSending)}
            onClick={
              isSending
                ? (e) => {
                    e.preventDefault();
                    onCancel();
                    textareaRef.current?.focus();
                  }
                : undefined
            }
            variant={isSending ? "outline" : "primary"}
            className={clsx(
              "h-[80px] rounded-xl px-6 text-sm font-semibold uppercase tracking-wide shadow-md focus:outline-none focus:ring-2",
              isSending
                ? "border-2 border-red-400 bg-red-50 text-red-800 hover:border-red-500 hover:bg-red-100 focus:ring-red-500/50"
                : "bg-vsa-orange text-white border-vsa-orange-600/30 hover:bg-vsa-orange-600 hover:shadow-vsa-orange"
            )}
            aria-label={isSending ? "Cancelar envio" : "Enviar mensagem"}
          >
            {isSending ? "Cancelar" : "Enviar"}
          </Button>
        </div>
      </form>
    </footer>
  );
}
