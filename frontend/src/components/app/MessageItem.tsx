"use client";

import { memo } from "react";
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

/**
 * Normaliza espaçamento em relatórios markdown: preserva \\n/\\t e colapsa
 * quebras "  \n" (GFM <br>) entre palavras para evitar uma palavra por linha.
 */
function normalizeReportSpacing(content: string): string {
  let out = content.replace(/\\n/g, "\n").replace(/\\t/g, "\t");
  // Colapsa "  \n" (markdown <br>) para espaço, evitando "Detalhes:\nProjeto\nde\n..." por linha
  out = out.replace(/  \n/g, " ");
  return out;
}

interface MessageItemProps {
  message: GenesisMessage;
  isEditing: boolean;
  editingContent: string;
  enableVSA: boolean;
  onEdit: () => void;
  onResend: () => void;
  onEditChange: (content: string) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onEditSaveAndResend: () => Promise<void>;
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
  enableVSA,
  onEdit,
  onResend,
  onEditChange,
  onEditSave,
  onEditCancel,
  onEditSaveAndResend,
  onConfirmLinearProject,
  isSending,
  artifacts,
  onOpenArtifact,
}: MessageItemProps) {
  const isAssistant = message.role === "assistant";
  const isThinking = message.content === "Pensando...";
  const isError = message.content.startsWith("Erro:");
  const isUserMessage = message.role === "user";

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
        "group relative rounded-2xl border-2 px-5 py-4 text-sm leading-relaxed shadow-sm transition-all animate-in fade-in slide-in-from-bottom-2 duration-300",
        isAssistant ? "w-full max-w-5xl" : "max-w-2xl ml-auto",
        isError
          ? "border-red-300 bg-red-50 text-slate-900"
          : isAssistant
            ? "border-slate-400 bg-white text-slate-900"
            : "border-vsa-orange/40 bg-vsa-orange/10 text-slate-900",
        isEditing && "ring-2 ring-vsa-orange/40",
      )}
    >
      {isUserMessage && !isEditing && (
        <MessageActions
          message={message}
          onEdit={onEdit}
          onResend={onResend}
        />
      )}
      <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.35em] text-slate-500">
        <span>
          {message.role === "assistant" ? "Agente" : "Você"}
          {message.editedAt && (
            <span className="ml-2 text-[9px] italic text-slate-400">(editado)</span>
          )}
        </span>
        <span className="text-slate-400">{new Date(message.timestamp).toLocaleTimeString()}</span>
      </div>
      {isEditing ? (
        <div className="space-y-2">
            <textarea
              value={editingContent}
              onChange={(e) => onEditChange(e.target.value)}
            className="w-full resize-none rounded-lg border-2 border-slate-400 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-vsa-orange focus:outline-none"
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
              className="border-slate-400 text-slate-700"
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onEditSave}
              disabled={!editingContent.trim()}
              className="bg-vsa-orange/15 text-slate-900 hover:bg-vsa-orange/25"
            >
              Salvar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onEditSaveAndResend}
              disabled={!editingContent.trim() || isSending}
              className="bg-emerald-100 text-slate-900 hover:bg-emerald-200"
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
                  <p className="mb-4 last:mb-0 whitespace-normal text-slate-800 leading-relaxed">{children}</p>
                ),
                br: () => <br />,
                a: ({ ...props }) => (
                  <a
                    {...props}
                    className="font-semibold text-slate-900 underline decoration-vsa-orange/40 underline-offset-4 hover:text-slate-900"
                    target="_blank"
                    rel="noreferrer"
                  />
                ),
                code: ({ node, className, children, ...props }) => {
                  const isInline = !className?.includes('language-');
                  return isInline ? (
                    <code
                      className={clsx(
                        "rounded bg-slate-100 px-1.5 py-0.5 text-[13px] text-slate-800",
                        className,
                      )}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <pre
                      className="overflow-x-auto rounded-lg border-2 border-slate-400 bg-slate-50 p-4 text-[13px] text-slate-800 shadow-sm"
                    >
                      <code className={className} {...props}>{children}</code>
                    </pre>
                  );
                },
                li: ({ ...props }) => <li className="pl-1" {...props} />,
                h1: ({ ...props }) => <h1 className="mb-4 text-2xl font-bold" {...props} />,
                h2: ({ ...props }) => <h2 className="mb-3 mt-4 text-xl font-semibold" {...props} />,
                h3: ({ ...props }) => <h3 className="mb-2 mt-3 text-lg font-semibold" {...props} />,
                ul: ({ ...props }) => <ul className="mb-4 ml-6 list-disc space-y-1" {...props} />,
                ol: ({ ...props }) => <ol className="mb-4 ml-6 list-decimal space-y-1" {...props} />,
                blockquote: ({ ...props }) => <blockquote className="mb-4 border-l-4 border-vsa-orange/40 pl-4 italic text-slate-700" {...props} />,
                img: ({ src, alt, ...props }) => {
                  if (!src) return null;
                  return <img src={src} alt={alt || ""} className="max-w-full rounded-lg my-4" {...props} />;
                },
                table: ({ ...props }) => (
                  <div className="my-4 w-full min-w-0 overflow-x-auto rounded-lg border-2 border-slate-400 shadow-sm">
                    <table className="min-w-full table-auto divide-y divide-slate-200 text-sm" {...props} />
                  </div>
                ),
                thead: ({ ...props }) => <thead className="bg-slate-50" {...props} />,
                tbody: ({ ...props }) => <tbody className="divide-y divide-slate-200 bg-white" {...props} />,
                tr: ({ ...props }) => <tr className="hover:bg-slate-50 transition-colors" {...props} />,
                th: ({ ...props }) => (
                  <th
                    className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
                    {...props}
                  />
                ),
                td: ({ ...props }) => (
                  <td className="min-w-0 max-w-[40rem] break-words px-4 py-3 text-sm text-slate-700 align-top" {...props} />
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
                  className="bg-emerald-100 text-slate-900 hover:bg-emerald-200"
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
        <p className="whitespace-pre-wrap text-[15px] text-slate-900" style={{ fontFamily: "var(--font-sans)" }}>
          {message.content}
        </p>
      )}
      <div className="mt-3 flex flex-wrap gap-3 text-[10px] uppercase tracking-[0.35em] text-slate-500">
        {message.modelId ? <span>Modelo: {message.modelId}</span> : null}
        {message.usedTavily ? <span>Busca Web Ativada</span> : null}
      </div>
    </article>
  );
});
