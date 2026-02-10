"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import clsx from "clsx";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";
import { SettingsPanel } from "./SettingsPanel";
import { DeleteConfirmDialog } from "./DeleteConfirmDialog";
import { SkeletonSessionCard } from "@/components/ui/skeleton";

interface SidebarProps {
  collapsed?: boolean;
  open?: boolean;
  onClose?: () => void;
}

export function Sidebar({ collapsed = false, open = false, onClose }: SidebarProps) {
  const {
    isLoading,
    models,
    selectedModelId,
    setSelectedModelId,
    useTavily,
    setUseTavily,
    sessions,
    currentSessionId,
    selectSession,
    createSession,
    deleteSession,
    renameSession,
    messagesBySession,
  } = useGenesisUI();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>("");

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setDeleteDialogOpen(true);
  };

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
        return;
      }

      const isMeta = event.metaKey || event.ctrlKey;

      if (event.key === "Delete" && currentSessionId) {
        setSessionToDelete(currentSessionId);
        setDeleteDialogOpen(true);
        return;
      }

      if (isMeta && event.key.toLowerCase() === "n") {
        event.preventDefault();
        createSession().catch(console.error);
        return;
      }

      if (!sessions.length) return;
      const currentIndex = sessions.findIndex((s) => s.id === currentSessionId);

      if (isMeta && event.key === "]") {
        event.preventDefault();
        const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % sessions.length : 0;
        const nextSession = sessions[nextIndex];
        if (nextSession) {
          selectSession(nextSession.id).catch(console.error);
        }
        return;
      }

      if (isMeta && event.key === "[") {
        event.preventDefault();
        const prevIndex =
          currentIndex > 0 ? currentIndex - 1 : sessions.length - 1;
        const prevSession = sessions[prevIndex];
        if (prevSession) {
          selectSession(prevSession.id).catch(console.error);
        }
        return;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSessionId, sessions, createSession, selectSession]);

  const handleDeleteConfirm = async () => {
    if (sessionToDelete) {
      await deleteSession(sessionToDelete);
      setSessionToDelete(null);
    }
  };

  const handleCreateSession = async () => {
    await createSession();
    onClose?.();
  };

  const handleSelectSession = async (sessionId: string) => {
    await selectSession(sessionId);
    onClose?.();
  };

  const sessionToDeleteTitle = sessionToDelete
    ? sessions.find((s) => s.id === sessionToDelete)?.title
    : undefined;

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}
      <aside className={clsx(
        "fixed inset-y-0 left-0 z-50 flex h-[100dvh] flex-col border-r border-white/[0.06] bg-obsidian-900 text-white",
        "w-[85vw] max-w-[320px] p-6 gap-6 transition-transform duration-300",
        "lg:static lg:h-screen lg:translate-x-0",
        collapsed ? "lg:w-20 lg:p-4" : "lg:w-80 lg:p-7 lg:gap-8",
        open ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
      )}>
        {!collapsed ? (
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[11px] uppercase tracking-[0.4em] text-neutral-500">AI Agent</div>
              <div
                className="text-2xl font-black uppercase text-white"
              >
                VSA Nexus AI
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center mb-4">
            <div className="text-2xl font-black uppercase text-white">
              V
            </div>
          </div>
        )}

        {!collapsed ? (
          <>
            <section className="space-y-3">
              <header className="text-xs uppercase tracking-[0.35em] text-neutral-500">Navegação</header>
              <div className="space-y-2">
                <Link
                  href="/"
                  onClick={onClose}
                  className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-neutral-200 hover:border-brand-primary/30 hover:bg-white/5 transition-colors"
                >
                  Chat
                  <span className="text-[10px] uppercase text-neutral-500">Principal</span>
                </Link>
                <Link
                  href="/planning"
                  onClick={onClose}
                  className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-neutral-200 hover:border-brand-primary/30 hover:bg-white/5 transition-colors"
                >
                  Projetos
                  <span className="text-[10px] uppercase text-neutral-500">Planejamento</span>
                </Link>
                <Link
                  href="/automation/scheduler"
                  onClick={onClose}
                  className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-obsidian-800 px-3 py-2 text-sm text-neutral-200 hover:border-brand-primary/30 hover:bg-white/5 transition-colors"
                >
                  Agendamento
                  <span className="text-[10px] uppercase text-neutral-500">Automacao</span>
                </Link>
              </div>
            </section>
            <section className="space-y-3">
              <header className="text-xs uppercase tracking-[0.35em] text-neutral-500">Seleção de Modelo</header>
              {isLoading ? (
                <div className="rounded-lg border border-white/[0.06] bg-white/5 p-3 text-sm text-neutral-500">
                  Carregando modelos...
                </div>
              ) : models.length === 0 ? (
                <div className="rounded-lg border border-white/[0.06] bg-white/5 p-3 text-sm text-neutral-500">
                  Nenhum modelo disponível
                </div>
              ) : (
                <Select
                  value={selectedModelId}
                  onChange={setSelectedModelId}
                  options={models.map((model) => ({
                    value: model.id,
                    label: `${model.label}${model.isDefault ? " ⭐" : ""}`,
                    description: `custo in/out $${model.inputCost.toFixed(2)} / $${model.outputCost.toFixed(2)}`,
                  }))}
                  placeholder="Selecione um modelo..."
                  className="w-full"
                />
              )}
            </section>

            <section className="space-y-3">
              <header className="text-xs uppercase tracking-[0.35em] text-neutral-500">Ferramentas</header>
              <Switch
                checked={useTavily}
                label={useTavily ? "Busca Web habilitada" : "Busca Web desabilitada"}
                onClick={() => setUseTavily(!useTavily)}
              />
            </section>

            <SettingsPanel />
          </>
        ) : (
          <div className="flex flex-col gap-4 items-center">
            <button
              onClick={() => setSelectedModelId(selectedModelId || models[0]?.id)}
              className={clsx(
                "w-12 h-12 rounded-lg border flex items-center justify-center transition-colors",
                selectedModelId
                  ? "border-brand-primary/40 bg-brand-primary/10 text-white"
                  : "border-white/[0.06] bg-white/5 text-neutral-500"
              )}
              title={models.find(m => m.id === selectedModelId)?.label || "Modelo"}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </button>
            <button
              onClick={() => setUseTavily(!useTavily)}
              className={clsx(
                "w-12 h-12 rounded-lg border flex items-center justify-center transition-colors",
                useTavily
                  ? "border-brand-primary/40 bg-brand-primary/10 text-white"
                  : "border-white/[0.06] bg-white/5 text-neutral-500"
              )}
              title={useTavily ? "Busca Web habilitada" : "Busca Web desabilitada"}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </div>
        )}

        <section className="flex-1 space-y-3 overflow-hidden">
          {!collapsed && (
            <header className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-neutral-500">
              Sessões Ativas
              <Button
                onClick={() => handleCreateSession().catch(console.error)}
                size="sm"
                variant="primary"
                disabled={isLoading}
              >
                Nova Sessão
              </Button>
            </header>
          )}
          {collapsed && (
            <button
              onClick={() => handleCreateSession().catch(console.error)}
              disabled={isLoading}
              className="w-12 h-12 rounded-lg border border-brand-primary/40 bg-brand-primary text-white hover:bg-brand-primary/80 hover:shadow-glow-orange flex items-center justify-center transition-colors disabled:opacity-50"
              title="Nova Sessão"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          )}
          <div className={clsx(
            "flex h-full flex-col gap-2 overflow-y-auto",
            collapsed ? "" : "-mr-3 pr-3"
          )}>
            {isLoading ? (
              <div className="space-y-2">
                <SkeletonSessionCard />
                <SkeletonSessionCard />
                <SkeletonSessionCard />
              </div>
            ) : sessions.length === 0 ? (
              <div className="space-y-2 rounded-md border border-white/[0.06] bg-white/5 p-3 text-xs text-neutral-500">
                Nenhuma sessão. Clique em "Nova Sessão" para começar.
              </div>
            ) : (
              [...sessions]
                .sort((a, b) => {
                  const aTs = a.lastActivityAt ?? a.createdAt;
                  const bTs = b.lastActivityAt ?? b.createdAt;
                  return bTs - aTs;
                })
                .map((session) => {
                  const active = session.id === currentSessionId;
                  const messages = messagesBySession[session.id] || [];
                  const messageCount = messages.length;
                  const lastMessage = messages[messages.length - 1];
                  const lastMessagePreview = lastMessage
                    ? lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? "..." : "")
                    : "Nenhuma mensagem";

                  return (
                    collapsed ? (
                      <button
                        key={session.id}
                        onClick={() => handleSelectSession(session.id).catch(console.error)}
                        className={clsx(
                          "w-12 h-12 rounded-lg border flex items-center justify-center transition-all relative",
                          active
                            ? "border-brand-primary/40 bg-brand-primary/10 text-white shadow-glow-orange"
                            : "border-white/[0.06] bg-obsidian-800 text-neutral-300 hover:border-brand-primary/30 hover:bg-white/5",
                        )}
                        title={`${session.title} (${messageCount} mensagens)`}
                        aria-label={`Sessão ${session.title}, ${messageCount} mensagens`}
                      >
                        <span className="text-xs font-bold">{session.title.charAt(0).toUpperCase()}</span>
                        {messageCount > 0 && (
                          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-brand-primary/20 text-[8px] flex items-center justify-center text-white border border-brand-primary/40">
                            {messageCount > 9 ? "9+" : messageCount}
                          </span>
                        )}
                      </button>
                    ) : (
                      <div
                        key={session.id}
                        className={clsx(
                          "group relative flex items-center gap-2 rounded-xl border px-3 py-2 transition-all animate-in fade-in slide-in-from-left-2 duration-200",
                          active
                            ? "border-brand-primary/40 bg-brand-primary/10 text-white shadow-glow-orange"
                            : "border-white/[0.06] bg-obsidian-800 text-neutral-300 hover:border-brand-primary/30 hover:bg-white/5",
                        )}
                      >
                        <button
                          onClick={() => handleSelectSession(session.id).catch(console.error)}
                          className="flex flex-1 flex-col gap-1 text-left"
                          aria-label={`Sessão ${session.title}, ${messageCount} mensagens`}
                        >
                          <div className="flex items-center justify-between">
                            {editingSessionId === session.id ? (
                              <input
                                autoFocus
                                value={editingTitle}
                                onChange={(e) => setEditingTitle(e.target.value)}
                                onBlur={() => {
                                  if (editingTitle.trim()) {
                                    renameSession(session.id, editingTitle.trim());
                                  }
                                  setEditingSessionId(null);
                                }}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") {
                                    if (editingTitle.trim()) {
                                      renameSession(session.id, editingTitle.trim());
                                    }
                                    setEditingSessionId(null);
                                  } else if (e.key === "Escape") {
                                    setEditingSessionId(null);
                                  }
                                }}
                                className="w-full rounded bg-obsidian-800 px-1 py-0.5 text-sm font-semibold text-white outline-none border border-white/10 focus:border-brand-primary"
                              />
                            ) : (
                              <span
                                className="text-sm font-semibold uppercase tracking-wide text-white"
                                onDoubleClick={() => {
                                  setEditingSessionId(session.id);
                                  setEditingTitle(session.title);
                                }}
                              >
                                {session.title}
                              </span>
                            )}
                            {messageCount > 0 && (
                              <span className="ml-2 rounded-full bg-brand-primary/10 px-2 py-0.5 text-[10px] text-neutral-300">
                                {messageCount}
                              </span>
                            )}
                          </div>
                          {lastMessage && (
                            <span className="text-[11px] text-neutral-500 line-clamp-1">
                              {lastMessage.role === "user" ? "Você: " : "Agente: "}
                              {lastMessagePreview}
                            </span>
                          )}
                          {!lastMessage && (
                            <span className="text-[11px] text-neutral-500 italic">{lastMessagePreview}</span>
                          )}
                        </button>
                        <button
                          onClick={(e) => handleDeleteClick(e, session.id)}
                          className={clsx(
                            "opacity-0 transition-opacity group-hover:opacity-100",
                            "rounded p-1.5 text-neutral-500 hover:bg-red-500/10 hover:text-red-400",
                            "focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-400/50",
                          )}
                          aria-label={`Deletar sessão ${session.title}`}
                          title="Deletar sessão (Delete)"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    )
                  );
                })
            )}
          </div>
        </section>
      </aside>
      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onClose={() => {
          setDeleteDialogOpen(false);
          setSessionToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        sessionTitle={sessionToDeleteTitle}
      />
    </>
  );
}
