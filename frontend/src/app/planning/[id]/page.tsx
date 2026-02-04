"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThinkingIndicator } from "@/components/app/ThinkingIndicator";
// Using relative URLs - Next.js rewrites proxy to backend

interface Document {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  content_preview: string | null;
  uploaded_at: string;
}

interface Stage {
  id: string;
  title: string;
  description: string | null;
  order_index: number;
  status: string;
  estimated_days: number | null;
  start_date: string | null;
  end_date: string | null;
}

interface BudgetItem {
  id: string;
  category: string;
  description: string | null;
  estimated_cost: number;
  actual_cost: number;
  currency: string;
}

interface Project {
  id: string;
  title: string;
  description: string | null;
  status: string;
  embedding_model: string;
  linear_project_id: string | null;
  linear_project_url: string | null;
  stages: Stage[];
  documents: Document[];
  budget_items: BudgetItem[];
  total_budget_estimated: number;
  total_budget_actual: number;
}

interface RagModel {
  id: string;
  name: string;
  dims: number;
}

interface ChatMessage {
  id?: string | null;
  role: "user" | "assistant";
  content: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [ragModels, setRagModels] = useState<RagModel[]>([]);
  const [embeddingModel, setEmbeddingModel] = useState("openai");
  const [savingEmbedding, setSavingEmbedding] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [chatCollapsed, setChatCollapsed] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [copyStatus, setCopyStatus] = useState("Copiar (Word/Docs)");
  const [selectedChatIndex, setSelectedChatIndex] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatAbortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const uniqueRagModels = Array.from(
    new Map(ragModels.map((model) => [model.id, model])).values()
  );

  const fetchProject = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/planning/projects/${projectId}`);
      if (!res.ok) throw new Error("Erro ao carregar projeto");
      const data: Project = await res.json();
      setProject(data);
      setEmbeddingModel(data.embedding_model || "openai");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch(`/api/v1/config/rag-models`);
        if (!res.ok) throw new Error("Erro ao carregar modelos RAG");
        const data: RagModel[] = await res.json();
        if (data && data.length > 0) {
          setRagModels(data);
          return;
        }
      } catch (e) {
        if (process.env.NODE_ENV === "development") {
          console.error("[Planning] RAG models error:", e);
        }
      }
      setRagModels([
        { id: "openai", name: "OpenAI Cloud (Rápido)", dims: 1536 },
      ]);
    };
    fetchModels();
  }, []);

  useEffect(() => {
    if (!project) return;
    if (ragModels.some((m) => m.id === project.embedding_model)) return;
    if (!project.embedding_model) return;
    setRagModels((prev) => [
      ...prev,
      { id: project.embedding_model, name: `${project.embedding_model} (Indisponível)`, dims: 0 },
    ]);
  }, [project, ragModels]);

  useEffect(() => {
    const fetchThread = async () => {
      try {
        const threadId = `planning:${projectId}`;
        const res = await fetch(`/api/v1/threads/${encodeURIComponent(threadId)}`);
        if (!res.ok) throw new Error("Erro ao carregar histórico do chat");
        const data = await res.json();
        if (Array.isArray(data.messages)) {
          setChatMessages(
            data.messages
              .filter((msg: ChatMessage) => msg && msg.content)
              .map((msg: ChatMessage) => ({
                id: msg.id ?? null,
                role: msg.role,
                content: msg.content,
              }))
          );
        }
      } catch (e) {
        if (process.env.NODE_ENV === "development") {
          console.error("[Planning] Chat history error:", e);
        }
      }
    };
    fetchThread();
  }, [projectId]);

  useEffect(() => {
    if (chatCollapsed) return;
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chatMessages, chatCollapsed]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append("file", file);
        
        const res = await fetch(`/api/v1/planning/projects/${projectId}/documents`, {
          method: "POST",
          body: formData,
        });
        
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Erro no upload");
        }
      }
      fetchProject();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro no upload");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("Excluir este documento?")) return;
    
    try {
      const res = await fetch(`/api/v1/planning/projects/${projectId}/documents/${docId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Erro ao excluir");
      fetchProject();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao excluir");
    }
  };

  const handleSaveEmbeddingModel = async () => {
    if (!project) return;
    if (embeddingModel === project.embedding_model) return;
    try {
      setSavingEmbedding(true);
      const res = await fetch(`/api/v1/planning/projects/${projectId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embedding_model: embeddingModel }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erro ao atualizar modelo");
      }
      const updated: Project = await res.json();
      setProject(updated);
      setEmbeddingModel(updated.embedding_model || embeddingModel);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao atualizar modelo");
    } finally {
      setSavingEmbedding(false);
    }
  };

  const handleClearChat = async () => {
    try {
      const threadId = `planning:${projectId}`;
      const res = await fetch(`/api/v1/threads/${encodeURIComponent(threadId)}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Erro ao limpar chat");
      setChatMessages([]);
      setChatError(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao limpar chat");
    }
  };

  const getLastAssistantMessage = () => {
    for (let i = chatMessages.length - 1; i >= 0; i -= 1) {
      const msg = chatMessages[i];
      if (msg.role === "assistant" && msg.content.trim()) {
        return msg.content;
      }
    }
    return "";
  };

  const getSelectedAssistantMessage = () => {
    if (selectedChatIndex === null) return "";
    const msg = chatMessages[selectedChatIndex];
    if (!msg || msg.role !== "assistant") return "";
    return msg.content.trim() ? msg.content : "";
  };

  const markdownToHtml = (markdown: string) => {
    let text = markdown;
    const codeBlocks: string[] = [];

    const escapeHtml = (value: string) =>
      value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    text = text.replace(/```[\s\S]*?```/g, (match) => {
      const index = codeBlocks.length;
      codeBlocks.push(match);
      return `__CODE_BLOCK_${index}__`;
    });

    text = text.replace(
      /^###\s+(.*)$/gm,
      "<h3 style=\"margin:12px 0 8px;font-size:18px;font-weight:600;\">$1</h3>"
    );
    text = text.replace(
      /^##\s+(.*)$/gm,
      "<h2 style=\"margin:14px 0 10px;font-size:20px;font-weight:700;\">$1</h2>"
    );
    text = text.replace(
      /^#\s+(.*)$/gm,
      "<h1 style=\"margin:16px 0 12px;font-size:22px;font-weight:700;\">$1</h1>"
    );

    const lines = text.split("\n");
    const output: string[] = [];
    let inList = false;
    let listType: "ul" | "ol" | null = null;

    const isTableSeparator = (line: string) =>
      /^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*$/.test(line);

    const normalizeRowLine = (line: string) => {
      const trimmed = line.trim();
      if (!trimmed.includes("|")) return trimmed;
      return trimmed.replace(/^\|/, "").replace(/\|$/, "");
    };

    const parseTableRow = (line: string) =>
      normalizeRowLine(line)
        .split("|")
        .map((cell) => escapeHtml(cell.trim()));

    const parseAlignments = (line: string) =>
      normalizeRowLine(line)
        .split("|")
        .map((cell) => {
          const trimmed = cell.trim();
          if (trimmed.startsWith(":") && trimmed.endsWith(":")) return "center";
          if (trimmed.endsWith(":")) return "right";
          if (trimmed.startsWith(":")) return "left";
          return "left";
        });

    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      const nextLine = lines[i + 1];

      if (line.includes("|") && nextLine && isTableSeparator(nextLine)) {
        if (inList) {
          output.push("</ul>");
          inList = false;
        }

        const headers = parseTableRow(line);
        const alignments = parseAlignments(nextLine);
        const rows: string[] = [];
        i += 2;
        while (i < lines.length && lines[i].includes("|")) {
          const cells = parseTableRow(lines[i]);
          rows.push(
            `<tr>${cells
              .map((c, idx) => {
                const align = alignments[idx] || "left";
                return `<td style=\"border:1px solid #e2e8f0;padding:6px 8px;text-align:${align};vertical-align:top;\">${c}</td>`;
              })
              .join("")}</tr>`
          );
          i += 1;
        }
        i -= 1;

        output.push(
          `<table style=\"border-collapse:collapse;width:100%;margin:10px 0;\"><thead><tr>${headers
            .map((h, idx) => {
              const align = alignments[idx] || "left";
              return `<th style=\"border:1px solid #cbd5f5;padding:6px 8px;text-align:${align};background:#f8fafc;font-weight:600;\">${h}</th>`;
            })
            .join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`
        );
        continue;
      }

      const unorderedMatch = /^\s*[-*]\s+(.*)/.exec(line);
      const orderedMatch = /^\s*\d+\.\s+(.*)/.exec(line);
      if (unorderedMatch || orderedMatch) {
        const nextType: "ul" | "ol" = orderedMatch ? "ol" : "ul";
        if (!inList || listType !== nextType) {
          if (inList) output.push(`</${listType}>`);
          output.push(
            nextType === "ol"
              ? "<ol style=\"margin:8px 0 8px 20px;\">"
              : "<ul style=\"margin:8px 0 8px 20px;\">"
          );
          inList = true;
          listType = nextType;
        }
        output.push(`<li>${(orderedMatch || unorderedMatch)?.[1] || ""}</li>`);
        continue;
      }

      if (inList) {
        output.push(`</${listType}>`);
        inList = false;
        listType = null;
      }
      output.push(line);
    }

    if (inList) output.push(`</${listType}>`);

    text = output.join("\n");
    text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/__(.+?)__/g, "<strong>$1</strong>");
    text = text.replace(/\*(.+?)\*/g, "<em>$1</em>");
    text = text.replace(/_(.+?)_/g, "<em>$1</em>");
    text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
    text = text.replace(
      /\[([^\]]+)]\((https?:\/\/[^\s)]+)\)/g,
      "<a href=\"$2\" style=\"color:#0f172a;text-decoration:underline;\" target=\"_blank\" rel=\"noreferrer\">$1</a>"
    );

    text = text
      .split(/\n\n+/)
      .map((block) => {
        if (
          block.trim().startsWith("<h") ||
          block.trim().startsWith("<ul") ||
          block.trim().startsWith("<ol") ||
          block.trim().startsWith("<table")
        ) {
          return block;
        }
        return `<p style=\"margin:8px 0;\">${block.replace(/\n/g, "<br />")}</p>`;
      })
      .join("\n");

    text = text.replace(/__CODE_BLOCK_(\d+)__/g, (_, idx) => {
      const raw = codeBlocks[Number(idx)] || "";
      const content = raw.replace(/^```[a-zA-Z0-9-]*\n?/, "").replace(/```$/, "");
      return `<pre><code>${content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>`;
    });

    return `<!DOCTYPE html><html><body>${text}</body></html>`;
  };

  const handleCopyLastResponse = async () => {
    const content = getSelectedAssistantMessage();
    if (!content) return;
    const html = markdownToHtml(content);
    try {
      if (navigator.clipboard && "write" in navigator.clipboard) {
        const item = new ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([content], { type: "text/plain" }),
        });
        await navigator.clipboard.write([item]);
      } else {
        await navigator.clipboard.writeText(content);
      }
      setCopyStatus("Copiado!");
      setTimeout(() => setCopyStatus("Copiar (Word/Docs)"), 2000);
    } catch (e) {
      setCopyStatus("Falha ao copiar");
      setTimeout(() => setCopyStatus("Copiar (Word/Docs)"), 2000);
    }
  };

  const appendAssistantChunk = (chunk: string) => {
    setChatMessages((prev) => {
      if (prev.length === 0) return [{ role: "assistant", content: chunk }];
      const last = prev[prev.length - 1];
      if (last.role !== "assistant") {
        return [...prev, { role: "assistant", content: chunk }];
      }
      const updated = [...prev];
      updated[updated.length - 1] = {
        ...last,
        content: `${last.content}${chunk}`,
      };
      return updated;
    });
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || isStreaming) return;
    setChatError(null);
    const message = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [
      ...prev,
      { role: "user", content: message },
      { role: "assistant", content: "" },
    ]);
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    setIsStreaming(true);

    const threadId = `planning:${projectId}`;
    const controller = new AbortController();
    chatAbortRef.current = controller;

    try {
      const res = await fetch(`/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          project_id: projectId,
          thread_id: threadId,
          enable_planning: true,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error("Erro ao iniciar streaming");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          const payload = line.replace(/^data:\s*/, "");
          if (!payload) continue;
          let parsed;
          try {
            parsed = JSON.parse(payload);
          } catch {
            continue;
          }
          if (parsed.type === "content" && parsed.content) {
            appendAssistantChunk(parsed.content);
          }
          if (parsed.type === "error") {
            setChatError(parsed.error || "Erro no streaming");
          }
          if (parsed.type === "done") {
            setIsStreaming(false);
          }
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") {
        return;
      }
      if (process.env.NODE_ENV === "development") {
        console.error("[Planning] Chat stream error:", e);
      }
      setChatError(e instanceof Error ? e.message : "Erro no streaming");
    } finally {
      setIsStreaming(false);
      chatAbortRef.current = null;
    }
  };

  const handleStopChat = () => {
    if (!chatAbortRef.current) return;
    chatAbortRef.current.abort();
    setIsStreaming(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F6F8] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-vsa-orange"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0f1f35] to-[#0a1628] flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-900 mb-4">{error || "Projeto não encontrado"}</p>
          <Link href="/planning">
            <Button>Voltar</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F6F8] text-slate-900">
      {/* Header */}
      <div className="border-b-2 border-slate-400 bg-white px-6 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Link href="/planning" className="text-slate-500 hover:text-slate-900">
                ← Projetos
              </Link>
              <span className="text-slate-400">/</span>
              <h1 className="text-xl font-semibold">{project.title}</h1>
            </div>
            {project.description && (
              <p className="text-sm text-slate-600 mt-1">{project.description}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <select
                value={embeddingModel}
                onChange={(e) => setEmbeddingModel(e.target.value)}
                className="px-2 py-1 bg-white border-2 border-slate-300 rounded-md text-xs text-slate-900"
              >
                {uniqueRagModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.dims})
                  </option>
                ))}
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSaveEmbeddingModel}
                disabled={savingEmbedding || embeddingModel === project.embedding_model}
                className="border-slate-300 text-slate-700"
              >
                {savingEmbedding ? "Salvando..." : "Salvar"}
              </Button>
            </div>
            {project.linear_project_url && (
              <a
                href={project.linear_project_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate-900 hover:text-slate-900"
              >
                Ver no Linear ↗
              </a>
            )}
            <Link href="/">
              <Button variant="outline" size="sm" className="border-slate-400 text-slate-700">
                Chat VSA
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 md:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.6fr] gap-6">
          {/* Left: Documents */}
          <div className="lg:col-span-1 order-1">
            <Card className="lg:-ml-2">
              <CardHeader>
                <CardTitle className="text-slate-900 flex items-center justify-between">
                  <span>Documentos</span>
                  <span className="text-sm font-normal text-slate-500">
                    {project.documents.length} arquivo(s)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Upload Area */}
                <div
                  className="border-2 border-dashed border-slate-400 rounded-lg p-4 text-center mb-4 hover:border-vsa-orange/50 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.add("border-vsa-orange");
                  }}
                  onDragLeave={(e) => {
                    e.currentTarget.classList.remove("border-vsa-orange");
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.remove("border-vsa-orange");
                    handleFileUpload(e.dataTransfer.files);
                  }}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.md,.txt"
                    multiple
                    className="hidden"
                    onChange={(e) => handleFileUpload(e.target.files)}
                  />
                  {uploading ? (
                    <span className="text-slate-500">Enviando...</span>
                  ) : (
                    <span className="text-slate-500">
                      Arraste arquivos ou clique para upload<br />
                      <span className="text-xs">(PDF, MD, TXT)</span>
                    </span>
                  )}
                </div>

                {/* Document List */}
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {project.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-2 bg-slate-50 rounded-lg border-2 border-slate-400 shadow-sm"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-900 truncate">{doc.file_name}</p>
                        <p className="text-xs text-slate-500">
                          {doc.file_type?.toUpperCase()} • {formatFileSize(doc.file_size || 0)}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="text-slate-900 hover:text-slate-900 p-1"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right: Project Chat */}
          <div className="lg:col-span-1 order-2">
            <Card className="lg:sticky lg:top-6">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-slate-900">Chat do Projeto</CardTitle>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopyLastResponse}
                      disabled={!getSelectedAssistantMessage()}
                      className="border-slate-300 text-slate-700"
                    >
                      {copyStatus}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setChatCollapsed((prev) => !prev)}
                      className="border-slate-300 text-slate-700"
                    >
                      {chatCollapsed ? "Expandir" : "Recolher"}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              {!chatCollapsed && (
                <CardContent className="flex flex-col gap-3">
                  {project.documents.length === 0 && (
                    <div className="text-xs text-slate-600 bg-slate-50 border-2 border-slate-300 rounded-lg p-2">
                      Sem documentos. Faça upload para melhorar as respostas.
                    </div>
                  )}

                  <div className="flex-1 max-h-[240px] md:max-h-[320px] lg:max-h-[560px] overflow-y-auto space-y-2">
                    {chatMessages.length === 0 && (
                      <p className="text-sm text-slate-600">Nenhuma mensagem ainda.</p>
                    )}
                    {chatMessages.map((msg, index) => (
                      <div
                        key={`${msg.role}-${index}`}
                        onClick={() => {
                          if (msg.role !== "assistant" || !msg.content.trim()) return;
                          setSelectedChatIndex(index);
                        }}
                        className={`p-2 rounded-lg text-sm border-2 shadow-sm ${
                          msg.role === "user"
                            ? "bg-slate-50 border-slate-300 text-slate-900"
                            : `bg-white border-slate-200 text-slate-900 ${
                                selectedChatIndex === index
                                  ? "ring-2 ring-vsa-orange/40"
                                  : ""
                              }`
                        }`}
                      >
                        <p className="text-xs text-slate-500 mb-1">
                          {msg.role === "user" ? "Você" : "VSA"}
                        </p>
                        {msg.role === "assistant" && !msg.content.trim() && isStreaming ? (
                          <ThinkingIndicator compact={true} vsaMode={false} />
                        ) : (
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        )}
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>

                  {chatError && (
                    <div className="text-xs text-red-700 bg-red-50 border-2 border-red-300 rounded-lg p-2">
                      {chatError}
                    </div>
                  )}

                  <div className="flex flex-col gap-2">
                    <textarea
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          handleSendChat();
                        }
                      }}
                      rows={3}
                      className="w-full min-h-[72px] md:min-h-[90px] px-3 py-2 bg-white border-2 border-slate-300 rounded-lg text-slate-900 shadow-sm focus:border-vsa-orange focus:outline-none resize-none"
                      placeholder="Pergunte sobre os documentos do projeto"
                    />
                    <div className="flex items-center justify-between gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleClearChat}
                        className="border-slate-300 text-slate-700"
                      >
                        Limpar chat
                      </Button>
                      <div className="flex items-center gap-2">
                        {isStreaming && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleStopChat}
                            className="border-slate-300 text-slate-700"
                          >
                            Parar
                          </Button>
                        )}
                        <Button
                          onClick={handleSendChat}
                          disabled={isStreaming || !chatInput.trim()}
                          className="bg-vsa-orange hover:bg-vsa-orange-dark"
                        >
                          {isStreaming ? "Enviando..." : "Enviar"}
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
