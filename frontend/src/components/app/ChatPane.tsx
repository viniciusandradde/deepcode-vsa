"use client";

import { useMemo, useState, useEffect, useCallback } from "react";
import clsx from "clsx";
import { Virtuoso } from "react-virtuoso";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Logo } from "./Logo";
import { MessageInput } from "./MessageInput";
import { MessageItem } from "./MessageItem";
import { SuggestionChips } from "./SuggestionChips";
import { ArtifactPanel } from "./ArtifactPanel";
import type { Artifact } from "@/state/artifact-types";
import { SkeletonMessage } from "@/components/ui/skeleton";

interface ChatPaneProps {
  sidebarCollapsed?: boolean;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function ChatPane({ sidebarCollapsed = false, sidebarOpen = false, onToggleSidebar }: ChatPaneProps) {
  const {
    isLoading,
    isSending,
    currentSessionId,
    messagesBySession,
    selectedModelId,
    useTavily,
    sendMessage,
    editingMessageId,
    setEditingMessageId,
    editMessage,
    resendMessage,
    cancelMessage,
    // VSA Integration states
    enableVSA,
    enableGLPI,
    enableZabbix,
    enableLinear,
    enablePlanning,
    // Artifacts
    artifactsBySession,
    selectedArtifactId,
    panelOpen,
    selectArtifact,
    closePanel,
    getSessionArtifacts,
  } = useGenesisUI();
  const messages = useMemo(() => messagesBySession[currentSessionId] ?? [], [messagesBySession, currentSessionId]);
  const sessionArtifacts = useMemo(() => getSessionArtifacts(currentSessionId), [getSessionArtifacts, currentSessionId, artifactsBySession]);

  // Build a map from artifact id -> Artifact for quick lookup
  const artifactMap = useMemo(() => {
    const map = new Map<string, Artifact>();
    for (const art of sessionArtifacts) map.set(art.id, art);
    return map;
  }, [sessionArtifacts]);

  // Resolve the selected artifact object
  const selectedArtifact = useMemo(
    () => (selectedArtifactId ? artifactMap.get(selectedArtifactId) ?? null : null),
    [selectedArtifactId, artifactMap],
  );

  const [editingContent, setEditingContent] = useState("");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    function updateViewport() {
      if (typeof window !== "undefined") {
        setIsMobile(window.innerWidth < 1024);
      }
    }
    updateViewport();
    window.addEventListener("resize", updateViewport);
    return () => window.removeEventListener("resize", updateViewport);
  }, []);

  const handleMessageSubmit = useCallback(async (message: string, streaming: boolean) => {
    await sendMessage(message, streaming);
  }, [sendMessage]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
        if (event.key === "Escape" && editingMessageId) {
          setEditingMessageId(null);
          setEditingContent("");
        }
        return;
      }

      if (event.key === "e" || event.key === "E") {
        if (!editingMessageId && messages.length > 0) {
          const lastUserMessage = [...messages].reverse().find((msg) => msg.role === "user");
          if (lastUserMessage) {
            setEditingMessageId(lastUserMessage.id);
            setEditingContent(lastUserMessage.content);
          }
        }
      } else if (event.key === "Escape") {
        if (editingMessageId) {
          setEditingMessageId(null);
          setEditingContent("");
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editingMessageId, messages, setEditingMessageId]);

  return (
    <div className="flex min-h-[100dvh] flex-1 min-w-0">
      {/* Main chat column */}
      <div className="flex flex-1 flex-col min-w-0">
      <header className="safe-area-top flex h-16 md:h-20 shrink-0 items-center justify-between border-b border-white/[0.06] px-4 md:px-10 text-white bg-obsidian-900/80 backdrop-blur-md">
        <div className="flex min-w-0 items-center gap-3 md:gap-4">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="p-2 rounded-lg border border-white/10 bg-white/5 text-neutral-400 hover:border-brand-primary/40 hover:bg-brand-primary/10 hover:text-white transition-colors"
              aria-label={isMobile ? (sidebarOpen ? "Fechar menu" : "Abrir menu") : (sidebarCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral")}
              title={isMobile ? (sidebarOpen ? "Fechar menu" : "Abrir menu") : (sidebarCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral")}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                {(isMobile ? !sidebarOpen : sidebarCollapsed) ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                )}
              </svg>
            </button>
          )}
          <div className="flex min-w-0 flex-col">
            <span className="hidden sm:block text-xs uppercase tracking-[0.35em] text-neutral-500">
              VSA Nexus
            </span>
            <span className="truncate text-sm font-semibold text-white">
              Chat Inteligente
            </span>
          </div>
          <div className="hidden md:block h-12 w-px bg-brand-primary/30" />
        </div>
        <div className="flex min-w-0 items-center gap-2 md:gap-4 text-[11px] uppercase tracking-wide">
          <div className="md:hidden min-w-0">
            <span className={clsx(
              "glass-panel rounded-md px-2 py-1 text-[10px] flex items-center gap-2 max-w-[160px]",
              enableVSA ? "text-neutral-300" : "text-neutral-500",
            )}>
              <span className={clsx(
                "h-2 w-2 rounded-full",
                enableVSA ? "bg-brand-primary animate-pulse" : "bg-neutral-600",
              )} />
              <span className="truncate">{enableVSA ? "VSA Ativo" : "VSA Inativo"}</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-4 text-[11px] uppercase tracking-wide">
            {enableVSA ? (
              <span className="glass-panel rounded-md px-3 py-1 text-neutral-300 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-brand-primary animate-pulse" />
                VSA Ativo
                {enableGLPI && <span className="text-neutral-400">GLPI</span>}
                {enableZabbix && <span className="text-neutral-400">Zabbix</span>}
                {enableLinear && <span className="text-neutral-400">Linear</span>}
                {enablePlanning && <span className="text-neutral-400">Planejamento</span>}
              </span>
            ) : (
              <span className="glass-panel rounded-md px-3 py-1 text-neutral-500 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-neutral-600" />
                VSA Inativo
              </span>
            )}
          </div>
          {sessionArtifacts.length > 0 && (
            <button
              onClick={() => {
                const last = sessionArtifacts[sessionArtifacts.length - 1];
                if (last) selectArtifact(last.id);
              }}
              className="glass-panel rounded-md px-2 md:px-3 py-1 text-neutral-300 flex items-center gap-2 hover:border-brand-primary/40 transition-colors"
              title="Ver artefatos"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{sessionArtifacts.length}</span>
            </button>
          )}
        </div>
      </header>

        <main className="vsa-main-background relative flex flex-1 flex-col min-h-0">
        {isLoading ? (
          <div className="space-y-4 px-6 md:px-10 py-6 md:py-8">
            <SkeletonMessage align="right" />
            <SkeletonMessage align="left" />
            <SkeletonMessage align="right" />
            <SkeletonMessage align="left" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-8 px-6 md:px-10 py-8">
            <div className="text-center px-4">
              <h2 className="text-2xl md:text-3xl font-semibold text-white">
                Como posso ajudar?
              </h2>
              <p className="mt-2 text-neutral-400 font-medium">
                Escolha uma opção ou digite sua pergunta
              </p>
            </div>
            <SuggestionChips
              onSelect={(cmd) => handleMessageSubmit(cmd, true)}
              disabled={isSending || isLoading}
            />
          </div>
        ) : (
          <Virtuoso
            key={currentSessionId}
            style={{ flex: 1 }}
            data={messages}
            followOutput="smooth"
            initialTopMostItemIndex={messages.length - 1}
            computeItemKey={(_, msg) => msg.id}
            itemContent={(_, message) => {
              const msgArtifacts = message.artifactIds
                ?.map((aid) => artifactMap.get(aid))
                .filter((a): a is Artifact => !!a);

              return (
                <div className="px-6 md:px-10 py-2">
                  <MessageItem
                    message={message}
                    isEditing={editingMessageId === message.id}
                    editingContent={editingContent}
                    enableVSA={enableVSA}
                    onEdit={() => {
                      setEditingMessageId(message.id);
                      setEditingContent(message.content);
                    }}
                    onResend={() => resendMessage(message.id)}
                    onEditChange={setEditingContent}
                    onEditSave={() => {
                      if (editingContent.trim()) {
                        editMessage(message.id, editingContent.trim());
                        setEditingMessageId(null);
                        setEditingContent("");
                      }
                    }}
                    onEditCancel={() => {
                      setEditingMessageId(null);
                      setEditingContent("");
                    }}
                    onEditSaveAndResend={async () => {
                      if (editingContent.trim()) {
                        editMessage(message.id, editingContent.trim());
                        setEditingMessageId(null);
                        setEditingContent("");
                        await resendMessage(message.id);
                      }
                    }}
                    onConfirmLinearProject={
                      enableLinear
                        ? () => handleMessageSubmit("Confirmar criação do projeto no Linear.", true)
                        : undefined
                    }
                    isSending={isSending}
                    artifacts={msgArtifacts}
                    onOpenArtifact={selectArtifact}
                  />
                </div>
              );
            }}
          />
        )}
      </main>

      <MessageInput
        onSubmit={handleMessageSubmit}
        isLoading={isLoading}
        isSending={isSending}
        onCancel={cancelMessage}
        currentSessionId={currentSessionId}
      />
      </div>

      {/* Artifact side panel */}
      <ArtifactPanel
        artifact={selectedArtifact}
        open={panelOpen}
        onClose={closePanel}
        sessionArtifacts={sessionArtifacts}
        onSelectArtifact={selectArtifact}
      />
    </div>
  );
}
