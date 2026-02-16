"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { storage } from "@/lib/storage";
import { apiClient } from "@/lib/api-client";
import type { GenesisSession } from "./types";

interface SessionState {
  sessions: GenesisSession[];
  setSessions: React.Dispatch<React.SetStateAction<GenesisSession[]>>;
  currentSessionId: string;
  setCurrentSessionId: React.Dispatch<React.SetStateAction<string>>;
  createSession: () => Promise<string | undefined>;
  selectSession: (id: string) => Promise<void>;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => Promise<void>;
  fetchSession: (sessionId: string, merge?: boolean) => Promise<any>;
  sessionsLoaded: boolean;
}

const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [sessions, setSessions] = useState<GenesisSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [sessionsLoaded, setSessionsLoaded] = useState(false);

  const createSession = useCallback(async (): Promise<string | undefined> => {
    try {
      const res = await apiClient.post("/api/threads", {});
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
      setCurrentSessionId(session.id);

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
      const res = await apiClient.get(`/api/threads/${sessionId}`);
      if (!res.ok) return [];
      const data = await res.json();
      const messages = (data.messages || []).map((msg: any, idx: number) => ({
        id: msg.id || `msg-${idx}`,
        role: msg.role === "user" ? "user" : "assistant",
        content: typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content),
        timestamp: msg.timestamp || Date.now(),
        modelId: msg.modelId,
        usedTavily: msg.usedTavily,
      }));
      return { messages, merge };
    } catch (error) {
      console.error("Error fetching session:", error);
      return [];
    }
  }, []);

  const selectSession = useCallback(async (id: string) => {
    setCurrentSessionId(id);
  }, []);

  const renameSession = useCallback((id: string, title: string) => {
    setSessions((prev) => prev.map((session) => (session.id === id ? { ...session, title } : session)));
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    try {
      const res = await apiClient.delete(`/api/threads/${id}`);
      if (!res.ok && res.status !== 204) {
        console.error("Failed to delete thread in backend:", res.status);
      }
    } catch (error) {
      console.error("Error deleting thread:", error);
    }

    setSessions((prev) => {
      const nextSessions = prev.filter((session) => session.id !== id);
      setCurrentSessionId((prevId) => (prevId === id ? nextSessions[0]?.id ?? "" : prevId));
      return nextSessions;
    });

    storage.sessions.remove(id);
    storage.messages.clear(id);
  }, []);

  useEffect(() => {
    async function loadSessions() {
      const storedSessions = storage.sessions.getAll();

      try {
        const res = await apiClient.get("/api/threads", { cache: "no-store" });
        if (res.ok) {
          const data = await res.json();
          const threads = Array.isArray(data.threads) ? data.threads : [];

          const apiSessions: GenesisSession[] = threads.map((thread: any) => {
            const id = thread.thread_id || thread.id;
            const lastTs = thread.last_ts ? Date.parse(thread.last_ts) : Date.now();
            const dt = new Date(lastTs);
            const time = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            const date = dt.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

            const title = thread.title || `Sessão de ${date} ${time}`;

            return { id, title, createdAt: lastTs, lastActivityAt: lastTs };
          });

          setSessions(apiSessions);

          storage.sessions.save(apiSessions.map(s => ({
            id: s.id,
            title: s.title,
            createdAt: s.createdAt,
            lastAccessed: Date.now(),
            messageCount: 0,
          })));

          if (apiSessions[0]) {
            setCurrentSessionId((prev) => prev || apiSessions[0].id);
          }
        } else if (storedSessions.length === 0) {
          const newSessionId = await createSession();
          if (newSessionId) {
            setCurrentSessionId(newSessionId);
          }
        }
      } catch (error) {
        console.error("Error loading sessions:", error);
        if (storedSessions.length > 0) {
          setSessions(storedSessions.map((s) => ({
            id: s.id,
            title: s.title,
            createdAt: s.createdAt,
          })));
        }
      } finally {
        setSessionsLoaded(true);
      }
    }
    loadSessions();
  }, [createSession]);

  const value = useMemo<SessionState>(
    () => ({
      sessions,
      setSessions,
      currentSessionId,
      setCurrentSessionId,
      createSession,
      selectSession,
      renameSession,
      deleteSession,
      fetchSession,
      sessionsLoaded,
    }),
    [sessions, currentSessionId, createSession, selectSession, renameSession, deleteSession, fetchSession, sessionsLoaded],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
}
