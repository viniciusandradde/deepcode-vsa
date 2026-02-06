"use client";

import { useCallback } from "react";
import { ConfigProvider, useConfig } from "./config-context";
import { SessionProvider, useSession } from "./session-context";
import { ChatProvider, useChat } from "./chat-context";

// Re-export types for backward compatibility
export type { Role, GenesisMessage, GenesisSession, ModelOption } from "./types";

export function GenesisUIProvider({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider>
      <SessionProvider>
        <ChatProvider>
          {children}
        </ChatProvider>
      </SessionProvider>
    </ConfigProvider>
  );
}

export function useGenesisUI() {
  const config = useConfig();
  const session = useSession();
  const chat = useChat();

  // Coordinate deleteSession across both session and chat contexts
  const deleteSession = useCallback(async (id: string) => {
    await session.deleteSession(id);
    chat.clearSessionMessages(id);
  }, [session.deleteSession, chat.clearSessionMessages]);

  return {
    // Config
    models: config.models,
    selectedModelId: config.selectedModelId,
    setSelectedModelId: config.setSelectedModelId,
    useTavily: config.useTavily,
    setUseTavily: config.setUseTavily,
    enableVSA: config.enableVSA,
    setEnableVSA: config.setEnableVSA,
    enableGLPI: config.enableGLPI,
    setEnableGLPI: config.setEnableGLPI,
    enableZabbix: config.enableZabbix,
    setEnableZabbix: config.setEnableZabbix,
    enableLinear: config.enableLinear,
    setEnableLinear: config.setEnableLinear,
    enablePlanning: config.enablePlanning,
    setEnablePlanning: config.setEnablePlanning,
    // Session
    sessions: session.sessions,
    currentSessionId: session.currentSessionId,
    createSession: session.createSession,
    selectSession: session.selectSession,
    renameSession: session.renameSession,
    deleteSession,
    // Chat
    isLoading: chat.isLoading,
    isSending: chat.isSending,
    messagesBySession: chat.messagesBySession,
    sendMessage: chat.sendMessage,
    editingMessageId: chat.editingMessageId,
    setEditingMessageId: chat.setEditingMessageId,
    editMessage: chat.editMessage,
    resendMessage: chat.resendMessage,
    cancelMessage: chat.cancelMessage,
    abortControllerRef: chat.abortControllerRef,
  };
}
