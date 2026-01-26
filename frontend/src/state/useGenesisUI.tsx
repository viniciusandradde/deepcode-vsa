"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { storage } from "@/lib/storage";

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
}

export interface ModelOption {
  id: string;
  label: string;
  inputCost: number;
  outputCost: number;
}

interface GenesisUIState {
  isLoading: boolean;
  isSending: boolean;
  models: ModelOption[];
  selectedModelId: string;
  setSelectedModelId: (id: string) => void;
  useTavily: boolean;
  setUseTavily: (value: boolean) => void;
  sessions: GenesisSession[];
  currentSessionId: string;
  createSession: () => Promise<string | undefined>;
  selectSession: (id: string) => Promise<void>;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => Promise<void>;
  messagesBySession: Record<string, GenesisMessage[]>;
  sendMessage: (content: string) => Promise<void>;
  editingMessageId: string | null;
  setEditingMessageId: (id: string | null) => void;
  editMessage: (messageId: string, newContent: string) => void;
  resendMessage: (messageId: string) => Promise<void>;
}

const GenesisUIContext = createContext<GenesisUIState | null>(null);

export function GenesisUIProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [useTavily, setUseTavily] = useState<boolean>(false);
  const [sessions, setSessions] = useState<GenesisSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messagesBySession, setMessagesBySession] = useState<Record<string, GenesisMessage[]>>({});
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);

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
      }));
      setModels(mapped);
      if (!selectedModelId && mapped[0]) {
        setSelectedModelId(mapped[0].id);
      }
    } catch (error) {
      console.error("Error loading models:", error);
    }
  }

  async function loadSessions() {
    try {
      // Load from localStorage first
      const storedSessions = storage.sessions.getAll();
      if (storedSessions.length > 0) {
        const nextSessions: GenesisSession[] = storedSessions.map((s) => ({
          id: s.id,
          title: s.title,
          createdAt: s.createdAt,
        }));
        setSessions(nextSessions);

        // Load messages from localStorage
        const nextMessages: Record<string, GenesisMessage[]> = {};
        for (const session of nextSessions) {
          const storedMessages = storage.messages.get(session.id);
          nextMessages[session.id] = storedMessages.map((msg) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
            modelId: msg.modelId,
            usedTavily: msg.usedTavily,
          }));
        }
        setMessagesBySession(nextMessages);

        if (!currentSessionId && nextSessions[0]) {
          setCurrentSessionId(nextSessions[0].id);
        }
      }

      // Also try to load from API
      const res = await fetch("/api/threads", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        const threads = Array.isArray(data.threads) ? data.threads : [];
        
        const apiSessions: GenesisSession[] = threads.map((thread: any) => ({
          id: thread.thread_id || thread.id,
          title: thread.title || `Sessão ${thread.thread_id?.slice(0, 8) || thread.id?.slice(0, 8)}`,
          createdAt: thread.created_at ? Date.parse(thread.created_at) : Date.now(),
        }));
        
        // Merge with stored sessions
        const allSessions = [...apiSessions, ...storedSessions.filter(s => 
          !apiSessions.find(api => api.id === s.id)
        )];
        setSessions(allSessions);
        
        // Save to localStorage
        storage.sessions.save(allSessions.map(s => ({
          id: s.id,
          title: s.title,
          createdAt: s.createdAt,
          lastAccessed: Date.now(),
          messageCount: 0,
        })));
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
      const storedSessions = storage.sessions.getAll();
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
          messages.forEach(msg => {
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

  const sendMessage = useCallback(
    async (content: string, useStreaming: boolean = true) => {
      let threadId = currentSessionId;
      if (!threadId) {
        const newThreadId = await createSession();
        threadId = newThreadId || currentSessionId || sessions[0]?.id || "";
      }
      if (!threadId) return;

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
          const res = await fetch(`/api/threads/${threadId}/messages/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content, model: selectedModelId, useTavily, thread_id: threadId }),
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
            console.log("[STREAM] Before removing thinking, messages count:", existing.length);
            console.log("[STREAM] Messages:", existing.map(m => ({ id: m.id, role: m.role, content: m.content.substring(0, 50) })));
            
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
            console.log("[STREAM] After adding assistant message, messages count:", updated.length);
            console.log("[STREAM] Updated messages:", updated.map(m => ({ id: m.id, role: m.role, content: m.content.substring(0, 50) || "(vazio)" })));
            
            return { ...prev, [threadId]: updated };
          });

          if (reader) {
            let streamActive = true;
            let totalBytesReceived = 0;
            let totalLinesProcessed = 0;
            try {
              console.log("[STREAM] Starting to read stream...");
            while (true) {
              const { done, value } = await reader.read();
                if (done) {
                  console.log("[STREAM] Stream completed. Total bytes:", totalBytesReceived, "Total lines:", totalLinesProcessed, "Final buffer:", buffer.length);
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
                console.log("[STREAM] Received chunk:", value?.length || 0, "bytes. Buffer now has", buffer.length, "chars. Processing", lines.length, "lines");

              for (const line of lines) {
                  if (line.trim() === "") {
                    console.log("[STREAM] Skipping empty line");
                    continue; // Skip empty lines
                  }
                  
                  console.log("[STREAM] Processing line:", line.substring(0, 100));
                  
                  // Try to parse as SSE data
                if (line.startsWith("data: ")) {
                  try {
                      const jsonStr = line.slice(6);
                      console.log("[STREAM] Parsing JSON:", jsonStr.substring(0, 200));
                      const data = JSON.parse(jsonStr);
                      console.log("[STREAM] Parsed data type:", data.type, "has content:", !!data.content, "content length:", data.content?.length || 0);
                      
                    if (data.type === "content" && data.content) {
                        // Handle escaped newlines - convert \n to actual newlines
                        const processedContent = typeof data.content === 'string' 
                          ? data.content.replace(/\\n/g, '\n').replace(/\\t/g, '\t')
                          : data.content;
                        
                        // If this is a final content update (complete content), replace instead of append
                        if (data.final === true) {
                          console.log("[STREAM] Received final complete content, replacing accumulated content");
                          console.log("[STREAM] Final content length:", processedContent.length);
                          console.log("[STREAM] Previous accumulated length:", accumulatedContent.length);
                          accumulatedContent = processedContent;
                          console.log("[STREAM] After replacement, accumulated length:", accumulatedContent.length);
                        } else {
                          accumulatedContent += processedContent;
                        }
                        console.log("[STREAM] Content updated, total length:", accumulatedContent.length, "new chunk:", processedContent.length, "is final:", data.final || false);
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
                        console.log("[STREAM] Received chunk data, trying to extract content");
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
                                console.log("[STREAM] Extracted content from chunk:", newContent.length, "chars");
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
                        console.log("[STREAM] Stream done signal received");
                        console.log("[STREAM] Final content length from done message:", data.total_length || "not provided");
                        console.log("[STREAM] Accumulated content length:", accumulatedContent.length);
                        streamActive = false;
                        
                        // Check if we received the expected total length
                        if (data.total_length && data.total_length > accumulatedContent.length) {
                          console.warn(`[STREAM] WARNING: Expected ${data.total_length} chars but only have ${accumulatedContent.length} chars!`);
                          console.warn("[STREAM] Content may be incomplete. Check if final content message was received.");
                        }
                        
                        // Process any remaining content in buffer before final save
                        if (buffer.trim()) {
                          console.log("[STREAM] Processing remaining buffer:", buffer.substring(0, 100));
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
                                console.log("[STREAM] Added buffer content, new total length:", accumulatedContent.length);
                              }
                            }
                          } catch (e) {
                            console.log("[STREAM] Could not parse remaining buffer as JSON:", e);
                          }
                        }
                        
                        // Ensure final content is saved
                        if (accumulatedContent) {
                          console.log("[STREAM] Saving final content. Length:", accumulatedContent.length);
                          console.log("[STREAM] Final content preview (first 200):", accumulatedContent.substring(0, 200));
                          console.log("[STREAM] Final content preview (last 200):", accumulatedContent.substring(Math.max(0, accumulatedContent.length - 200)));
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
                            console.log("[STREAM] Messages after saving content:", updated.length);
                            console.log("[STREAM] Saved message content length:", savedMsg?.content?.length || 0);
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
                      throw new Error(data.error);
                      } else if (data.type === "chunk") {
                        // Log chunk data for debugging
                        console.log("[STREAM] Chunk received:", data.data?.substring(0, 100));
                      }
                    } catch (e) {
                      console.error("[STREAM] Error parsing line:", line, e);
                      // Don't throw, continue processing
                    }
                  } else if (line.trim() !== "") {
                    // Log non-data lines for debugging
                    console.log("[STREAM] Non-data line:", line.substring(0, 100));
                  }
                }
              }
              
              // If stream ended without "done" message, ensure content is saved
              // Also process any remaining buffer
              if (buffer.trim() && accumulatedContent) {
                console.log("[STREAM] Processing final buffer before saving. Buffer length:", buffer.length);
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
                          console.log("[STREAM] Added final buffer content, new total:", accumulatedContent.length);
                    }
                  } catch (e) {
                        console.log("[STREAM] Could not parse final buffer line:", e);
                      }
                    }
                  }
                } catch (e) {
                  console.log("[STREAM] Error processing final buffer:", e);
                }
              }
              
              if (streamActive && accumulatedContent) {
                console.log("[STREAM] Stream ended without done message, saving content. Length:", accumulatedContent.length);
                console.log("[STREAM] Final content preview:", accumulatedContent.substring(0, 200));
                console.log("[STREAM] Final content end preview:", accumulatedContent.substring(Math.max(0, accumulatedContent.length - 200)));
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
                  console.log("[STREAM] Final message content length:", updated.find(m => m.id === assistantMessageId)?.content?.length || 0);
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
              console.log("[STREAM] Stream loop ended. Final accumulatedContent length:", accumulatedContent.length);
              if (accumulatedContent) {
                console.log("[STREAM] Final check - ensuring content is saved. Length:", accumulatedContent.length);
                console.log("[STREAM] Final content preview (first 300):", accumulatedContent.substring(0, 300));
                console.log("[STREAM] Final content preview (last 300):", accumulatedContent.substring(Math.max(0, accumulatedContent.length - 300)));
                setMessagesBySession((prev) => {
                  const existing = prev[threadId] ?? [];
                  const assistantMsg = existing.find(msg => msg.id === assistantMessageId);
                  console.log("[STREAM] Current assistant message content length:", assistantMsg?.content?.length || 0);
                  if (!assistantMsg || assistantMsg.content !== accumulatedContent) {
                    console.log("[STREAM] Content mismatch or missing! Updating...");
                    console.log("[STREAM] Expected length:", accumulatedContent.length, "Current length:", assistantMsg?.content?.length || 0);
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
                      console.log("[STREAM] Assistant message not found, creating new one");
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
                    console.log("[STREAM] Final message after update - length:", finalMsg?.content?.length || 0);
                    storage.messages.save(threadId, updated);
                    console.log("[STREAM] Saved to localStorage. Final message count:", updated.length);
                    return { ...prev, [threadId]: updated };
                  }
                  console.log("[STREAM] Content already matches, no update needed");
                  return prev;
                });
              } else {
                console.warn("[STREAM] WARNING: Stream completed but accumulatedContent is empty!");
              }
            } catch (streamError) {
              console.error("[STREAM] Error reading stream:", streamError);
              // Don't remove user message on stream error
              throw streamError;
            }
          } else {
            console.error("[STREAM] No reader available");
            throw new Error("Stream reader not available");
          }
        } else {
          // Non-streaming mode (fallback)
          const res = await fetch(`/api/threads/${threadId}/messages`, {
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
        console.error("Error sending message:", error);
        // Remove only thinking message, preserve user message
        setMessagesBySession((prev) => {
          const existing = prev[threadId] ?? [];
          // Filter out thinking message but keep user message
          const filtered = existing.filter(msg => msg.id !== thinkingMessageId);
          // Also remove empty assistant message if it exists
          const cleaned = filtered.filter(msg => 
            !(msg.role === "assistant" && msg.content === "")
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
        const errorMessage: GenesisMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `❌ **Erro ao enviar mensagem**\n\n${errorMsg}${errorDetails}\n\n**Possíveis causas:**\n- API keys não configuradas (OPENROUTER_API_KEY, OPENAI_API_KEY)\n- Backend não está acessível\n- Problema de conexão\n\nVerifique os logs do backend para mais detalhes.`,
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
    }),
    [
      isLoading,
      isSending,
      models,
      selectedModelId,
      useTavily,
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

