"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import type { Artifact } from "@/state/artifact-types";

interface ArtifactPanelProps {
  artifact: Artifact | null;
  open: boolean;
  onClose: () => void;
  /** All artifacts in this session, for navigating between them. */
  sessionArtifacts: Artifact[];
  onSelectArtifact: (id: string) => void;
}

type ExportFormat = "md" | "pdf" | "docx";

export function ArtifactPanel({
  artifact,
  open,
  onClose,
  sessionArtifacts,
  onSelectArtifact,
}: ArtifactPanelProps) {
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const [tab, setTab] = useState<"content" | "history">("content");

  // Keyboard shortcut: Escape to close
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  const handleExport = useCallback(
    async (format: ExportFormat) => {
      if (!artifact) return;
      setExporting(format);

      try {
        if (format === "md") {
          // Direct download as markdown
          const blob = new Blob([artifact.content], { type: "text/markdown" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${artifact.title.replace(/[^a-zA-Z0-9_-]/g, "_")}.md`;
          a.click();
          URL.revokeObjectURL(url);
        } else {
          // Call backend export endpoint
          const res = await fetch("/api/v1/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: artifact.content,
              title: artifact.title,
              format,
            }),
          });

          if (!res.ok) {
            const errText = await res.text();
            throw new Error(errText || `Export failed: ${res.status}`);
          }

          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const ext = format === "pdf" ? "pdf" : "docx";
          const a = document.createElement("a");
          a.href = url;
          a.download = `${artifact.title.replace(/[^a-zA-Z0-9_-]/g, "_")}.${ext}`;
          a.click();
          URL.revokeObjectURL(url);
        }
      } catch (err) {
        console.error("Export error:", err);
      } finally {
        setExporting(null);
      }
    },
    [artifact],
  );

  const handleCopy = useCallback(async () => {
    if (!artifact) return;
    try {
      await navigator.clipboard.writeText(artifact.content);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  }, [artifact]);

  // History = other artifacts in the session
  const otherArtifacts = useMemo(
    () => sessionArtifacts.filter((a) => a.id !== artifact?.id),
    [sessionArtifacts, artifact?.id],
  );

  if (!open) return null;

  return (
    <>
      {/* Mobile overlay backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        onClick={onClose}
      />

      {/* Panel */}
      <aside
        className={clsx(
          "flex flex-col border-l border-white/[0.06] bg-obsidian-900 z-50",
          // Desktop: side panel, Mobile: fullscreen overlay
          "fixed inset-y-0 right-0 w-full sm:w-[480px] lg:static lg:w-[50%] lg:max-w-3xl lg:min-w-[400px]",
          "animate-in slide-in-from-right duration-200",
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3 shrink-0">
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-base font-semibold text-white">
              {artifact?.title || "Artefato"}
            </h2>
            {artifact && (
              <span className="text-[10px] uppercase tracking-wider text-neutral-500">
                {artifact.source === "rule-based" ? "Gerado por código" : "Extraído da IA"}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-3 rounded-lg border border-white/10 p-1.5 text-neutral-500 hover:border-white/20 hover:text-neutral-300 transition-colors"
            aria-label="Fechar painel"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-white/[0.06] px-5 shrink-0">
          <button
            onClick={() => setTab("content")}
            className={clsx(
              "px-3 py-2 text-xs font-medium uppercase tracking-wider border-b-2 transition-colors",
              tab === "content"
                ? "border-brand-primary text-white"
                : "border-transparent text-neutral-500 hover:text-neutral-300",
            )}
          >
            Conteúdo
          </button>
          <button
            onClick={() => setTab("history")}
            className={clsx(
              "px-3 py-2 text-xs font-medium uppercase tracking-wider border-b-2 transition-colors",
              tab === "history"
                ? "border-brand-primary text-white"
                : "border-transparent text-neutral-500 hover:text-neutral-300",
            )}
          >
            Histórico ({otherArtifacts.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 min-h-0">
          {tab === "content" && artifact ? (
            <div className="markdown-body">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => (
                    <p className="mb-4 last:mb-0 whitespace-normal text-neutral-200 leading-relaxed">{children}</p>
                  ),
                  a: ({ ...props }) => (
                    <a
                      {...props}
                      className="font-semibold text-brand-primary underline decoration-brand-primary/40 underline-offset-4 hover:text-brand-primary/80"
                      target="_blank"
                      rel="noreferrer"
                    />
                  ),
                  code: ({ node, className, children, ...props }) => {
                    const isInline = !className?.includes("language-");
                    return isInline ? (
                      <code className="rounded bg-white/5 px-1.5 py-0.5 text-[13px] text-neutral-200" {...props}>
                        {children}
                      </code>
                    ) : (
                      <pre className="overflow-x-auto rounded-lg border border-white/10 bg-obsidian-800 p-4 text-[13px] text-neutral-200">
                        <code className={className} {...props}>{children}</code>
                      </pre>
                    );
                  },
                  h1: ({ ...props }) => <h1 className="mb-4 text-2xl font-bold text-white" {...props} />,
                  h2: ({ ...props }) => <h2 className="mb-3 mt-4 text-xl font-semibold text-white" {...props} />,
                  h3: ({ ...props }) => <h3 className="mb-2 mt-3 text-lg font-semibold text-white" {...props} />,
                  ul: ({ ...props }) => <ul className="mb-4 ml-6 list-disc space-y-1" {...props} />,
                  ol: ({ ...props }) => <ol className="mb-4 ml-6 list-decimal space-y-1" {...props} />,
                  table: ({ ...props }) => (
                    <div className="my-4 w-full min-w-0 overflow-x-auto rounded-lg border border-white/10">
                      <table className="min-w-full table-auto divide-y divide-white/10 text-sm" {...props} />
                    </div>
                  ),
                  thead: ({ ...props }) => <thead className="bg-white/5" {...props} />,
                  tbody: ({ ...props }) => <tbody className="divide-y divide-white/[0.06]" {...props} />,
                  tr: ({ ...props }) => <tr className="hover:bg-white/5 transition-colors" {...props} />,
                  th: ({ ...props }) => (
                    <th className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-400" {...props} />
                  ),
                  td: ({ ...props }) => (
                    <td className="min-w-0 max-w-[40rem] break-words px-4 py-3 text-sm text-neutral-300 align-top" {...props} />
                  ),
                }}
              >
                {artifact.content}
              </ReactMarkdown>
            </div>
          ) : tab === "history" ? (
            <div className="space-y-2">
              {otherArtifacts.length === 0 ? (
                <p className="text-sm text-neutral-500">Nenhum outro artefato nesta sessão.</p>
              ) : (
                otherArtifacts.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => {
                      onSelectArtifact(a.id);
                      setTab("content");
                    }}
                    className="w-full rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-left hover:border-brand-primary/30 hover:bg-white/5 transition-colors"
                  >
                    <p className="text-sm font-medium text-white">{a.title}</p>
                    <p className="text-xs text-neutral-500">
                      {new Date(a.createdAt).toLocaleTimeString()}
                    </p>
                  </button>
                ))
              )}
            </div>
          ) : (
            <p className="text-sm text-neutral-500">Nenhum artefato selecionado.</p>
          )}
        </div>

        {/* Footer: Export buttons */}
        {artifact && tab === "content" && (
          <div className="flex items-center gap-2 border-t border-white/[0.06] px-5 py-3 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
            >
              Copiar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("md")}
              disabled={exporting !== null}
            >
              {exporting === "md" ? "..." : "MD"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("pdf")}
              disabled={exporting !== null}
            >
              {exporting === "pdf" ? "..." : "PDF"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("docx")}
              disabled={exporting !== null}
            >
              {exporting === "docx" ? "..." : "DOCX"}
            </Button>
          </div>
        )}
      </aside>
    </>
  );
}
