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
import { GenesisMessage } from "@/state/useGenesisUI";

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
  isSending: boolean;
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
  isSending
}: MessageItemProps) {
  const isAssistant = message.role === "assistant";
  const isThinking = message.content === "Pensando...";
  const isError = message.content.startsWith("Erro:");
  const isUserMessage = message.role === "user";

  // Don't render empty assistant messages
  if (isAssistant && !isThinking && !message.content.trim() && !isError) {
    return null;
  }

  return (
    <article
      className={clsx(
        "group relative rounded-2xl border px-5 py-4 text-sm leading-relaxed shadow-lg transition-all animate-in fade-in slide-in-from-bottom-2 duration-300",
        isAssistant ? "w-full max-w-5xl" : "max-w-2xl ml-auto",
        isError
          ? "border-red-500/40 bg-red-500/10 text-red-100"
          : isAssistant
            ? "border-white/10 bg-white/10 text-slate-100"
            : "border-vsa-orange/40 bg-vsa-orange/10 text-vsa-orange-light",
        isEditing && "ring-2 ring-vsa-blue/50",
      )}
    >
      {isUserMessage && !isEditing && (
        <MessageActions
          message={message}
          onEdit={onEdit}
          onResend={onResend}
        />
      )}
      <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.35em] text-slate-400">
        <span>
          {message.role === "assistant" ? "Agente" : "Você"}
          {message.editedAt && (
            <span className="ml-2 text-[9px] italic text-slate-500">(editado)</span>
          )}
        </span>
        <span className="text-slate-500">{new Date(message.timestamp).toLocaleTimeString()}</span>
      </div>
      {isEditing ? (
        <div className="space-y-2">
          <textarea
            value={editingContent}
            onChange={(e) => onEditChange(e.target.value)}
            className="w-full resize-none rounded-lg border border-vsa-blue/40 bg-[#0b1526]/90 px-3 py-2 text-sm text-white focus:border-vsa-blue focus:outline-none"
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
              className="border-slate-400/40 text-slate-300"
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onEditSave}
              disabled={!editingContent.trim()}
              className="bg-vsa-orange/20 text-vsa-orange-light hover:bg-vsa-orange/30"
            >
              Salvar
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onEditSaveAndResend}
              disabled={!editingContent.trim() || isSending}
              className="bg-emerald-500/20 text-emerald-100 hover:bg-emerald-500/30"
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
                p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
                br: () => <br />,
                a: ({ ...props }) => (
                  <a
                    {...props}
                    className="font-semibold text-vsa-blue-light underline decoration-vsa-blue/60 underline-offset-4 hover:text-vsa-blue-lighter"
                    target="_blank"
                    rel="noreferrer"
                  />
                ),
                code: ({ node, className, children, ...props }) => {
                  const isInline = !className?.includes('language-');
                  return isInline ? (
                    <code
                      className={clsx(
                        "rounded bg-white/10 px-1.5 py-0.5 text-[13px] text-slate-100",
                        className,
                      )}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <pre
                      className="overflow-x-auto rounded-lg border border-white/10 bg-[#0b1526] p-4 text-[13px] text-slate-100"
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
                blockquote: ({ ...props }) => <blockquote className="mb-4 border-l-4 border-vsa-orange/40 pl-4 italic" {...props} />,
                img: ({ src, alt, ...props }) => {
                  if (!src) return null;
                  return <img src={src} alt={alt || ""} className="max-w-full rounded-lg my-4" {...props} />;
                },
                table: ({ ...props }) => (
                  <div className="my-4 w-full min-w-0 overflow-x-auto rounded-lg border border-white/10">
                    <table className="min-w-full table-fixed divide-y divide-white/10 text-sm" {...props} />
                  </div>
                ),
                thead: ({ ...props }) => <thead className="bg-white/5" {...props} />,
                tbody: ({ ...props }) => <tbody className="divide-y divide-white/5 bg-white/[0.02]" {...props} />,
                tr: ({ ...props }) => <tr className="hover:bg-white/5 transition-colors" {...props} />,
                th: ({ ...props }) => (
                  <th
                    className="break-words px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-300"
                    {...props}
                  />
                ),
                td: ({ ...props }) => (
                  <td className="max-w-0 break-words px-4 py-3 text-sm text-slate-200" {...props} />
                ),
              }}
            >
              {message.content.replace(/\\n/g, '\n').replace(/\\t/g, '\t')}
            </ReactMarkdown>
          </div>
        )
      ) : (
        <p className="whitespace-pre-wrap text-[15px] text-slate-100" style={{ fontFamily: "var(--font-sans)" }}>
          {message.content}
        </p>
      )}
      <div className="mt-3 flex flex-wrap gap-3 text-[10px] uppercase tracking-[0.35em] text-slate-400">
        {message.modelId ? <span>Modelo: {message.modelId}</span> : null}
        {message.usedTavily ? <span>Busca Web Ativada</span> : null}
      </div>
    </article>
  );
});
