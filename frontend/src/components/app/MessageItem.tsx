"use client";

import { memo, useState } from "react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { MessageActions } from "./MessageActions";
import { ITILBadge, parseITILFromResponse } from "./ITILBadge";
import { ActionPlan, parseActionPlanFromResponse } from "./ActionPlan";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { ArtifactCard } from "./ArtifactCard";
import { GenesisMessage } from "@/state/useGenesisUI";
import type { Artifact } from "@/state/artifact-types";
import { markdownToHtml } from "@/lib/markdown-to-html";

/**
 * Normaliza espaçamento em relatórios markdown: preserva \\n/\\t e colapsa
 * quebras "  \n" (GFM <br>) entre palavras para evitar uma palavra por linha.
 */
function normalizeReportSpacing(content: string): string {
  let out = content.replace(/\\n/g, "\n").replace(/\\t/g, "\t");
  out = out.replace(/  \n/g, " ");
  return out;
}

interface MessageItemProps {
  message: GenesisMessage;
  isEditing: boolean;
  editingContent: string;
  editingAttachments?: GenesisMessage["attachments"];
  enableVSA: boolean;
  onEdit: () => void;
  onResend: () => void;
  onEditChange: (content: string) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onEditSaveAndResend: () => Promise<void>;
  onEditAttachmentsChange?: (attachments: NonNullable<GenesisMessage["attachments"]>) => void;
  onConfirmLinearProject?: () => void;
  isSending: boolean;
  /** Artifacts linked to this message (resolved from artifactIds). */
  artifacts?: Artifact[];
  /** Callback to open an artifact in the side panel. */
  onOpenArtifact?: (id: string) => void;
}

/**
 * Memoized message component to prevent unnecessary re-renders
 * when parent ChatPane re-renders (e.g., when user types in input)
 */
export const MessageItem = memo(function MessageItem({
  message,
  isEditing,
  editingContent,
  editingAttachments,
  enableVSA,
  onEdit,
  onResend,
  onEditChange,
  onEditSave,
  onEditCancel,
  onEditSaveAndResend,
  onEditAttachmentsChange,
  onConfirmLinearProject,
  isSending,
  artifacts,
  onOpenArtifact,
}: MessageItemProps) {
  const isAssistant = message.role === "assistant";
  const isThinking = message.content === "Pensando...";
  const isError = message.content.startsWith("Erro:");
  const isUserMessage = message.role === "user";
  const attachments = message.attachments || [];
  const activeEditingAttachments = editingAttachments || attachments;

  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const html = markdownToHtml(message.content);
    try {
      if (typeof ClipboardItem !== "undefined" && navigator.clipboard?.write) {
        const item = new ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([message.content], { type: "text/plain" }),
        });
        await navigator.clipboard.write([item]);
      } else {
        await navigator.clipboard?.writeText(message.content);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed", err);
    }
  };

  const isProjectPreview =
    isAssistant &&
    !isThinking &&
    !!message.content &&
    message.content.includes("## Preview do Projeto") &&
    message.content.includes("VSA_PROJECT_PREVIEW_CONFIRM");

  // Don't render empty assistant messages
  if (isAssistant && !isThinking && !message.content.trim() && !isError) {
    return null;
  }

  return (
    <article
      className={clsx(
        "group relative rounded-2xl border px-5 py-4 text-sm leading-relaxed transition-all animate-in fade-in slide-in-from-bottom-2 duration-300",
        isAssistant ? "w-full max-w-5xl" : "max-w-2xl ml-auto",
        isError
          ? "border-red-500/30 bg-red-900/20 text-red-300"
          : isAssistant
            ? "glass-panel border-white/[0.06] text-neutral-200"
            : "border-brand-primary/20 bg-brand-primary/10 text-white",
        isEditing && "ring-2 ring-brand-primary/30",
      )}
    >
      {isUserMessage && !isEditing && (
        <MessageActions
          message={message}
          onEdit={onEdit}
          onResend={onResend}
        />
      )}
      <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.35em] text-neutral-500">
        <span>
          {message.role === "assistant" ? "Agente" : "Você"}
          {message.editedAt && (
            <span className="ml-2 text-[9px] italic text-neutral-600">(editado)</span>
          )}
        </span>
        <span className="text-neutral-600">{new Date(message.timestamp).toLocaleTimeString()}</span>
      </div>
      {attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center gap-2 rounded-lg border border-white/10 bg-obsidian-800/60 px-3 py-2 text-xs text-neutral-300"
            >
              {att.mime.startsWith("image/") ? (
                <img src={att.url} alt={att.name} className="h-10 w-10 rounded object-cover" />
              ) : (
                <span className="h-10 w-10 rounded bg-white/10 flex items-center justify-center text-[10px] text-neutral-400">
                  DOC
                </span>
              )}
              <div className="flex flex-col">
                <span className="max-w-[180px] truncate">{att.name}</span>
                <span className="text-[10px] text-neutral-500">
                  {(att.size / 1024).toFixed(0)} KB
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      {isEditing ? (
        <div className="space-y-2">
          {activeEditingAttachments.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {activeEditingAttachments.map((att) => (
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
                  {onEditAttachmentsChange && (
                    <button
                      type="button"
                      className="ml-1 text-neutral-500 hover:text-white"
                      onClick={() =>
                        onEditAttachmentsChange(
                          activeEditingAttachments.filter((item) => item.id !== att.id)
                        )
                      }
                      aria-label="Remover anexo"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
          <textarea
            value={editingContent}
            onChange={(e) => onEditChange(e.target.value)}
            className="w-full resize-none rounded-lg border border-white/10 bg-obsidian-800 px-3 py-2 text-sm text-white focus:border-brand-primary focus:outline-none"
            rows={3}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                onEditCancel();
              } else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                if (editingContent.trim()) {
                  onEditSave();
                }
              }
            }}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onEditCancel}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onEditSave}
              disabled={!editingContent.trim()}
              className="bg-brand-primary/15 text-white hover:bg-brand-primary/25"
            >
              Salvar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onEditSaveAndResend}
              disabled={!editingContent.trim() || isSending}
              className="bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25"
            >
              Salvar e Reenviar
            </Button>
          </div>
        </div>
      ) : isAssistant ? (
        isThinking ? (
          <ThinkingIndicator autoProgress={true} vsaMode={enableVSA} />
        ) : (
          <div className="markdown-body">
            {/* ITIL Badge */}
            {(() => {
              const itilData = parseITILFromResponse(message.content);
              return itilData ? (
                <div className="mb-4">
                  <ITILBadge {...itilData} />
                </div>
              ) : null;
            })()}
            {/* Action Plan */}
            {(() => {
              const actionPlanData = parseActionPlanFromResponse(message.content);
              return actionPlanData ? (
                <div className="mb-4">
                  <ActionPlan {...actionPlanData} />
                </div>
              ) : null;
            })()}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[]}
              components={{
                p: ({ children }) => (
                  <p className="mb-4 last:mb-0 whitespace-normal text-neutral-200 leading-relaxed">{children}</p>
                ),
                br: () => <br />,
                a: ({ ...props }) => (
                  <a
                    {...props}
                    className="font-semibold text-brand-primary underline decoration-brand-primary/40 underline-offset-4 hover:text-brand-primary/80"
                    target="_blank"
                    rel="noreferrer"
                  />
                ),
                code: ({ node, className, children, ...props }) => {
                  const isInline = !className?.includes('language-');
                  return isInline ? (
                    <code
                      className={clsx(
                        "rounded bg-white/5 px-1.5 py-0.5 text-[13px] text-neutral-200",
                        className,
                      )}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <pre
                      className="overflow-x-auto rounded-lg border border-white/10 bg-obsidian-800 p-4 text-[13px] text-neutral-200"
                    >
                      <code className={className} {...props}>{children}</code>
                    </pre>
                  );
                },
                li: ({ ...props }) => <li className="pl-1" {...props} />,
                h1: ({ ...props }) => <h1 className="mb-4 text-2xl font-bold text-white" {...props} />,
                h2: ({ ...props }) => <h2 className="mb-3 mt-4 text-xl font-semibold text-white" {...props} />,
                h3: ({ ...props }) => <h3 className="mb-2 mt-3 text-lg font-semibold text-white" {...props} />,
                ul: ({ ...props }) => <ul className="mb-4 ml-6 list-disc space-y-1" {...props} />,
                ol: ({ ...props }) => <ol className="mb-4 ml-6 list-decimal space-y-1" {...props} />,
                blockquote: ({ ...props }) => <blockquote className="mb-4 border-l-4 border-brand-primary/30 pl-4 italic text-neutral-400" {...props} />,
                img: ({ src, alt, ...props }) => {
                  if (!src) return null;
                  return <img src={src} alt={alt || ""} className="max-w-full rounded-lg my-4" {...props} />;
                },
                table: ({ ...props }) => (
                  <div className="my-4 w-full min-w-0 overflow-x-auto rounded-lg border border-white/10">
                    <table className="min-w-full table-auto divide-y divide-white/10 text-sm" {...props} />
                  </div>
                ),
                thead: ({ ...props }) => <thead className="bg-white/5" {...props} />,
                tbody: ({ ...props }) => <tbody className="divide-y divide-white/[0.06]" {...props} />,
                tr: ({ ...props }) => <tr className="hover:bg-white/5 transition-colors" {...props} />,
                th: ({ ...props }) => (
                  <th
                    className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-400"
                    {...props}
                  />
                ),
                td: ({ ...props }) => (
                  <td className="min-w-0 max-w-[40rem] break-words px-4 py-3 text-sm text-neutral-300 align-top" {...props} />
                ),
              }}
            >
              {normalizeReportSpacing(message.content)}
            </ReactMarkdown>
            {isProjectPreview && onConfirmLinearProject && (
              <div className="mt-4 flex flex-wrap gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onConfirmLinearProject}
                  disabled={isSending}
                  className="bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25"
                >
                  Confirmar criação do projeto no Linear
                </Button>
              </div>
            )}
            {/* Artifact cards */}
            {artifacts && artifacts.length > 0 && onOpenArtifact && (
              <div className="mt-4 flex flex-wrap gap-2">
                {artifacts.map((art) => (
                  <ArtifactCard key={art.id} artifact={art} onOpen={onOpenArtifact} />
                ))}
              </div>
            )}
          </div>
        )
      ) : (
        <p className="whitespace-pre-wrap text-[15px] text-white">
          {message.content}
        </p>
      )}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-[10px] uppercase tracking-[0.35em] text-neutral-600">
        <div className="flex flex-wrap gap-3">
          {message.modelId ? <span>Modelo: {message.modelId}</span> : null}
          {message.usedTavily ? <span>Busca Web Ativada</span> : null}
        </div>
        {isAssistant && !isThinking && !isError && (
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-neutral-500 transition-colors hover:bg-white/10 hover:text-neutral-300"
            aria-label="Copiar resposta"
            title="Copiar resposta"
          >
            {copied ? (
              <>
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5  13l4 4L19 7" />
                </svg>
                <span>Copiado</span>
              </>
            ) : (
              <>
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copiar</span>
              </>
            )}
          </button>
        )}
      </div>
    </article>
  );
});
