import type { MutableRefObject } from "react";

export type Role = "user" | "assistant";

export interface GenesisMessage {
  id: string;
  role: Role;
  content: string;
  timestamp: number;
  modelId?: string;
  usedTavily?: boolean;
  editedAt?: number;
}

export interface GenesisSession {
  id: string;
  title: string;
  createdAt: number;
  lastActivityAt?: number;
}

export interface ModelOption {
  id: string;
  label: string;
  inputCost: number;
  outputCost: number;
  isDefault?: boolean;
}

export interface TranslatedError {
  title: string;
  message: string;
  suggestions: string[];
  isRecoverable: boolean;
}

export interface GenesisUIState {
  isLoading: boolean;
  isSending: boolean;
  models: ModelOption[];
  selectedModelId: string;
  setSelectedModelId: (id: string) => void;
  useTavily: boolean;
  setUseTavily: (value: boolean) => void;
  enableVSA: boolean;
  setEnableVSA: (value: boolean) => void;
  enableGLPI: boolean;
  setEnableGLPI: (value: boolean) => void;
  enableZabbix: boolean;
  setEnableZabbix: (value: boolean) => void;
  enableLinear: boolean;
  setEnableLinear: (value: boolean) => void;
  enablePlanning: boolean;
  setEnablePlanning: (value: boolean) => void;
  sessions: GenesisSession[];
  currentSessionId: string;
  createSession: () => Promise<string | undefined>;
  selectSession: (id: string) => Promise<void>;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => Promise<void>;
  messagesBySession: Record<string, GenesisMessage[]>;
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>;
  editingMessageId: string | null;
  setEditingMessageId: (id: string | null) => void;
  editMessage: (messageId: string, newContent: string) => void;
  resendMessage: (messageId: string) => Promise<void>;
  cancelMessage: () => void;
  abortControllerRef: MutableRefObject<AbortController | null>;
}
