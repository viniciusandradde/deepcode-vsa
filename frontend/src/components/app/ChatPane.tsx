"use client";

import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Logo } from "./Logo";
import { MessageInput } from "./MessageInput";
import { MessageItem } from "./MessageItem";
import { SuggestionChips } from "./SuggestionChips";

interface ChatPaneProps {
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export function ChatPane({ sidebarCollapsed = false, onToggleSidebar }: ChatPaneProps) {
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
  } = useGenesisUI();
  const messages = useMemo(() => messagesBySession[currentSessionId] ?? [], [messagesBySession, currentSessionId]);
  const [editingContent, setEditingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLElement>(null);
  const [userHasScrolled, setUserHasScrolled] = useState(false);
  const lastMessageCountRef = useRef(0);

  const handleMessageSubmit = useCallback(async (message: string, streaming: boolean) => {
    setUserHasScrolled(false);
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

  useEffect(() => {
    const mainElement = mainRef.current;
    if (!mainElement) return;

    function handleUserScroll(event: Event) {
      const target = event.target as HTMLElement;
      if (!target) return;

      const { scrollTop, scrollHeight, clientHeight } = target;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;

      if (!isNearBottom) {
        setUserHasScrolled(true);
      }
    }

    mainElement.addEventListener('scroll', handleUserScroll, { passive: true });
    mainElement.addEventListener('wheel', handleUserScroll, { passive: true });
    mainElement.addEventListener('touchmove', handleUserScroll, { passive: true });

    return () => {
      mainElement.removeEventListener('scroll', handleUserScroll);
      mainElement.removeEventListener('wheel', handleUserScroll);
      mainElement.removeEventListener('touchmove', handleUserScroll);
    };
  }, []);

  useEffect(() => {
    const hasNewMessages = messages.length > lastMessageCountRef.current;
    lastMessageCountRef.current = messages.length;

    if (!userHasScrolled || hasNewMessages) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, userHasScrolled]);

  useEffect(() => {
    setUserHasScrolled(false);
    lastMessageCountRef.current = 0;
  }, [currentSessionId]);

  return (
    <div className="flex h-screen flex-1 flex-col bg-gradient-to-br from-[#0d1426] via-[#0d1b2a] to-[#09111e]">
      <header className="flex h-20 items-center justify-between border-b border-vsa-blue/20 px-10 text-slate-100 bg-gradient-to-r from-vsa-blue-dark/10 via-transparent to-vsa-orange-dark/10">
        <div className="flex items-center gap-4">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="p-2 rounded-lg border border-vsa-blue/40 bg-vsa-blue/10 text-vsa-blue-light hover:border-vsa-blue hover:bg-vsa-blue/20 transition-colors"
              aria-label={sidebarCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
              title={sidebarCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                {sidebarCollapsed ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                )}
              </svg>
            </button>
          )}
          <Logo size="md" showText={true} />
          <div className="h-12 w-px bg-vsa-orange/30" />
          <div>
            <div className="text-[11px] uppercase tracking-[0.4em] text-vsa-blue-light/70">Painel de Controle</div>
            <div className="text-2xl font-bold uppercase text-white" style={{ fontFamily: "var(--font-sans)" }}>
              Sessão {currentSessionId ? currentSessionId.slice(0, 12) : "—"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 text-[11px] uppercase tracking-wide">
          {enableVSA && (
            <span className="rounded-md border border-green-500/40 px-3 py-1 text-green-400 bg-green-500/10 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
              VSA Ativo
              {enableGLPI && <span className="text-purple-400">GLPI</span>}
              {enableZabbix && <span className="text-orange-400">Zabbix</span>}
              {enableLinear && <span className="text-blue-400">Linear</span>}
            </span>
          )}
          <span className="rounded-md border border-vsa-blue/40 px-3 py-1 text-vsa-blue-light bg-vsa-blue/5">
            Modelo: <span className="font-semibold text-white">{selectedModelId || "—"}</span>
          </span>
          <span className="rounded-md border border-vsa-orange/40 px-3 py-1 text-vsa-orange-light bg-vsa-orange/5">
            Busca Web: <span className={useTavily ? "text-vsa-orange-light" : "text-slate-400"}>{useTavily ? "Ativa" : "Inativa"}</span>
          </span>
        </div>
      </header>

      <main ref={mainRef} className="relative flex flex-1 flex-col gap-5 overflow-y-auto px-10 py-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(5,173,202,0.12),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(32,51,109,0.18),transparent_55%)]" />
        <div className="relative flex-1 space-y-4">
          {isLoading ? (
            <Card className="border border-white/10 bg-white/5 text-center text-slate-400">
              <CardHeader>Carregando sessões</CardHeader>
              <CardContent>Aguarde enquanto conectamos ao servidor.</CardContent>
            </Card>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-8 py-8">
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-white">Como posso ajudar?</h2>
                <p className="mt-2 text-slate-400">Escolha uma opção ou digite sua pergunta</p>
              </div>
              <SuggestionChips
                onSelect={(cmd) => handleMessageSubmit(cmd, true)}
                disabled={isSending || isLoading}
              />
            </div>
          ) : (
            messages.map((message) => (
              <MessageItem
                key={message.id}
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
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <MessageInput
        onSubmit={handleMessageSubmit}
        isLoading={isLoading}
        isSending={isSending}
        onCancel={cancelMessage}
        currentSessionId={currentSessionId}
      />
    </div>
  );
}
