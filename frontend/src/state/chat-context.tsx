"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { storage } from "@/lib/storage";
import { logger } from "@/lib/logger";
import { translateApiError, formatErrorMessage } from "./error-utils";
import { useConfig } from "./config-context";
import { useSession } from "./session-context";
import { apiClient } from "@/lib/api-client";
import { useArtifacts } from "./artifact-context";
import { useArtifactDetection } from "@/hooks/useArtifactDetection";
import type { GenesisMessage, FileAttachment } from "./types";
import type { ArtifactStartData } from "./artifact-types";

interface ChatState {
  isLoading: boolean;
  isSending: boolean;
  messagesBySession: Record<string, GenesisMessage[]>;
  sendMessage: (content: string, useStreaming?: boolean, attachments?: FileAttachment[]) => Promise<void>;
  editingMessageId: string | null;
  setEditingMessageId: (id: string | null) => void;
  editMessage: (messageId: string, newContent: string, attachments?: FileAttachment[]) => void;
  resendMessage: (messageId: string) => Promise<void>;
  cancelMessage: () => void;
  clearSessionMessages: (sessionId: string) => void;
  abortControllerRef: React.MutableRefObject<AbortController | null>;
}

const ChatContext = createContext<ChatState | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const config = useConfig();
  const session = useSession();
  const artifactCtx = useArtifacts();
  const { detectArtifacts } = useArtifactDetection();

  const [isSending, setIsSending] = useState<boolean>(false);
  const [messagesBySession, setMessagesBySession] = useState<Record<string, GenesisMessage[]>>({});
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Use refs for values needed inside sendMessage to avoid stale closures
  const configRef = useRef(config);
  configRef.current = config;
  const sessionRef = useRef(session);
  sessionRef.current = session;
  const messagesBySessionRef = useRef(messagesBySession);
  messagesBySessionRef.current = messagesBySession;
  const artifactCtxRef = useRef(artifactCtx);
  artifactCtxRef.current = artifactCtx;
  const detectArtifactsRef = useRef(detectArtifacts);
  detectArtifactsRef.current = detectArtifacts;

  // Derive isLoading from session load state
  const isLoading = !session.sessionsLoaded;

  // Initialize messagesBySession for new sessions created by SessionProvider
  useEffect(() => {
    if (session.currentSessionId && messagesBySession[session.currentSessionId] === undefined) {
      // Auto-load messages for this session from API
      logger.debug(`[ChatContext] Auto-loading messages for session: ${session.currentSessionId}`);
      session.fetchSession(session.currentSessionId).then((result: any) => {
        if (result && result.messages) {
          if (result.merge) {
            setMessagesBySession((prev) => {
              const existing = prev[session.currentSessionId] || [];
              const existingMap = new Map(existing.map((msg: GenesisMessage) => [msg.id, msg]));
              result.messages.forEach((msg: GenesisMessage) => { existingMap.set(msg.id, msg); });
              return { ...prev, [session.currentSessionId]: Array.from(existingMap.values()) };
            });
          } else {
            setMessagesBySession((prev) => ({ ...prev, [session.currentSessionId]: result.messages }));
          }
        }
      }).catch(console.error);
    }
  }, [session.currentSessionId, session.fetchSession, messagesBySession]);

  const cancelMessage = useCallback(() => {
    if (abortControllerRef.current) {
      logger.debug("Cancelling message request...");
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsSending(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, useStreaming: boolean = true, attachments: FileAttachment[] = []) => {
      // Read fresh values from refs to avoid stale closures
      const { selectedModelId, useTavily, enableVSA, enableGLPI, enableZabbix, enableLinear, enablePlanning, selectedAgentId } = configRef.current;
      const { currentSessionId, sessions, createSession, setSessions } = sessionRef.current;

      let threadId = currentSessionId;
      if (!threadId) {
        const newThreadId = await createSession();
        threadId = newThreadId || sessionRef.current.currentSessionId || sessions[0]?.id || "";
      }
      if (!threadId) return;

      const previousMessagesCount = messagesBySessionRef.current[threadId]?.length ?? 0;

      const optimistic: GenesisMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: Date.now(),
        modelId: selectedModelId,
        usedTavily: useTavily,
        ...(attachments.length > 0 ? { attachments } : {}),
      };

      setMessagesBySession((prev) => {
        const existing = prev[threadId] ?? [];
        const updated = { ...prev, [threadId]: [...existing, optimistic] };
        storage.messages.save(threadId, updated[threadId]);
        return updated;
      });
      sessionRef.current.setCurrentSessionId(threadId);

      // Update lastActivityAt and auto-title
      setSessions((prev: any[]) => {
        return prev.map((s: any) => {
          if (s.id !== threadId) return s;

          const now = Date.now();
          let title = s.title;

          const isFirstMessage = previousMessagesCount === 0;
          const isDefaultTitle = title.startsWith("Sessão de ") || title.startsWith("Nova Sessão");

          if (isFirstMessage && isDefaultTitle) {
            const plain = content.replace(/\s+/g, " ").trim();
            const snippet = plain.slice(0, 60);
            if (snippet) {
              const autoTitle = snippet.charAt(0).toUpperCase() + snippet.slice(1);
              title = autoTitle;

              const storedSessions = storage.sessions.getAll();
              const updatedStored = storedSessions.map((ss) =>
                ss.id === s.id ? { ...ss, title: autoTitle } : ss,
              );
              storage.sessions.save(updatedStored);
            }
          }

          return { ...s, title, lastActivityAt: now };
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
          const controller = new AbortController();
          abortControllerRef.current = controller;

          const res = await apiClient.post(`/api/threads/${threadId}/messages/stream`, {
            content,
            model: selectedModelId,
            useTavily,
            thread_id: threadId,
            agent_id: selectedAgentId || undefined,
            enable_vsa: enableVSA,
            enable_glpi: enableGLPI,
            enable_zabbix: enableZabbix,
            enable_linear: enableLinear,
            enable_planning: enablePlanning,
            attachments: attachments.map((att) => ({
              file_id: att.id,
              name: att.name,
              mime: att.mime,
              size: att.size,
              url: att.url,
            })),
          }, {
            signal: controller.signal,
          });

          if (!res.ok) {
            let errorMessage = `Stream failed: ${res.status}`;
            let errorDetails: any = {};

            try {
              const errorData = await res.json();
              console.error("Stream error details:", errorData);
              errorDetails = errorData;

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
                errorMessage = JSON.stringify(errorData);
              }
            } catch (jsonError) {
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
          let thinkingReplaced = false;
          const collectedArtifactIds: string[] = [];

          const replaceThinkingWithAssistant = (assistantContent: string) => {
            setMessagesBySession((prev) => {
              const existing = prev[threadId] ?? [];
              const withoutThinking = existing.filter(msg => msg.id !== thinkingMessageId);
              const cleaned = withoutThinking.filter(msg => {
                if (msg.role === "user") return true;
                if (msg.role === "assistant" && (!msg.content || msg.content.trim() === "")) return false;
                return true;
              });
              const assistantMessage: GenesisMessage = {
                id: assistantMessageId,
                role: "assistant",
                content: assistantContent,
                timestamp: Date.now(),
                modelId: selectedModelId,
                usedTavily: useTavily,
                ...(collectedArtifactIds.length > 0 ? { artifactIds: [...collectedArtifactIds] } : {}),
              };
              const updated = [...cleaned, assistantMessage];
              storage.messages.save(threadId, updated);
              return { ...prev, [threadId]: updated };
            });
          };

          const updateAssistantContent = (newContent: string) => {
            setMessagesBySession((prev) => {
              const existing = prev[threadId] ?? [];
              const updated = existing.map((msg) => {
                if (msg.id === assistantMessageId && msg.role === "assistant") {
                  return { ...msg, content: newContent };
                }
                return msg;
              });
              storage.messages.save(threadId, updated);
              return { ...prev, [threadId]: updated };
            });
          };

          if (reader) {
            let streamActive = true;
            let totalBytesReceived = 0;
            let totalLinesProcessed = 0;
            try {
              logger.perf("[STREAM] Starting to read stream (thinking message stays until first content)...");
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

                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                totalLinesProcessed += lines.length;
                logger.perf("[STREAM] Received chunk:", value?.length || 0, "bytes. Buffer now has", buffer.length, "chars. Processing", lines.length, "lines");

                for (const line of lines) {
                  if (line.trim() === "") {
                    logger.perf("[STREAM] Skipping empty line");
                    continue;
                  }

                  logger.perf("[STREAM] Processing line:", line.substring(0, 100));

                  if (line.startsWith("data: ")) {
                    try {
                      const jsonStr = line.slice(6);
                      logger.perf("[STREAM] Parsing JSON:", jsonStr.substring(0, 200));
                      const data = JSON.parse(jsonStr);
                      logger.perf("[STREAM] Parsed data type:", data.type, "has content:", !!data.content, "content length:", data.content?.length || 0);

                      if (data.type === "start") {
                        continue;
                      }

                      // --- Artifact SSE events ---
                      if (data.type === "artifact_start" && data.artifact) {
                        const artData = data.artifact as ArtifactStartData;
                        artifactCtxRef.current.startArtifact(threadId, assistantMessageId, artData);
                        collectedArtifactIds.push(artData.artifact_id);
                        continue;
                      }
                      if (data.type === "artifact_content" && data.artifact_id && data.content) {
                        artifactCtxRef.current.appendArtifactContent(data.artifact_id, data.content);
                        continue;
                      }
                      if (data.type === "artifact_end" && data.artifact_id) {
                        artifactCtxRef.current.endArtifact(data.artifact_id);
                        continue;
                      }

                      if (data.type === "content" && data.content !== undefined && data.content !== null) {
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
                        const processedContent = rawContent.replace(/\\n/g, "\n").replace(/\\t/g, "\t");

                        // Track artifact_id from content events
                        if (data.artifact_id && !collectedArtifactIds.includes(data.artifact_id)) {
                          collectedArtifactIds.push(data.artifact_id);
                        }

                        if (data.final === true) {
                          logger.perf("[STREAM] Received final complete content, replacing accumulated content");
                          accumulatedContent = processedContent;
                        } else {
                          accumulatedContent += processedContent;
                        }
                        logger.perf("[STREAM] Content updated, total length:", accumulatedContent.length);

                        if (!thinkingReplaced) {
                          thinkingReplaced = true;
                          replaceThinkingWithAssistant(accumulatedContent);
                        } else {
                          updateAssistantContent(accumulatedContent);
                        }
                      } else if (data.type === "chunk" && data.data) {
                        logger.perf("[STREAM] Received chunk data, trying to extract content");
                        try {
                          const chunkStr = data.data;
                          if (chunkStr.includes("AIMessage") || chunkStr.includes("content=")) {
                            const contentMatch = chunkStr.match(/content=['"]([^'"]+)['"]/);
                            if (contentMatch && contentMatch[1]) {
                              const extractedContent = contentMatch[1];
                              if (extractedContent.length > accumulatedContent.length) {
                                accumulatedContent = extractedContent;
                                logger.perf("[STREAM] Extracted content from chunk:", accumulatedContent.length, "chars");
                                if (!thinkingReplaced) {
                                  thinkingReplaced = true;
                                  replaceThinkingWithAssistant(accumulatedContent);
                                } else {
                                  updateAssistantContent(accumulatedContent);
                                }
                              }
                            }
                          }
                        } catch (extractError) {
                          console.error("[STREAM] Error extracting content from chunk:", extractError);
                        }
                      } else if (data.type === "done") {
                        logger.perf("[STREAM] Stream done signal received");
                        logger.perf("[STREAM] Accumulated content length:", accumulatedContent.length);
                        streamActive = false;

                        if (data.total_length && data.total_length > accumulatedContent.length) {
                          console.warn(`[STREAM] WARNING: Expected ${data.total_length} chars but only have ${accumulatedContent.length} chars!`);
                        }

                        // Process remaining buffer
                        if (buffer.trim()) {
                          logger.perf("[STREAM] Processing remaining buffer:", buffer.substring(0, 100));
                          try {
                            if (buffer.startsWith("data: ")) {
                              const jsonStr = buffer.slice(6);
                              const bufferData = JSON.parse(jsonStr);
                              if (bufferData.type === "content" && bufferData.content) {
                                const processedContent = typeof bufferData.content === 'string'
                                  ? bufferData.content.replace(/\\n/g, '\n').replace(/\\t/g, '\t')
                                  : bufferData.content;
                                accumulatedContent += processedContent;
                              }
                            }
                          } catch (e) {
                            logger.perf("[STREAM] Could not parse remaining buffer as JSON:", e);
                          }
                        }

                        // Final save
                        if (accumulatedContent) {
                          logger.perf("[STREAM] Saving final content. Length:", accumulatedContent.length);

                          // LLM artifact detection (only if no rule-based artifacts already)
                          if (collectedArtifactIds.length === 0) {
                            const { artifacts: detected, cleanedContent } =
                              detectArtifactsRef.current(accumulatedContent, threadId, assistantMessageId);
                            if (detected.length > 0) {
                              logger.perf("[STREAM] Detected", detected.length, "LLM artifacts");
                              for (const art of detected) {
                                artifactCtxRef.current.addArtifact(art);
                                collectedArtifactIds.push(art.id);
                              }
                              accumulatedContent = cleanedContent;
                            }
                          }

                          if (!thinkingReplaced) {
                            thinkingReplaced = true;
                            replaceThinkingWithAssistant(accumulatedContent);
                          } else {
                            updateAssistantContent(accumulatedContent);
                          }
                        } else {
                          if (!thinkingReplaced) {
                            setMessagesBySession((prev) => ({
                              ...prev,
                              [threadId]: (prev[threadId] ?? []).filter((m) => m.id !== thinkingMessageId),
                            }));
                          } else {
                            setMessagesBySession((prev) => {
                              const existing = prev[threadId] ?? [];
                              const lastAssistant = existing.find((msg) => msg.id === assistantMessageId);
                              if (lastAssistant && !lastAssistant.content) {
                                return { ...prev, [threadId]: existing.filter((msg) => msg.id !== assistantMessageId) };
                              }
                              return prev;
                            });
                          }
                        }
                      } else if (data.type === "error") {
                        console.error("[STREAM] Error from stream:", data.error);
                        const translated = translateApiError(data.error || "Erro desconhecido");
                        const formattedError = formatErrorMessage(translated);
                        throw new Error(formattedError);
                      } else if (data.type === "chunk") {
                        logger.perf("[STREAM] Chunk received:", data.data?.substring(0, 100));
                      }
                    } catch (e) {
                      console.error("[STREAM] Error parsing line:", line, e);
                    }
                  } else if (line.trim() !== "") {
                    logger.perf("[STREAM] Non-data line:", line.substring(0, 100));
                  }
                }
              }

              // Process any remaining buffer
              if (buffer.trim() && accumulatedContent) {
                logger.perf("[STREAM] Processing final buffer before saving. Buffer length:", buffer.length);
                try {
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
                if (!thinkingReplaced) {
                  replaceThinkingWithAssistant(accumulatedContent);
                } else {
                  updateAssistantContent(accumulatedContent);
                }
              } else if (streamActive && !accumulatedContent) {
                console.warn("[STREAM] Stream ended but no content was accumulated!");
                if (!thinkingReplaced) {
                  setMessagesBySession((prev) => ({
                    ...prev,
                    [threadId]: (prev[threadId] ?? []).filter((m) => m.id !== thinkingMessageId),
                  }));
                } else {
                  setMessagesBySession((prev) => {
                    const existing = prev[threadId] ?? [];
                    return { ...prev, [threadId]: existing.filter((msg) => msg.id !== assistantMessageId) };
                  });
                }
              }

              // Final check: ensure content is saved
              logger.perf("[STREAM] Stream loop ended. Final accumulatedContent length:", accumulatedContent.length);
              if (accumulatedContent) {
                logger.perf("[STREAM] Final check - ensuring content is saved. Length:", accumulatedContent.length);
                if (!thinkingReplaced) {
                  replaceThinkingWithAssistant(accumulatedContent);
                } else {
                  setMessagesBySession((prev) => {
                    const existing = prev[threadId] ?? [];
                    const assistantMsg = existing.find((msg) => msg.id === assistantMessageId);
                    const artIds = collectedArtifactIds.length > 0 ? [...collectedArtifactIds] : undefined;
                    if (!assistantMsg || assistantMsg.content !== accumulatedContent) {
                      const updated = existing.map((msg) =>
                        msg.id === assistantMessageId && msg.role === "assistant"
                          ? { ...msg, content: accumulatedContent, ...(artIds ? { artifactIds: artIds } : {}) }
                          : msg
                      );
                      if (!assistantMsg) {
                        updated.push({
                          id: assistantMessageId,
                          role: "assistant",
                          content: accumulatedContent,
                          timestamp: Date.now(),
                          modelId: selectedModelId,
                          usedTavily: useTavily,
                          ...(artIds ? { artifactIds: artIds } : {}),
                        });
                      }
                      storage.messages.save(threadId, updated);
                      return { ...prev, [threadId]: updated };
                    }
                    return prev;
                  });
                }
              } else if (!thinkingReplaced) {
                setMessagesBySession((prev) => ({
                  ...prev,
                  [threadId]: (prev[threadId] ?? []).filter((m) => m.id !== thinkingMessageId),
                }));
              } else {
                console.warn("[STREAM] WARNING: Stream completed but accumulatedContent is empty!");
              }
            } catch (streamError) {
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

          const res = await apiClient.post(`/api/threads/${threadId}/messages`, {
            content,
            model: selectedModelId,
            useTavily,
            agent_id: selectedAgentId || undefined,
            enable_vsa: enableVSA,
            enable_glpi: enableGLPI,
            enable_zabbix: enableZabbix,
            enable_linear: enableLinear,
            enable_planning: enablePlanning,
            attachments: attachments.map((att) => ({
              file_id: att.id,
              name: att.name,
              mime: att.mime,
              size: att.size,
              url: att.url,
            })),
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

          // Fetch updated session messages
          const result = await session.fetchSession(threadId);
          if (result && result.messages) {
            setMessagesBySession((prev) => ({ ...prev, [threadId]: result.messages }));
          }
        }
      } catch (error) {
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
        setMessagesBySession((prev) => {
          const existing = prev[threadId] ?? [];
          const filtered = existing.filter((msg) => msg.id !== thinkingMessageId);
          const cleaned = filtered.filter(
            (msg) => !(msg.role === "assistant" && msg.content === "")
          );
          return { ...prev, [threadId]: cleaned };
        });

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
    // sendMessage reads from refs, so no stale closure issue.
    // We only depend on session.fetchSession for the non-streaming fallback path.
    [session.fetchSession],
  );

  const editMessage = useCallback((messageId: string, newContent: string, attachments?: FileAttachment[]) => {
    setMessagesBySession((prev) => {
      const updated = { ...prev };
      for (const sessionId in updated) {
        const messages = updated[sessionId];
        const index = messages.findIndex((msg) => msg.id === messageId);
        if (index !== -1) {
          updated[sessionId] = messages.map((msg, i) =>
            i === index
              ? {
                ...msg,
                content: newContent,
                editedAt: Date.now(),
                ...(attachments ? { attachments } : {}),
              }
              : msg
          );
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
      const threadId = sessionRef.current.currentSessionId;
      if (!threadId) return;

      const messages = messagesBySessionRef.current[threadId] || [];
      const messageIndex = messages.findIndex((msg) => msg.id === messageId);
      if (messageIndex === -1) return;

      const message = messages[messageIndex];
      if (message.role !== "user") return;

      const messagesToKeep = messages.slice(0, messageIndex + 1);
      setMessagesBySession((prev) => ({
        ...prev,
        [threadId]: messagesToKeep,
      }));
      storage.messages.save(threadId, messagesToKeep);

      await sendMessage(message.content, true, message.attachments || []);
    },
    [sendMessage]
  );

  const clearSessionMessages = useCallback((sessionId: string) => {
    setMessagesBySession((prev) => {
      const next = { ...prev };
      delete next[sessionId];
      return next;
    });
  }, []);

  const value = useMemo<ChatState>(
    () => ({
      isLoading,
      isSending,
      messagesBySession,
      sendMessage,
      editingMessageId,
      setEditingMessageId,
      editMessage,
      resendMessage,
      cancelMessage,
      clearSessionMessages,
      abortControllerRef,
    }),
    [
      isLoading,
      isSending,
      messagesBySession,
      sendMessage,
      editingMessageId,
      editMessage,
      resendMessage,
      cancelMessage,
      clearSessionMessages,
    ],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within ChatProvider");
  }
  return context;
}
