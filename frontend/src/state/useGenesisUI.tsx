"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, useRef, type MutableRefObject } from "react";
import { storage } from "@/lib/storage";
import { logger } from "@/lib/logger";


// ============================================
// Error Translation - User-friendly messages
// ============================================
interface TranslatedError {
  title: string;
  message: string;
  suggestions: string[];
  isRecoverable: boolean;
}

function translateApiError(error: string): TranslatedError {
  const errorLower = error.toLowerCase();
  
  // Authentication errors
  if (errorLower.includes("user not found") || errorLower.includes("401")) {
    return {
      title: "Erro de Autenticação",
      message: "A chave de API do OpenRouter é inválida ou expirou.",
      suggestions: [
        "Acesse openrouter.ai e gere uma nova API key",
        "Atualize a variável OPENROUTER_API_KEY no arquivo .env",
        "Reinicie o backend: docker compose restart backend"
      ],
      isRecoverable: false
    };
  }
  
  // Rate limit / quota errors
  if (errorLower.includes("rate limit") || errorLower.includes("429") || errorLower.includes("quota")) {
    return {
      title: "Limite de Requisições",
      message: "O limite de requisições da API foi atingido.",
      suggestions: [
        "Aguarde alguns minutos antes de tentar novamente",
        "Verifique seu plano no OpenRouter",
        "Considere usar um modelo diferente"
      ],
      isRecoverable: true
    };
  }
  
  // Spending limit
  if (errorLower.includes("spend limit") || errorLower.includes("spending limit")) {
    return {
      title: "Limite de Gastos Excedido",
      message: "O limite de gastos da chave API foi excedido.",
      suggestions: [
        "Acesse openrouter.ai/settings e aumente o Spending Limit",
        "Adicione créditos à sua conta",
        "Use um modelo mais econômico"
      ],
      isRecoverable: false
    };
  }
  
  // Model not found
  if (errorLower.includes("model not found") || errorLower.includes("invalid model")) {
    return {
      title: "Modelo Não Encontrado",
      message: "O modelo de IA selecionado não está disponível.",
      suggestions: [
        "Selecione outro modelo na lista",
        "Verifique se o modelo está disponível no OpenRouter"
      ],
      isRecoverable: true
    };
  }
  
  // Connection errors
  if (errorLower.includes("fetch") || errorLower.includes("network") || errorLower.includes("connection") || errorLower.includes("econnrefused")) {
    return {
      title: "Erro de Conexão",
      message: "Não foi possível conectar ao servidor.",
      suggestions: [
        "Verifique se o backend está rodando (porta 8000)",
        "Execute: docker compose up -d",
        "Verifique sua conexão de internet"
      ],
      isRecoverable: true
    };
  }
  
  // Timeout
  if (errorLower.includes("timeout") || errorLower.includes("timed out")) {
    return {
      title: "Tempo Esgotado",
      message: "A requisição demorou muito para responder.",
      suggestions: [
        "Tente novamente com uma pergunta mais curta",
        "Verifique a conexão com a internet",
        "O servidor pode estar sobrecarregado"
      ],
      isRecoverable: true
    };
  }
  
  // Server errors
  if (errorLower.includes("500") || errorLower.includes("internal server error")) {
    return {
      title: "Erro no Servidor",
      message: "Ocorreu um erro interno no servidor.",
      suggestions: [
        "Verifique os logs: docker logs ai_agent_backend",
        "Reinicie o backend: docker compose restart backend",
        "Tente novamente em alguns segundos"
      ],
      isRecoverable: true
    };
  }
  
  // Default error
  return {
    title: "Erro Inesperado",
    message: error,
    suggestions: [
      "Tente novamente",
      "Verifique os logs do backend para mais detalhes"
    ],
    isRecoverable: true
  };
}

function formatErrorMessage(translated: TranslatedError): string {
  const icon = translated.isRecoverable ? "⚠️" : "❌";
  const suggestions = translated.suggestions.map((s, i) => `${i + 1}. ${s}`).join("\n");
  
  return `${icon} **${translated.title}**

${translated.message}

**Como resolver:**
${suggestions}`;
}

// Custom hook for localStorage persistence
function useLocalStorageState(key: string, defaultValue: boolean): [boolean, (value: boolean) => void] {
  // Always start with defaultValue for SSR
  const [state, setState] = useState<boolean>(defaultValue);
  const [isHydrated, setIsHydrated] = useState(false);

  // Hydrate from localStorage on mount (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(key);
      logger.perf(`[useLocalStorageState] Hydrating ${key}:`, saved);

      if (saved !== null) {
        const parsedValue = saved === 'true';
        setState(parsedValue);
        logger.perf(`[useLocalStorageState] Restored ${key}:`, parsedValue);
      }

      setIsHydrated(true);
    }
  }, [key]);

  const setValue = useCallback((value: boolean) => {
    setState(value);
    if (typeof window !== 'undefined') {
      localStorage.setItem(key, String(value));
      logger.perf(`[useLocalStorageState] Saved ${key}:`, value);
    }
  }, [key]);

  return [state, setValue];
}

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

interface GenesisUIState {
  isLoading: boolean;
  isSending: boolean;
  models: ModelOption[];
  selectedModelId: string;
  setSelectedModelId: (id: string) => void;
  useTavily: boolean;
  setUseTavily: (value: boolean) => void;
  // VSA Integration states (Task 1.2, 1.3)
  enableVSA: boolean;
  setEnableVSA: (value: boolean) => void;
  enableGLPI: boolean;
  setEnableGLPI: (value: boolean) => void;
  enableZabbix: boolean;
  setEnableZabbix: (value: boolean) => void;
  enableLinear: boolean;
  setEnableLinear: (value: boolean) => void;
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

const GenesisUIContext = createContext<GenesisUIState | null>(null);

export function GenesisUIProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  // Tavily Search - Persisted in localStorage
  const [useTavily, setUseTavily] = useLocalStorageState('vsa_useTavily', false);
  // VSA Integration states (Task 1.2, 1.3) - Persisted in localStorage
  const [enableVSA, setEnableVSA] = useLocalStorageState('vsa_enableVSA', false);
  const [enableGLPI, setEnableGLPI] = useLocalStorageState('vsa_enableGLPI', false);
  const [enableZabbix, setEnableZabbix] = useLocalStorageState('vsa_enableZabbix', false);
  const [enableLinear, setEnableLinear] = useLocalStorageState('vsa_enableLinear', false);
  const [sessions, setSessions] = useState<GenesisSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messagesBySession, setMessagesBySession] = useState<Record<string, GenesisMessage[]>>({});
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const abortControllerRef = useContext(GenesisUIContext)?.abortControllerRef ?? useRef<AbortController | null>(null);

  useEffect(() => {
    async function bootstrap() {
      setIsLoading(true);
      try {
        await Promise.all([loadModels(), loadSessions()]);
      } finally {
        setIsLoading(false);
      }
    }
    bootstrap().catch(console.error);
  }, []);

  async function loadModels() {
    try {
      const res = await fetch("/api/models", { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      const mapped: ModelOption[] = (data.models ?? []).map((model: any) => ({
        id: model.id,
        label: model.label,
        inputCost: model.input_cost ?? 0,
        outputCost: model.output_cost ?? 0,
        isDefault: model.default ?? false,
      }));
      setModels(mapped);
      // Seleciona o modelo marcado como padrão, ou o primeiro da lista
      const defaultModel = mapped.find(m => m.isDefault) ?? mapped[0];
      if (!selectedModelId && defaultModel) {
        setSelectedModelId(defaultModel.id);
      }
    } catch (error) {
      console.error("Error loading models:", error);
    }
  }

  async function loadSessions() {
    // Ler sessões do localStorage primeiro (para fallback)
    const storedSessions = storage.sessions.getAll();

    try {
      // Fonte primária: API (backend + checkpoints)
      const res = await fetch("/api/threads", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        const threads = Array.isArray(data.threads) ? data.threads : [];

        const apiSessions: GenesisSession[] = threads.map((thread: any) => {
          const id = thread.thread_id || thread.id;
          // last_ts vem do backend a partir do checkpoint->>'ts'
          const lastTs = thread.last_ts ? Date.parse(thread.last_ts) : Date.now();
          const dt = new Date(lastTs);
          const time = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          const date = dt.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

          const title =
            thread.title ||
            `Sessão de ${date} ${time}`;

          return {
            id,
            title,
            createdAt: lastTs, // proxy de criação
            lastActivityAt: lastTs,
          };
        });

        setSessions(apiSessions);

        // Atualiza cache local para uso offline (opcional)
        storage.sessions.save(apiSessions.map(s => ({
          id: s.id,
          title: s.title,
          createdAt: s.createdAt,
          lastAccessed: Date.now(),
          messageCount: 0,
        })));

        // Não carregamos mensagens do localStorage, pois o histórico vem da API
        // via fetchSession(sessionId) quando o usuário seleciona a sessão.

        if (!currentSessionId && apiSessions[0]) {
          setCurrentSessionId(apiSessions[0].id);
        }
      } else if (storedSessions.length === 0) {
        // Se não houver sessões, cria uma nova
        const newSessionId = await createSession();
        if (newSessionId) {
          setCurrentSessionId(newSessionId);
        }
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
      // Fallback to localStorage only
      if (storedSessions.length > 0) {
        setSessions(storedSessions.map((s) => ({
          id: s.id,
          title: s.title,
          createdAt: s.createdAt,
        })));
      }
    }
  }

  const createSession = useCallback(async (): Promise<string | undefined> => {
    try {
      const res = await fetch("/api/threads", { method: "POST" });
      if (!res.ok) return;
      const data = await res.json();
      const threadId = data.thread_id || data.thread?.thread_id || data.id;
      if (!threadId) return;

      const session: GenesisSession = {
        id: threadId,
        title: `Nova Sessão ${new Date().toLocaleTimeString()}`,
        createdAt: Date.now(),
      };

      setSessions((prev) => [session, ...prev]);
      setMessagesBySession((prev) => ({ ...prev, [session.id]: [] }));
      setCurrentSessionId(session.id);

      // Save to localStorage
      storage.sessions.add({
        id: session.id,
        title: session.title,
        createdAt: session.createdAt,
        lastAccessed: Date.now(),
        messageCount: 0,
      });
      storage.messages.save(session.id, []);

      return session.id;
    } catch (error) {
      console.error("Error creating session:", error);
      return undefined;
    }
  }, []);

  const fetchSession = useCallback(async (sessionId: string, merge: boolean = false) => {
    try {
      const res = await fetch(`/api/threads/${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();
      const messages = (data.messages || []).map((msg: any, idx: number) => ({
        id: msg.id || `msg-${idx}`,
        role: msg.role === "user" ? "user" : "assistant",
        content: typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content),
        timestamp: msg.timestamp || Date.now(),
        modelId: msg.modelId,
        usedTavily: msg.usedTavily,
      }));

      if (merge) {
        // Merge with existing messages instead of replacing
        setMessagesBySession((prev) => {
          const existing = prev[sessionId] || [];
          // Create a map of existing messages by ID
          const existingMap = new Map(existing.map(msg => [msg.id, msg]));
          // Update with new messages, preserving existing ones
          messages.forEach((msg: GenesisMessage) => {
            existingMap.set(msg.id, msg);
          });
          return { ...prev, [sessionId]: Array.from(existingMap.values()) };
        });
      } else {
        setMessagesBySession((prev) => ({ ...prev, [sessionId]: messages }));
      }
    } catch (error) {
      console.error("Error fetching session:", error);
    }
  }, []);

  const selectSession = useCallback(async (id: string) => {
    setCurrentSessionId(id);
    await fetchSession(id);
  }, [fetchSession]);

  // ✅ Auto-load messages when currentSessionId changes
  useEffect(() => {
    if (currentSessionId && !messagesBySession[currentSessionId]) {
      logger.debug(`[useGenesisUI] Auto-loading messages for session: ${currentSessionId}`);
      fetchSession(currentSessionId).catch(console.error);
    }
  }, [currentSessionId, fetchSession, messagesBySession]);

  const renameSession = useCallback((id: string, title: string) => {
    setSessions((prev) => prev.map((session) => (session.id === id ? { ...session, title } : session)));
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    try {
      // Chamar API para deletar no backend
      const res = await fetch(`/api/threads/${id}`, {
        method: "DELETE",
      });

      if (!res.ok && res.status !== 204) {
        console.error("Failed to delete thread in backend:", res.status);
        // Continua com limpeza local mesmo se backend falhar
      }
    } catch (error) {
      console.error("Error deleting thread:", error);
      // Continua com limpeza local mesmo se API falhar
    }

    // Limpar do estado local
    setSessions((prev) => {
      const nextSessions = prev.filter((session) => session.id !== id);
      setCurrentSessionId((prevId) => (prevId === id ? nextSessions[0]?.id ?? "" : prevId));
      return nextSessions;
    });

    // Limpar mensagens do estado
    setMessagesBySession((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });

    // Limpar do localStorage
    storage.sessions.remove(id);
    storage.messages.clear(id);
  }, []);

  const cancelMessage = useCallback(() => {
    if (abortControllerRef.current) {
      logger.debug("Cancelling message request...");
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsSending(false);
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, useStreaming: boolean = true) => {
      let threadId = currentSessionId;
      if (!threadId) {
        const newThreadId = await createSession();
        threadId = newThreadId || currentSessionId || sessions[0]?.id || "";
      }
      if (!threadId) return;

      // Número de mensagens antes de adicionar a nova (para auto-título)
      const previousMessagesCount = messagesBySession[threadId]?.length ?? 0;

      const optimistic: GenesisMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: Date.now(),
        modelId: selectedModelId,
        usedTavily: useTavily,
      };

      setMessagesBySession((prev) => {
        const existing = prev[threadId] ?? [];
        const updated = { ...prev, [threadId]: [...existing, optimistic] };
        // Save to localStorage
        storage.messages.save(threadId, updated[threadId]);
        return updated;
      });
      setCurrentSessionId(threadId);

      // Atualizar lastActivityAt e, se for a primeira mensagem da sessão,
      // gerar um título automático amigável baseado no conteúdo
      setSessions((prev) => {
        return prev.map((session) => {
          if (session.id !== threadId) return session;

          const now = Date.now();
          let title = session.title;

          // Auto título apenas se for a primeira mensagem e o título ainda
          // estiver no formato padrão "Sessão de ..." ou "Nova Sessão ..."
          const isFirstMessage = previousMessagesCount === 0;
          const isDefaultTitle =
            title.startsWith("Sessão de ") || title.startsWith("Nova Sessão");

          if (isFirstMessage && isDefaultTitle) {
            const plain = content.replace(/\s+/g, " ").trim();
            const snippet = plain.slice(0, 60);
            if (snippet) {
              const autoTitle = snippet.charAt(0).toUpperCase() + snippet.slice(1);
              title = autoTitle;

              // Atualizar cache de sessões no localStorage
              const storedSessions = storage.sessions.getAll();
              const updatedStored = storedSessions.map((s) =>
                s.id === session.id ? { ...s, title: autoTitle } : s,
              );
              storage.sessions.save(updatedStored);
            }
          }

          return {
            ...session,
            title,
            lastActivityAt: now,
          };
        });
      });

      setIsSending(true);

      const thinkingMessageId = `thinking-${Date.now()}`;
      const thinkingMessage: GenesisMessage = {
        id: thinkingMessageId,
        role: "assistant",
        content: "Pensando...",
        timestamp: Date.now(),
      };

      setMessagesBySession((prev) => {
        const existing = prev[threadId] ?? [];
        return { ...prev, [threadId]: [...existing, thinkingMessage] };
      });

      try {
        if (useStreaming) {
          // Streaming mode
          // Setup AbortController
          const controller = new AbortController();
          abortControllerRef.current = controller;

          const res = await fetch(`/api/threads/${threadId}/messages/stream`, {
            signal: controller.signal,
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content,
              model: selectedModelId,
              useTavily,
              thread_id: threadId,
              // VSA Integration flags (Task 1.1)
              enable_vsa: enableVSA,
              enable_glpi: enableGLPI,
              enable_zabbix: enableZabbix,
              enable_linear: enableLinear,
            }),
          });

          if (!res.ok) {
            // Try to get error details from response
            let errorMessage = `Stream failed: ${res.status}`;
            let errorDetails: any = {};

            try {
              const errorData = await res.json();
              console.error("Stream error details:", errorData);
              errorDetails = errorData;

              // Try different error formats
              if (typeof errorData.error === "string") {
                errorMessage = errorData.error;
              } else if (errorData.details) {
                if (typeof errorData.details === "string") {
                  errorMessage = errorData.details;
                } else {
                  errorMessage = errorData.details.error || errorData.details.message || JSON.stringify(errorData.details);
                }
              } else if (errorData.message) {
                errorMessage = errorData.message;
              } else if (errorData.detail) {
                errorMessage = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
              } else if (Object.keys(errorData).length > 0) {
                // If we have data but no clear error message, stringify it
                errorMessage = JSON.stringify(errorData);
              }
            } catch (jsonError) {
              // If JSON parse fails, try text
              try {
                const errorText = await res.text();
                console.error("Stream error (text):", errorText);
                errorMessage = errorText || errorMessage;
                errorDetails = { text: errorText };
              } catch (textError) {
                console.error("Stream failed with status:", res.status, "Could not read response");
                errorDetails = { status: res.status, statusText: res.statusText };
              }
            }

            // Create a more informative error message
            const fullErrorMessage = errorMessage || `Stream failed with status ${res.status}`;
            const error = new Error(fullErrorMessage);
            (error as any).details = errorDetails;
            (error as any).status = res.status;
            throw error;
          }

          const reader = res.body?.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let accumulatedContent = "";
          const assistantMessageId = `assistant-${Date.now()}`;

          // Remove "Pensando..." e adiciona mensagem vazia do assistente
          // IMPORTANTE: Preservar todas as mensagens do usuário e garantir que a mensagem do assistente esteja vazia
          setMessagesBySession((prev) => {
            const existing = prev[threadId] ?? [];
            logger.perf("[STREAM] Before removing thinking, messages count:", existing.length);
            logger.perf("[STREAM] Messages:", existing.map(m => ({ id: m.id, role: m.role, content: m.content.substring(0, 50) })));

            // Remove apenas thinking, preserva tudo mais (incluindo mensagem do usuário)
            const withoutThinking = existing.filter(msg => msg.id !== thinkingMessageId);

            // Garantir que não há mensagem do assistente com conteúdo incorreto
            // Se houver alguma mensagem do assistente vazia ou com conteúdo errado, removê-la
            const cleaned = withoutThinking.filter(msg => {
              // Manter todas as mensagens do usuário
              if (msg.role === "user") return true;
              // Remover mensagens do assistente que estejam vazias ou com conteúdo incorreto
              // (exceto se for a mensagem que vamos criar)
              if (msg.role === "assistant" && (!msg.content || msg.content.trim() === "")) {
                return false; // Remove mensagens vazias antigas
              }
              return true;
            });

            const assistantMessage: GenesisMessage = {
              id: assistantMessageId,
              role: "assistant",
              content: "", // SEMPRE vazio inicialmente
              timestamp: Date.now(),
              modelId: selectedModelId,
              usedTavily: useTavily,
            };

            const updated = [...cleaned, assistantMessage];
            logger.perf("[STREAM] After adding assistant message, messages count:", updated.length);
            logger.perf("[STREAM] Updated messages:", updated.map(m => ({ id: m.id, role: m.role, content: m.content.substring(0, 50) || "(vazio)" })));

            return { ...prev, [threadId]: updated };
          });

          if (reader) {
            let streamActive = true;
            let totalBytesReceived = 0;
            let totalLinesProcessed = 0;
            try {
              logger.perf("[STREAM] Starting to read stream...");
              while (true) {
                const { done, value } = await reader.read();
                if (done) {
                  logger.perf("[STREAM] Stream completed. Total bytes:", totalBytesReceived, "Total lines:", totalLinesProcessed, "Final buffer:", buffer.length);
                  break;
                }

                if (value) {
                  totalBytesReceived += value.length;
                  buffer += decoder.decode(value, { stream: true });
                }

                // Process buffer into lines
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                totalLinesProcessed += lines.length;
                logger.perf("[STREAM] Received chunk:", value?.length || 0, "bytes. Buffer now has", buffer.length, "chars. Processing", lines.length, "lines");

                for (const line of lines) {
                  if (line.trim() === "") {
                    logger.perf("[STREAM] Skipping empty line");
                    continue; // Skip empty lines
                  }

                  logger.perf("[STREAM] Processing line:", line.substring(0, 100));

                  // Try to parse as SSE data
                  if (line.startsWith("data: ")) {
                    try {
                      const jsonStr = line.slice(6);
                      logger.perf("[STREAM] Parsing JSON:", jsonStr.substring(0, 200));
                      const data = JSON.parse(jsonStr);
                      logger.perf("[STREAM] Parsed data type:", data.type, "has content:", !!data.content, "content length:", data.content?.length || 0);

                      if (data.type === "start") {
                        // Backend confirmou conexão; nenhuma ação necessária
                        continue;
                      }
                      if (data.type === "content" && data.content !== undefined && data.content !== null) {
                        // Normalizar content para string (backend já envia string; fallback para listas)
                        let rawContent = data.content;
                        if (typeof rawContent !== "string") {
                          if (Array.isArray(rawContent)) {
                            rawContent = rawContent.map((b: unknown) =>
                              typeof b === "string" ? b : (b && typeof b === "object" && "text" in b ? String((b as { text?: string }).text ?? "") : "")
                            ).join("");
                          } else {
                            rawContent = String(rawContent);
                          }
                        }
                        // Handle escaped newlines - convert \n to actual newlines
                        const processedContent = rawContent.replace(/\\n/g, "\n").replace(/\\t/g, "\t");

                        // If this is a final content update (complete content), replace instead of append
                        if (data.final === true) {
                          logger.perf("[STREAM] Received final complete content, replacing accumulated content");
                          logger.perf("[STREAM] Final content length:", processedContent.length);
                          logger.perf("[STREAM] Previous accumulated length:", accumulatedContent.length);
                          accumulatedContent = processedContent;
                          logger.perf("[STREAM] After replacement, accumulated length:", accumulatedContent.length);
                        } else {
                          accumulatedContent += processedContent;
                        }
                        logger.perf("[STREAM] Content updated, total length:", accumulatedContent.length, "new chunk:", processedContent.length, "is final:", data.final || false);
                        // Update state immediately
                        // IMPORTANTE: Garantir que apenas a mensagem do assistente com o ID correto seja atualizada
                        setMessagesBySession((prev) => {
                          const existing = prev[threadId] ?? [];
                          const updated = existing.map((msg) => {
                            // Apenas atualizar a mensagem do assistente com o ID correto
                            if (msg.id === assistantMessageId && msg.role === "assistant") {
                              return { ...msg, content: accumulatedContent };
                            }
                            // Garantir que mensagens do usuário nunca sejam modificadas
                            if (msg.role === "user") {
                              return msg; // Retornar sem modificações
                            }
                            return msg;
                          });
                          // Save to localStorage on each update to prevent data loss
                          storage.messages.save(threadId, updated);
                          return {
                            ...prev,
                            [threadId]: updated,
                          };
                        });
                      } else if (data.type === "chunk" && data.data) {
                        // Try to extract content from chunk data if content type not received
                        logger.perf("[STREAM] Received chunk data, trying to extract content");
                        try {
                          // Chunk data might contain the message content
                          const chunkStr = data.data;
                          // Look for AIMessage or content in the chunk
                          if (chunkStr.includes("AIMessage") || chunkStr.includes("content=")) {
                            // Try to extract content from string representation
                            const contentMatch = chunkStr.match(/content=['"]([^'"]+)['"]/);
                            if (contentMatch && contentMatch[1]) {
                              const extractedContent = contentMatch[1];
                              if (extractedContent.length > accumulatedContent.length) {
                                const newContent = extractedContent.substring(accumulatedContent.length);
                                accumulatedContent = extractedContent;
                                logger.perf("[STREAM] Extracted content from chunk:", newContent.length, "chars");
                                setMessagesBySession((prev) => {
                                  const existing = prev[threadId] ?? [];
                                  return {
                                    ...prev,
                                    [threadId]: existing.map((msg) => {
                                      // Apenas atualizar a mensagem do assistente com o ID correto
                                      if (msg.id === assistantMessageId && msg.role === "assistant") {
                                        return { ...msg, content: accumulatedContent };
                                      }
                                      // Garantir que mensagens do usuário nunca sejam modificadas
                                      return msg;
                                    }),
                                  };
                                });
                              }
                            }
                          }
                        } catch (extractError) {
                          console.error("[STREAM] Error extracting content from chunk:", extractError);
                        }
                      } else if (data.type === "done") {
                        logger.perf("[STREAM] Stream done signal received");
                        logger.perf("[STREAM] Final content length from done message:", data.total_length || "not provided");
                        logger.perf("[STREAM] Accumulated content length:", accumulatedContent.length);
                        streamActive = false;

                        // Check if we received the expected total length
                        if (data.total_length && data.total_length > accumulatedContent.length) {
                          console.warn(`[STREAM] WARNING: Expected ${data.total_length} chars but only have ${accumulatedContent.length} chars!`);
                          console.warn("[STREAM] Content may be incomplete. Check if final content message was received.");
                        }

                        // Process any remaining content in buffer before final save
                        if (buffer.trim()) {
                          logger.perf("[STREAM] Processing remaining buffer:", buffer.substring(0, 100));
                          // Try to parse remaining buffer as JSON
                          try {
                            if (buffer.startsWith("data: ")) {
                              const jsonStr = buffer.slice(6);
                              const bufferData = JSON.parse(jsonStr);
                              if (bufferData.type === "content" && bufferData.content) {
                                const processedContent = typeof bufferData.content === 'string'
                                  ? bufferData.content.replace(/\\n/g, '\n').replace(/\\t/g, '\t')
                                  : bufferData.content;
                                accumulatedContent += processedContent;
                                logger.perf("[STREAM] Added buffer content, new total length:", accumulatedContent.length);
                              }
                            }
                          } catch (e) {
                            logger.perf("[STREAM] Could not parse remaining buffer as JSON:", e);
                          }
                        }

                        // Ensure final content is saved
                        if (accumulatedContent) {
                          logger.perf("[STREAM] Saving final content. Length:", accumulatedContent.length);
                          logger.perf("[STREAM] Final content preview (first 200):", accumulatedContent.substring(0, 200));
                          logger.perf("[STREAM] Final content preview (last 200):", accumulatedContent.substring(Math.max(0, accumulatedContent.length - 200)));
                          setMessagesBySession((prev) => {
                            const existing = prev[threadId] ?? [];
                            const updated = existing.map((msg) => {
                              // Apenas atualizar a mensagem do assistente com o ID correto
                              if (msg.id === assistantMessageId && msg.role === "assistant") {
                                return { ...msg, content: accumulatedContent };
                              }
                              // Garantir que mensagens do usuário nunca sejam modificadas
                              return msg;
                            });
                            const savedMsg = updated.find(m => m.id === assistantMessageId);
                            logger.perf("[STREAM] Messages after saving content:", updated.length);
                            logger.perf("[STREAM] Saved message content length:", savedMsg?.content?.length || 0);
                            // Save to localStorage
                            storage.messages.save(threadId, updated);
                            return { ...prev, [threadId]: updated };
                          });
                        } else {
                          console.warn("[STREAM] Stream done but no content accumulated!");
                          // Try to get content from the last message if available
                          setMessagesBySession((prev) => {
                            const existing = prev[threadId] ?? [];
                            const lastAssistant = existing.find(msg => msg.id === assistantMessageId);
                            if (lastAssistant && !lastAssistant.content) {
                              console.warn("[STREAM] Assistant message exists but is empty, removing it");
                              // Remove empty assistant message
                              return { ...prev, [threadId]: existing.filter(msg => msg.id !== assistantMessageId) };
                            }
                            return prev;
                          });
                        }
                        // Don't call fetchSession as it might overwrite messages
                        // await fetchSession(threadId);
                      } else if (data.type === "error") {
                        console.error("[STREAM] Error from stream:", data.error);
                        const translated = translateApiError(data.error || "Erro desconhecido");
                        const formattedError = formatErrorMessage(translated);
                        throw new Error(formattedError);
                      } else if (data.type === "chunk") {
                        // Log chunk data for debugging
                        logger.perf("[STREAM] Chunk received:", data.data?.substring(0, 100));
                      }
                    } catch (e) {
                      console.error("[STREAM] Error parsing line:", line, e);
                      // Don't throw, continue processing
                    }
                  } else if (line.trim() !== "") {
                    // Log non-data lines for debugging
                    logger.perf("[STREAM] Non-data line:", line.substring(0, 100));
                  }
                }
              }

              // If stream ended without "done" message, ensure content is saved
              // Also process any remaining buffer
              if (buffer.trim() && accumulatedContent) {
                logger.perf("[STREAM] Processing final buffer before saving. Buffer length:", buffer.length);
                try {
                  // Try to extract any remaining content from buffer
                  const bufferLines = buffer.split("\n");
                  for (const bufferLine of bufferLines) {
                    if (bufferLine.trim() && bufferLine.startsWith("data: ")) {
                      try {
                        const jsonStr = bufferLine.slice(6);
                        const bufferData = JSON.parse(jsonStr);
                        if (bufferData.type === "content" && bufferData.content) {
                          const processedContent = typeof bufferData.content === 'string'
                            ? bufferData.content.replace(/\\n/g, '\n').replace(/\\t/g, '\t')
                            : bufferData.content;
                          accumulatedContent += processedContent;
                          logger.perf("[STREAM] Added final buffer content, new total:", accumulatedContent.length);
                        }
                      } catch (e) {
                        logger.perf("[STREAM] Could not parse final buffer line:", e);
                      }
                    }
                  }
                } catch (e) {
                  logger.perf("[STREAM] Error processing final buffer:", e);
                }
              }

              if (streamActive && accumulatedContent) {
                logger.perf("[STREAM] Stream ended without done message, saving content. Length:", accumulatedContent.length);
                logger.perf("[STREAM] Final content preview:", accumulatedContent.substring(0, 200));
                logger.perf("[STREAM] Final content end preview:", accumulatedContent.substring(Math.max(0, accumulatedContent.length - 200)));
                setMessagesBySession((prev) => {
                  const existing = prev[threadId] ?? [];
                  const updated = existing.map((msg) => {
                    // Apenas atualizar a mensagem do assistente com o ID correto
                    if (msg.id === assistantMessageId && msg.role === "assistant") {
                      return { ...msg, content: accumulatedContent };
                    }
                    // Garantir que mensagens do usuário nunca sejam modificadas
                    return msg;
                  });
                  logger.perf("[STREAM] Final message content length:", updated.find(m => m.id === assistantMessageId)?.content?.length || 0);
                  // Save to localStorage
                  storage.messages.save(threadId, updated);
                  return { ...prev, [threadId]: updated };
                });
              } else if (streamActive && !accumulatedContent) {
                console.warn("[STREAM] Stream ended but no content was accumulated!");
                // Remove empty assistant message
                setMessagesBySession((prev) => {
                  const existing = prev[threadId] ?? [];
                  return { ...prev, [threadId]: existing.filter(msg => msg.id !== assistantMessageId) };
                });
              }

              // Final check: ensure content is saved even if stream completed normally
              logger.perf("[STREAM] Stream loop ended. Final accumulatedContent length:", accumulatedContent.length);
              if (accumulatedContent) {
                logger.perf("[STREAM] Final check - ensuring content is saved. Length:", accumulatedContent.length);
                logger.perf("[STREAM] Final content preview (first 300):", accumulatedContent.substring(0, 300));
                logger.perf("[STREAM] Final content preview (last 300):", accumulatedContent.substring(Math.max(0, accumulatedContent.length - 300)));
                setMessagesBySession((prev) => {
                  const existing = prev[threadId] ?? [];
                  const assistantMsg = existing.find(msg => msg.id === assistantMessageId);
                  logger.perf("[STREAM] Current assistant message content length:", assistantMsg?.content?.length || 0);
                  if (!assistantMsg || assistantMsg.content !== accumulatedContent) {
                    logger.perf("[STREAM] Content mismatch or missing! Updating...");
                    logger.perf("[STREAM] Expected length:", accumulatedContent.length, "Current length:", assistantMsg?.content?.length || 0);
                    const updated = existing.map((msg) => {
                      // Apenas atualizar a mensagem do assistente com o ID correto
                      if (msg.id === assistantMessageId && msg.role === "assistant") {
                        return { ...msg, content: accumulatedContent };
                      }
                      // Garantir que mensagens do usuário nunca sejam modificadas
                      return msg;
                    });
                    // If message doesn't exist, add it
                    if (!assistantMsg) {
                      logger.perf("[STREAM] Assistant message not found, creating new one");
                      updated.push({
                        id: assistantMessageId,
                        role: "assistant",
                        content: accumulatedContent,
                        timestamp: Date.now(),
                        modelId: selectedModelId,
                        usedTavily: useTavily,
                      });
                    }
                    const finalMsg = updated.find(m => m.id === assistantMessageId);
                    logger.perf("[STREAM] Final message after update - length:", finalMsg?.content?.length || 0);
                    storage.messages.save(threadId, updated);
                    logger.perf("[STREAM] Saved to localStorage. Final message count:", updated.length);
                    return { ...prev, [threadId]: updated };
                  }
                  logger.perf("[STREAM] Content already matches, no update needed");
                  return prev;
                });
              } else {
                console.warn("[STREAM] WARNING: Stream completed but accumulatedContent is empty!");
              }
            } catch (streamError) {
              // Cancelamento pelo usuário: não tratar como erro
              if (streamError instanceof Error && streamError.name === "AbortError") {
                setMessagesBySession((prev) => {
                  const existing = prev[threadId] ?? [];
                  const filtered = existing.filter((msg) => msg.id !== thinkingMessageId);
                  const cleaned = filtered.filter(
                    (msg) => !(msg.role === "assistant" && msg.content === "")
                  );
                  return { ...prev, [threadId]: cleaned };
                });
                return;
              }
              console.error("[STREAM] Error reading stream:", streamError);
              throw streamError;
            }
          } else {
            console.error("[STREAM] No reader available");
            throw new Error("Stream reader not available");
          }
        } else {
          // Non-streaming mode (fallback)
          const controller = new AbortController();
          abortControllerRef.current = controller;

          const res = await fetch(`/api/threads/${threadId}/messages`, {
            signal: controller.signal,
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content, model: selectedModelId, useTavily }),
          });

          if (!res.ok) {
            const errorText = await res.text();
            throw new Error(errorText || "Failed to send message");
          }

          const data = await res.json();
          const responseContent = data.response || data.result?.response || "Sem resposta";

          setMessagesBySession((prev) => {
            const existing = prev[threadId] ?? [];
            const withoutThinking = existing.filter(msg => msg.id !== thinkingMessageId);
            const assistantMessage: GenesisMessage = {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              content: responseContent,
              timestamp: Date.now(),
              modelId: selectedModelId,
              usedTavily: useTavily,
            };
            return { ...prev, [threadId]: [...withoutThinking, assistantMessage] };
          });

          await fetchSession(threadId);
        }
      } catch (error) {
        // Cancelamento pelo usuário (Stop): não exibir erro no chat nem no console
        if (error instanceof Error && error.name === "AbortError") {
          setMessagesBySession((prev) => {
            const existing = prev[threadId] ?? [];
            const filtered = existing.filter((msg) => msg.id !== thinkingMessageId);
            const cleaned = filtered.filter(
              (msg) => !(msg.role === "assistant" && msg.content === "")
            );
            return { ...prev, [threadId]: cleaned };
          });
          return;
        }

        console.error("Error sending message:", error);
        // Remove only thinking message, preserve user message
        setMessagesBySession((prev) => {
          const existing = prev[threadId] ?? [];
          const filtered = existing.filter((msg) => msg.id !== thinkingMessageId);
          const cleaned = filtered.filter(
            (msg) => !(msg.role === "assistant" && msg.content === "")
          );
          return { ...prev, [threadId]: cleaned };
        });

        // Extract detailed error information
        let errorMsg = error instanceof Error ? error.message : String(error);
        let errorDetails = "";

        if (error instanceof Error) {
          const errorAny = error as any;
          if (errorAny.details) {
            console.error("Error details:", errorAny.details);
            if (typeof errorAny.details === "object") {
              errorDetails = `\n\n**Detalhes técnicos:**\n\`\`\`json\n${JSON.stringify(errorAny.details, null, 2)}\n\`\`\``;
            } else {
              errorDetails = `\n\n**Detalhes:** ${errorAny.details}`;
            }
          }
          if (errorAny.status) {
            errorDetails += `\n**Status HTTP:** ${errorAny.status}`;
          }
        }

        // Show error to user with detailed message
        // Use translated error if not already formatted
        let finalErrorContent = errorMsg;
        if (!errorMsg.includes("**Como resolver:**")) {
          const translated = translateApiError(errorMsg);
          finalErrorContent = formatErrorMessage(translated);
        }
        const errorMessage: GenesisMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: finalErrorContent + errorDetails,
          timestamp: Date.now(),
        };
        setMessagesBySession((prev) => {
          const existing = prev[threadId] ?? [];
          return { ...prev, [threadId]: [...existing, errorMessage] };
        });
      } finally {
        setIsSending(false);
      }
    },
    [createSession, currentSessionId, fetchSession, selectedModelId, sessions, useTavily],
  );

  const editMessage = useCallback((messageId: string, newContent: string) => {
    setMessagesBySession((prev) => {
      const updated = { ...prev };
      for (const sessionId in updated) {
        const messages = updated[sessionId];
        const index = messages.findIndex((msg) => msg.id === messageId);
        if (index !== -1) {
          updated[sessionId] = messages.map((msg, i) =>
            i === index
              ? { ...msg, content: newContent, editedAt: Date.now() }
              : msg
          );
          // Save to localStorage
          storage.messages.save(sessionId, updated[sessionId]);
          break;
        }
      }
      return updated;
    });
    setEditingMessageId(null);
  }, []);

  const resendMessage = useCallback(
    async (messageId: string) => {
      const threadId = currentSessionId;
      if (!threadId) return;

      // Find the message
      const messages = messagesBySession[threadId] || [];
      const messageIndex = messages.findIndex((msg) => msg.id === messageId);
      if (messageIndex === -1) return;

      const message = messages[messageIndex];
      if (message.role !== "user") return;

      // Remove all messages after this one (including assistant responses)
      const messagesToKeep = messages.slice(0, messageIndex + 1);
      setMessagesBySession((prev) => ({
        ...prev,
        [threadId]: messagesToKeep,
      }));
      storage.messages.save(threadId, messagesToKeep);

      // Send the message again
      await sendMessage(message.content, true);
    },
    [currentSessionId, messagesBySession, sendMessage]
  );

  const value = useMemo<GenesisUIState>(
    () => ({
      isLoading,
      isSending,
      models,
      selectedModelId,
      setSelectedModelId,
      useTavily,
      setUseTavily,
      // VSA Integration states
      enableVSA,
      setEnableVSA,
      enableGLPI,
      setEnableGLPI,
      enableZabbix,
      setEnableZabbix,
      enableLinear,
      setEnableLinear,
      sessions,
      currentSessionId,
      createSession,
      selectSession,
      renameSession,
      deleteSession,
      messagesBySession,
      sendMessage,
      editingMessageId,
      setEditingMessageId,
      editMessage,
      resendMessage,
      cancelMessage,
      abortControllerRef,
    }),
    [
      isLoading,
      isSending,
      models,
      selectedModelId,
      useTavily,
      enableVSA,
      enableGLPI,
      enableZabbix,
      enableLinear,
      sessions,
      currentSessionId,
      messagesBySession,
      createSession,
      selectSession,
      renameSession,
      deleteSession,
      sendMessage,
      editingMessageId,
      editMessage,
      resendMessage,
      cancelMessage,
    ],
  );

  return <GenesisUIContext.Provider value={value}>{children}</GenesisUIContext.Provider>;
}

export function useGenesisUI() {
  const context = useContext(GenesisUIContext);
  if (!context) {
    throw new Error("useGenesisUI must be used within GenesisUIProvider");
  }
  return context;
}

