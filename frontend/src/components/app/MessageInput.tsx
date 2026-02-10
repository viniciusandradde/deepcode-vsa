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
    <footer className="safe-area-bottom border-t border-white/[0.06] bg-obsidian-900/80 backdrop-blur-md px-4 md:px-10 py-3 md:py-5">
      <form onSubmit={handleSubmit} className="flex w-full items-start gap-3 md:gap-4">
        <div className="flex-1">
          <div className="flex items-start gap-2">
            <textarea
              id="message-input"
              ref={textareaRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={isLoading ? "Carregando..." : "Digite sua mensagem ou use o microfone..."}
              className="h-20 md:h-[90px] w-full resize-none rounded-xl border border-white/10 bg-obsidian-800 px-4 py-3 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
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
        <div className="flex items-end pt-2 md:pt-[30px]">
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
              "h-12 md:h-[80px] rounded-xl px-4 md:px-6 text-xs md:text-sm font-semibold uppercase tracking-wide focus:outline-none focus:ring-2",
              isSending
                ? "border border-red-500/40 bg-red-900/20 text-red-400 hover:border-red-500/60 hover:bg-red-900/30 focus:ring-red-500/30"
                : "bg-brand-primary text-white hover:bg-brand-primary/80 hover:shadow-glow-orange"
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
