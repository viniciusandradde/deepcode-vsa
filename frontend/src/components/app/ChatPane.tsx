"use client";

import { FormEvent, useMemo, useState, useEffect, useRef } from "react";
import clsx from "clsx";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessageActions } from "./MessageActions";
import { Logo } from "./Logo";
import { AudioRecorderButton } from "./AudioRecorderButton";

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
  } = useGenesisUI();
  const messages = useMemo(() => messagesBySession[currentSessionId] ?? [], [messagesBySession, currentSessionId]);
  const [draft, setDraft] = useState("");
  const [useStreaming, setUseStreaming] = useState(true);
  const [editingContent, setEditingContent] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLElement>(null);
  const [userHasScrolled, setUserHasScrolled] = useState(false);
  const lastMessageCountRef = useRef(0);

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || isLoading || isSending) return;

    setDraft("");
    setUserHasScrolled(false);

    try {
      await sendMessage(trimmed, useStreaming);
    } catch (error) {
      setDraft(trimmed);
      console.error("Erro ao enviar mensagem:", error);
    }
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      // Ignore if user is typing in an input/textarea
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
        // Allow Escape to cancel editing
        if (event.key === "Escape" && editingMessageId) {
          setEditingMessageId(null);
          setEditingContent("");
        }
        // Allow Ctrl/Cmd+Enter to submit
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.preventDefault();
          handleSubmit();
        }
        return;
      }

      // Global shortcuts
      if (event.key === "e" || event.key === "E") {
        // E to edit last user message
        if (!editingMessageId && messages.length > 0) {
          const lastUserMessage = [...messages].reverse().find((msg) => msg.role === "user");
          if (lastUserMessage) {
            setEditingMessageId(lastUserMessage.id);
            setEditingContent(lastUserMessage.content);
          }
        }
      } else if (event.key === "Escape") {
        // Escape to cancel editing
        if (editingMessageId) {
          setEditingMessageId(null);
          setEditingContent("");
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [draft, isLoading, isSending, useStreaming, editingMessageId, messages, setEditingMessageId]);

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
          <span className="rounded-md border border-vsa-blue/40 px-3 py-1 text-vsa-blue-light bg-vsa-blue/5">
            Modelo: <span className="font-semibold text-white">{selectedModelId || "—"}</span>
          </span>
          <span className="rounded-md border border-vsa-orange/40 px-3 py-1 text-vsa-orange-light bg-vsa-orange/5">
            Busca Web: <span className={useTavily ? "text-vsa-orange-light" : "text-slate-400"}>{useTavily ? "Ativa" : "Inativa"}</span>
          </span>
          <span className="rounded-md border border-vsa-blue/40 px-3 py-1 text-vsa-blue-light bg-vsa-blue/5">
            Streaming: <span className={useStreaming ? "text-vsa-blue-light" : "text-slate-400"}>{useStreaming ? "Ativo" : "Inativo"}</span>
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
            <Card className="border border-dashed border-white/15 bg-transparent text-center text-slate-400">
              <CardContent>Envie uma mensagem para iniciar a conversa.</CardContent>
            </Card>
          ) : (
            messages.map((message) => {
              const isAssistant = message.role === "assistant";
              const isThinking = message.content === "Pensando...";
              const isError = message.content.startsWith("Erro:");
              const isEditing = editingMessageId === message.id;
              const isUserMessage = message.role === "user";

              // Não renderizar mensagens do assistente vazias (sem conteúdo)
              // Isso evita mostrar mensagens vazias enquanto o stream está carregando
              if (isAssistant && !isThinking && !message.content.trim() && !isError) {
                return null;
              }

              return (
                <article
                  key={message.id}
                  className={clsx(
                    "group relative max-w-2xl rounded-2xl border px-5 py-4 text-sm leading-relaxed shadow-lg transition-all animate-in fade-in slide-in-from-bottom-2 duration-300",
                    isError
                      ? "border-red-500/40 bg-red-500/10 text-red-100"
                      : isAssistant
                        ? "border-white/10 bg-white/10 text-slate-100"
                        : "ml-auto border-vsa-orange/40 bg-vsa-orange/10 text-vsa-orange-light",
                    isEditing && "ring-2 ring-vsa-blue/50",
                  )}
                >
                  {isUserMessage && !isEditing && (
                    <MessageActions
                      message={message}
                      onEdit={() => {
                        setEditingMessageId(message.id);
                        setEditingContent(message.content);
                      }}
                      onResend={() => resendMessage(message.id)}
                    />
                  )}
                  <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.35em] text-slate-400">
                    <span>
                      {message.role === "assistant" ? "Agente" : "Você"}
                      {message.editedAt && (
                        <span className="ml-2 text-[9px] italic text-slate-500">(editado)</span>
                      )}
                    </span>
                    <span className="text-slate-500">{new Date(message.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {isEditing ? (
                    <div className="space-y-2">
                      <textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        className="w-full resize-none rounded-lg border border-vsa-blue/40 bg-[#0b1526]/90 px-3 py-2 text-sm text-white focus:border-vsa-blue focus:outline-none"
                        rows={3}
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === "Escape") {
                            setEditingMessageId(null);
                            setEditingContent("");
                          } else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                            e.preventDefault();
                            if (editingContent.trim()) {
                              editMessage(message.id, editingContent.trim());
                              setEditingMessageId(null);
                              setEditingContent("");
                            }
                          }
                        }}
                      />
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingMessageId(null);
                            setEditingContent("");
                          }}
                          className="border-slate-400/40 text-slate-300"
                        >
                          Cancelar
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => {
                            if (editingContent.trim()) {
                              editMessage(message.id, editingContent.trim());
                              setEditingMessageId(null);
                              setEditingContent("");
                            }
                          }}
                          disabled={!editingContent.trim()}
                          className="bg-vsa-orange/20 text-vsa-orange-light hover:bg-vsa-orange/30"
                        >
                          Salvar
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={async () => {
                            if (editingContent.trim()) {
                              editMessage(message.id, editingContent.trim());
                              setEditingMessageId(null);
                              setEditingContent("");
                              await resendMessage(message.id);
                            }
                          }}
                          disabled={!editingContent.trim() || isSending}
                          className="bg-emerald-500/20 text-emerald-100 hover:bg-emerald-500/30"
                        >
                          Salvar e Reenviar
                        </Button>
                      </div>
                    </div>
                  ) : isAssistant ? (
                    isThinking ? (
                      <div className="flex items-center gap-3 italic text-slate-300">
                        <div className="flex gap-1">
                          <div className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse" style={{ animationDelay: "0ms" }} />
                          <div className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse" style={{ animationDelay: "150ms" }} />
                          <div className="h-2 w-2 rounded-full bg-vsa-orange animate-pulse" style={{ animationDelay: "300ms" }} />
                        </div>
                        <span className="animate-pulse">Analisando sua mensagem...</span>
                      </div>
                    ) : (
                      <div className="markdown-body">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[]}
                          components={{
                            p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
                            br: () => <br />,
                            a: ({ ...props }) => (
                              <a
                                {...props}
                                className="font-semibold text-vsa-blue-light underline decoration-vsa-blue/60 underline-offset-4 hover:text-vsa-blue-lighter"
                                target="_blank"
                                rel="noreferrer"
                              />
                            ),
                            code: ({ node, className, children, ...props }) => {
                              const isInline = !className?.includes('language-');
                              return isInline ? (
                                <code
                                  className={clsx(
                                    "rounded bg-white/10 px-1.5 py-0.5 text-[13px] text-slate-100",
                                    className,
                                  )}
                                  {...props}
                                >
                                  {children}
                                </code>
                              ) : (
                                <pre
                                  className="overflow-x-auto rounded-lg border border-white/10 bg-[#0b1526] p-4 text-[13px] text-slate-100"
                                >
                                  <code className={className} {...props}>{children}</code>
                                </pre>
                              );
                            },
                            li: ({ ...props }) => <li className="pl-1" {...props} />,
                            h1: ({ ...props }) => <h1 className="mb-4 text-2xl font-bold" {...props} />,
                            h2: ({ ...props }) => <h2 className="mb-3 mt-4 text-xl font-semibold" {...props} />,
                            h3: ({ ...props }) => <h3 className="mb-2 mt-3 text-lg font-semibold" {...props} />,
                            ul: ({ ...props }) => <ul className="mb-4 ml-6 list-disc space-y-1" {...props} />,
                            ol: ({ ...props }) => <ol className="mb-4 ml-6 list-decimal space-y-1" {...props} />,
                            blockquote: ({ ...props }) => <blockquote className="mb-4 border-l-4 border-vsa-orange/40 pl-4 italic" {...props} />,
                            img: ({ src, alt, ...props }) => {
                              if (!src) return null;
                              return <img src={src} alt={alt || ""} className="max-w-full rounded-lg my-4" {...props} />;
                            }
                          }}
                        >
                          {message.content.replace(/\\n/g, '\n').replace(/\\t/g, '\t')}
                        </ReactMarkdown>
                      </div>
                    )
                  ) : (
                    <p className="whitespace-pre-wrap text-[15px] text-slate-100" style={{ fontFamily: "var(--font-sans)" }}>
                      {message.content}
                    </p>
                  )}
                  <div className="mt-3 flex flex-wrap gap-3 text-[10px] uppercase tracking-[0.35em] text-slate-400">
                    {message.modelId ? <span>Modelo: {message.modelId}</span> : null}
                    {message.usedTavily ? <span>Busca Web Ativada</span> : null}
                  </div>
                </article>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="border-t border-white/10 px-10 py-5">
        <form onSubmit={handleSubmit} className="flex w-full items-start gap-4">
          <div className="flex-1">
            <label htmlFor="message-input" className="mb-2 block text-[11px] uppercase tracking-[0.35em] text-slate-400">
              Entrada de Comando
            </label>
            <div className="flex items-start gap-2">
              <textarea
                id="message-input"
                ref={textareaRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={isLoading ? "Carregando..." : "Digite sua mensagem ou use o microfone..."}
                className="h-[90px] w-full resize-none rounded-xl border border-white/10 bg-[#0b1526]/90 px-4 py-3 text-sm text-white shadow-[0_0_25px_rgba(62,130,246,0.35)] focus:border-vsa-blue focus:outline-none focus:ring-2 focus:ring-vsa-blue/50"
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    handleSubmit();
                  }
                }}
                disabled={isLoading || isSending}
                aria-label="Campo de entrada de mensagem"
                aria-describedby="message-hint"
              />
              <div className="flex items-start pt-2">
                <AudioRecorderButton
                  onTranscript={(transcript) => {
                    if (transcript) {
                      setDraft((prev) => {
                        // Verificar se o transcript já está no texto para evitar duplicação
                        const prevText = prev.trim();
                        if (prevText && transcript.startsWith(prevText)) {
                          // O transcript contém o texto anterior + novo texto
                          // Retornar apenas o transcript completo (já inclui o anterior)
                          return transcript;
                        } else if (prevText) {
                          // Adicionar o novo texto ao existente
                          return `${prevText} ${transcript}`;
                        } else {
                          // Primeiro texto
                          return transcript;
                        }
                      });
                      // Focar no textarea após atualizar
                      setTimeout(() => {
                        textareaRef.current?.focus();
                        // Mover cursor para o final
                        if (textareaRef.current) {
                          const length = textareaRef.current.value.length;
                          textareaRef.current.setSelectionRange(length, length);
                        }
                      }, 0);
                    }
                  }}
                  onError={(error) => {
                    console.error("Erro de gravação:", error);
                    // Opcional: mostrar toast ou mensagem de erro
                  }}
                  silenceTimeout={3000}
                />
              </div>
            </div>
            <p id="message-hint" className="sr-only">
              Pressione Ctrl+Enter ou Cmd+Enter para enviar, ou use o botão de microfone para gravar áudio
            </p>
          </div>
          <div className="flex items-end pt-[30px]">
            <Button
              type="submit"
              disabled={isLoading || isSending || !draft.trim()}
              className="h-[80px] rounded-lg border border-vsa-orange/40 bg-vsa-orange/20 px-6 text-sm uppercase tracking-[0.35em] text-vsa-orange-light transition hover:border-vsa-orange hover:bg-vsa-orange/30 focus:outline-none focus:ring-2 focus:ring-vsa-orange/50"
              aria-label={isSending ? "Enviando mensagem" : "Enviar mensagem"}
            >
              {isSending ? "Enviando..." : "Enviar"}
            </Button>
          </div>
        </form>
        <div className="mt-3 text-[11px] uppercase tracking-[0.3em] text-slate-500">
          Sessão atual: <span className="text-slate-300">{currentSessionId || "—"}</span>
        </div>
      </footer>
    </div>
  );
}
