"use client";

import { FormEvent, useRef, useState } from "react";
import clsx from "clsx";
import { Button } from "@/components/ui/button";
import { AudioRecorderButton } from "./AudioRecorderButton";

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

  return (
    <footer className="border-t border-white/10 px-10 py-5">
      <form onSubmit={handleSubmit} className="flex w-full items-start gap-4">
        <div className="flex-1">
          <label htmlFor="message-input" className="mb-2 block text-[11px] uppercase tracking-[0.35em] text-slate-400">
            Entrada de Comando
          </label>
          <div className="flex items-start gap-2">
            <textarea
              id="message-input"
              ref={textareaRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={isLoading ? "Carregando..." : "Digite sua mensagem ou use o microfone..."}
              className="h-[90px] w-full resize-none rounded-xl border border-white/10 bg-[#0b1526]/90 px-4 py-3 text-sm text-white shadow-[0_0_25px_rgba(62,130,246,0.35)] focus:border-vsa-blue focus:outline-none focus:ring-2 focus:ring-vsa-blue/50"
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
            <div className="flex items-start pt-2">
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
            onClick={isSending ? (e) => {
              e.preventDefault();
              onCancel();
              textareaRef.current?.focus();
            } : undefined}
            className={clsx(
              "h-[80px] rounded-lg border px-6 text-sm uppercase tracking-[0.35em] transition focus:outline-none focus:ring-2",
              isSending
                ? "border-red-500/40 bg-red-500/20 text-red-400 hover:border-red-500 hover:bg-red-500/30 focus:ring-red-500/50"
                : "border-vsa-orange/40 bg-vsa-orange/20 text-vsa-orange-light hover:border-vsa-orange hover:bg-vsa-orange/30 focus:ring-vsa-orange/50"
            )}
            aria-label={isSending ? "Cancelar envio" : "Enviar mensagem"}
          >
            {isSending ? "Cancelar" : "Enviar"}
          </Button>
        </div>
      </form>
      <div className="mt-3 text-[11px] uppercase tracking-[0.3em] text-slate-500">
        Sessão atual: <span className="text-slate-300">{currentSessionId || "—"}</span>
      </div>
    </footer>
  );
}
