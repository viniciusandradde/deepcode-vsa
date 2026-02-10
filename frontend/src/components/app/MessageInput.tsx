"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Button } from "@/components/ui/button";
import { AudioRecorderButton } from "./AudioRecorderButton";
import { QuickActionsMenu } from "./QuickActionsMenu";
import type { FileAttachment } from "@/state/types";

interface MessageInputProps {
  onSubmit: (message: string, streaming: boolean, attachments?: FileAttachment[]) => Promise<void>;
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
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_SIZE_BYTES = 4 * 1024 * 1024;
  const ALLOWED_MIME = new Set([
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "image/png",
    "image/jpeg",
  ]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const viewport = window.visualViewport;
    if (!viewport) return;

    const updateKeyboardOffset = () => {
      const offset = Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop);
      document.documentElement.style.setProperty("--keyboard-offset", `${offset}px`);
    };

    updateKeyboardOffset();
    viewport.addEventListener("resize", updateKeyboardOffset);
    viewport.addEventListener("scroll", updateKeyboardOffset);

    return () => {
      viewport.removeEventListener("resize", updateKeyboardOffset);
      viewport.removeEventListener("scroll", updateKeyboardOffset);
    };
  }, []);

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = draft.trim();
    if ((!trimmed && attachments.length === 0) || isLoading || isSending || uploading) return;

    const currentDraft = trimmed || "Analise os anexos.";
    setDraft("");
    setUploadError(null);

    try {
      await onSubmit(currentDraft, useStreaming, attachments);
      setAttachments([]);
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

  async function handleFilesSelected(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploadError(null);

    const pending = Array.from(files);
    const invalid = pending.find((f) => !ALLOWED_MIME.has(f.type));
    if (invalid) {
      setUploadError("Tipo de arquivo não suportado.");
      return;
    }
    const oversized = pending.find((f) => f.size > MAX_SIZE_BYTES);
    if (oversized) {
      setUploadError("Arquivo excede o limite de 4MB.");
      return;
    }

    setUploading(true);
    try {
      const uploaded = await Promise.all(
        pending.map(async (file) => {
          const formData = new FormData();
          formData.append("file", file);
          if (currentSessionId) {
            formData.append("thread_id", currentSessionId);
          }
          const res = await fetch("/api/files/upload", {
            method: "POST",
            body: formData,
          });
          if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data?.detail || "Falha ao enviar arquivo");
          }
          const data = await res.json();
          return {
            id: data.file_id,
            name: data.name,
            mime: data.mime,
            size: data.size,
            url: data.url,
          } as FileAttachment;
        })
      );
      setAttachments((prev) => [...prev, ...uploaded]);
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Falha ao enviar arquivo";
      setUploadError(msg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  return (
    <footer className="keyboard-safe border-t border-white/[0.06] bg-obsidian-900/80 backdrop-blur-md px-4 md:px-10 py-3 md:py-5">
      <form onSubmit={handleSubmit} className="flex w-full flex-col gap-3 md:flex-row md:items-start md:gap-4">
        <div className="flex-1">
          {attachments.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachments.map((att) => (
                <div
                  key={att.id}
                  className="flex items-center gap-2 rounded-lg border border-white/10 bg-obsidian-800/60 px-3 py-2 text-xs text-neutral-300"
                >
                  {att.mime.startsWith("image/") ? (
                    <img src={att.url} alt={att.name} className="h-8 w-8 rounded object-cover" />
                  ) : (
                    <span className="h-8 w-8 rounded bg-white/10 flex items-center justify-center text-[10px] text-neutral-400">
                      DOC
                    </span>
                  )}
                  <div className="flex flex-col">
                    <span className="max-w-[140px] truncate">{att.name}</span>
                    <span className="text-[10px] text-neutral-500">
                      {(att.size / 1024).toFixed(0)} KB
                    </span>
                  </div>
                  <button
                    type="button"
                    className="ml-1 text-neutral-500 hover:text-white"
                    onClick={() => setAttachments((prev) => prev.filter((item) => item.id !== att.id))}
                    aria-label="Remover anexo"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
          {uploadError && (
            <div className="mb-2 text-xs text-red-400">{uploadError}</div>
          )}
          <textarea
            id="message-input"
            ref={textareaRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={isLoading ? "Carregando..." : "Digite sua mensagem..."}
            className="min-h-[96px] md:min-h-[90px] w-full resize-none rounded-xl border border-white/10 bg-obsidian-800 px-4 py-3 text-sm text-white placeholder:text-neutral-600 focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
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
          <p id="message-hint" className="sr-only">
            Pressione Ctrl+Enter ou Cmd+Enter para enviar, ou use o botão de microfone para gravar áudio
          </p>
        </div>
        <div className="flex w-full items-center justify-between gap-2 md:w-auto md:flex-col md:items-end md:gap-3">
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              accept=".pdf,.docx,.txt,.csv,image/png,image/jpeg"
              onChange={(event) => handleFilesSelected(event.target.files)}
            />
            <Button
              type="button"
              variant="outline"
              className="h-12 rounded-xl px-3 text-xs uppercase tracking-wide"
              onClick={() => fileInputRef.current?.click()}
              disabled={isSending || isLoading || uploading}
            >
              {uploading ? "Enviando..." : "Anexar"}
            </Button>
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
          <Button
            type={isSending ? "button" : "submit"}
            disabled={
              isLoading ||
              uploading ||
              (!isSending && !draft.trim() && attachments.length === 0)
            }
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
              "h-12 w-auto md:h-[80px] rounded-xl px-4 md:px-6 text-xs md:text-sm font-semibold uppercase tracking-wide focus:outline-none focus:ring-2",
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
