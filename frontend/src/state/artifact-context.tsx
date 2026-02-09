"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import { storage } from "@/lib/storage";
import type { Artifact, ArtifactStartData } from "./artifact-types";

interface ArtifactState {
  /** All artifacts keyed by session id. */
  artifactsBySession: Record<string, Artifact[]>;
  /** Currently selected artifact id (shown in side panel). */
  selectedArtifactId: string | null;
  /** Whether the artifact panel is open. */
  panelOpen: boolean;

  /** Open the panel with a specific artifact. */
  selectArtifact: (id: string) => void;
  /** Close the artifact panel. */
  closePanel: () => void;

  /** Called on artifact_start SSE event — create placeholder. */
  startArtifact: (
    sessionId: string,
    messageId: string,
    data: ArtifactStartData,
  ) => void;
  /** Called on artifact_content SSE event — append content. */
  appendArtifactContent: (artifactId: string, chunk: string) => void;
  /** Called on artifact_end SSE event — finalize artifact. */
  endArtifact: (artifactId: string) => void;

  /** Add a fully-formed artifact (e.g. from LLM detection). */
  addArtifact: (artifact: Artifact) => void;

  /** Get artifacts for a specific session. */
  getSessionArtifacts: (sessionId: string) => Artifact[];

  /** Clear all artifacts for a session. */
  clearSessionArtifacts: (sessionId: string) => void;
}

const ArtifactContext = createContext<ArtifactState | null>(null);

export function ArtifactProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [artifactsBySession, setArtifactsBySession] = useState<
    Record<string, Artifact[]>
  >({});
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(
    null,
  );
  const [panelOpen, setPanelOpen] = useState(false);

  // Buffer for streaming artifact content
  const contentBufferRef = useRef<Record<string, string>>({});
  // Track which session an in-flight artifact belongs to
  const artifactSessionRef = useRef<Record<string, string>>({});

  const selectArtifact = useCallback((id: string) => {
    setSelectedArtifactId(id);
    setPanelOpen(true);
  }, []);

  const closePanel = useCallback(() => {
    setPanelOpen(false);
  }, []);

  const startArtifact = useCallback(
    (sessionId: string, messageId: string, data: ArtifactStartData) => {
      const artifact: Artifact = {
        id: data.artifact_id,
        sessionId,
        messageId,
        type: data.artifact_type,
        title: data.title,
        content: "",
        createdAt: Date.now(),
        source: data.source,
        intent: data.intent,
      };

      contentBufferRef.current[data.artifact_id] = "";
      artifactSessionRef.current[data.artifact_id] = sessionId;

      setArtifactsBySession((prev) => {
        const existing = prev[sessionId] || [];
        return { ...prev, [sessionId]: [...existing, artifact] };
      });
    },
    [],
  );

  const appendArtifactContent = useCallback(
    (artifactId: string, chunk: string) => {
      contentBufferRef.current[artifactId] =
        (contentBufferRef.current[artifactId] || "") + chunk;
    },
    [],
  );

  const endArtifact = useCallback((artifactId: string) => {
    const finalContent = contentBufferRef.current[artifactId] || "";
    const sessionId = artifactSessionRef.current[artifactId];

    delete contentBufferRef.current[artifactId];
    delete artifactSessionRef.current[artifactId];

    if (!sessionId) return;

    setArtifactsBySession((prev) => {
      const existing = prev[sessionId] || [];
      const updated = existing.map((a) =>
        a.id === artifactId ? { ...a, content: finalContent } : a,
      );
      storage.artifacts.saveForSession(sessionId, updated);
      return { ...prev, [sessionId]: updated };
    });
  }, []);

  const addArtifact = useCallback((artifact: Artifact) => {
    setArtifactsBySession((prev) => {
      const existing = prev[artifact.sessionId] || [];
      // Avoid duplicates
      if (existing.some((a) => a.id === artifact.id)) return prev;
      const updated = [...existing, artifact];
      storage.artifacts.saveForSession(artifact.sessionId, updated);
      return { ...prev, [artifact.sessionId]: updated };
    });
  }, []);

  const getSessionArtifacts = useCallback(
    (sessionId: string) => {
      return artifactsBySession[sessionId] || [];
    },
    [artifactsBySession],
  );

  const clearSessionArtifacts = useCallback((sessionId: string) => {
    setArtifactsBySession((prev) => {
      const next = { ...prev };
      delete next[sessionId];
      return next;
    });
    storage.artifacts.clearSession(sessionId);
  }, []);

  const value = useMemo<ArtifactState>(
    () => ({
      artifactsBySession,
      selectedArtifactId,
      panelOpen,
      selectArtifact,
      closePanel,
      startArtifact,
      appendArtifactContent,
      endArtifact,
      addArtifact,
      getSessionArtifacts,
      clearSessionArtifacts,
    }),
    [
      artifactsBySession,
      selectedArtifactId,
      panelOpen,
      selectArtifact,
      closePanel,
      startArtifact,
      appendArtifactContent,
      endArtifact,
      addArtifact,
      getSessionArtifacts,
      clearSessionArtifacts,
    ],
  );

  return (
    <ArtifactContext.Provider value={value}>
      {children}
    </ArtifactContext.Provider>
  );
}

export function useArtifacts() {
  const context = useContext(ArtifactContext);
  if (!context) {
    throw new Error("useArtifacts must be used within ArtifactProvider");
  }
  return context;
}
