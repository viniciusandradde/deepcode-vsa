import type { MutableRefObject } from "react";

export type Role = "user" | "assistant";

export interface FileAttachment {
  id: string;
  name: string;
  mime: string;
  size: number;
  url: string;
}

export interface GenesisMessage {
  id: string;
  role: Role;
  content: string;
  timestamp: number;
  modelId?: string;
  usedTavily?: boolean;
  editedAt?: number;
  artifactIds?: string[];
  attachments?: FileAttachment[];
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

export interface AgentOption {
  id: string;
  slug: string;
  name: string;
  description?: string;
  avatar?: string;
  agentType: string;
  isDefault: boolean;
  connectorCount: number;
  skillCount: number;
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
  // Multi-agent support
  agents: AgentOption[];
  selectedAgentId: string;
  setSelectedAgentId: (id: string) => void;
  sessions: GenesisSession[];
  currentSessionId: string;
  createSession: () => Promise<string | undefined>;
  selectSession: (id: string) => Promise<void>;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => Promise<void>;
  messagesBySession: Record<string, GenesisMessage[]>;
  sendMessage: (content: string, useStreaming?: boolean, attachments?: FileAttachment[]) => Promise<void>;
  editingMessageId: string | null;
  setEditingMessageId: (id: string | null) => void;
  editMessage: (messageId: string, newContent: string, attachments?: FileAttachment[]) => void;
  resendMessage: (messageId: string) => Promise<void>;
  cancelMessage: () => void;
  abortControllerRef: MutableRefObject<AbortController | null>;
}
