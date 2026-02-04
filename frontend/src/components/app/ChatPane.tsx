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
    enablePlanning,
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
    <div className="flex h-screen flex-1 flex-col min-w-0">
      <header className="flex h-20 shrink-0 items-center justify-between border-b-2 border-slate-400 px-6 md:px-10 text-slate-900 bg-white shadow-sm">
        <div className="flex items-center gap-4">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="p-2 rounded-lg border-2 border-slate-400 bg-white text-slate-600 shadow-sm hover:border-vsa-orange hover:bg-vsa-orange/5 hover:text-slate-900 transition-colors"
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
          <div className="h-12 w-px bg-vsa-orange/40" />
        </div>
        <div className="flex items-center gap-4 text-[11px] uppercase tracking-wide">
          {enableVSA ? (
            <span className="rounded-md border-2 border-slate-400 px-3 py-1 text-slate-900 bg-white flex items-center gap-2 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse" />
              VSA Ativo
              {enableGLPI && <span className="text-slate-900">GLPI</span>}
              {enableZabbix && <span className="text-slate-900">Zabbix</span>}
              {enableLinear && <span className="text-slate-900">Linear</span>}
              {enablePlanning && <span className="text-slate-900">Planejamento</span>}
            </span>
          ) : (
            <span className="rounded-md border-2 border-slate-400 px-3 py-1 text-slate-900 bg-white flex items-center gap-2 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-slate-400" />
              VSA Inativo
            </span>
          )}
        </div>
      </header>

      <main
        ref={mainRef}
        className="vsa-main-background relative flex flex-1 flex-col gap-5 overflow-y-auto px-6 md:px-10 py-6 md:py-8 min-h-0"
      >
        <div className="relative flex-1 space-y-4">
          {isLoading ? (
            <Card className="border-2 border-slate-400 bg-white text-center text-slate-600">
              <CardHeader>Carregando sessões</CardHeader>
              <CardContent>Aguarde enquanto conectamos ao servidor.</CardContent>
            </Card>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-8 py-8">
              <div className="text-center px-4">
                <h2 className="text-2xl md:text-3xl font-semibold text-slate-900 drop-shadow-sm">
                  Como posso ajudar?
                </h2>
                <p className="mt-2 text-slate-700 font-medium">
                  Escolha uma opção ou digite sua pergunta
                </p>
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
