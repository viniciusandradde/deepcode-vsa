/**
 * Local storage utilities for persisting session data
 */

const STORAGE_PREFIX = "ai_agent_rag_";

export interface StoredSession {
  id: string;
  title: string;
  createdAt: number;
  lastAccessed: number;
  messageCount: number;
}

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  modelId?: string;
  usedTavily?: boolean;
  editedAt?: number;
}

export const storage = {
  sessions: {
    getAll(): StoredSession[] {
      try {
        const data = localStorage.getItem(`${STORAGE_PREFIX}sessions`);
        return data ? JSON.parse(data) : [];
      } catch {
        return [];
      }
    },

    save(sessions: StoredSession[]): void {
      try {
        localStorage.setItem(`${STORAGE_PREFIX}sessions`, JSON.stringify(sessions));
      } catch (error) {
        console.error("Error saving sessions:", error);
      }
    },

    add(session: StoredSession): void {
      const sessions = this.getAll();
      sessions.unshift(session);
      this.save(sessions);
    },

    update(id: string, updates: Partial<StoredSession>): void {
      const sessions = this.getAll();
      const index = sessions.findIndex((s) => s.id === id);
      if (index !== -1) {
        sessions[index] = { ...sessions[index], ...updates };
        this.save(sessions);
      }
    },

    remove(id: string): void {
      const sessions = this.getAll();
      this.save(sessions.filter((s) => s.id !== id));
    },
  },

  messages: {
    get(sessionId: string): StoredMessage[] {
      try {
        const data = localStorage.getItem(`${STORAGE_PREFIX}messages_${sessionId}`);
        return data ? JSON.parse(data) : [];
      } catch {
        return [];
      }
    },

    save(sessionId: string, messages: StoredMessage[]): void {
      try {
        localStorage.setItem(`${STORAGE_PREFIX}messages_${sessionId}`, JSON.stringify(messages));
      } catch (error) {
        console.error("Error saving messages:", error);
      }
    },

    add(sessionId: string, message: StoredMessage): void {
      const messages = this.get(sessionId);
      messages.push(message);
      this.save(sessionId, messages);
    },

    clear(sessionId: string): void {
      try {
        localStorage.removeItem(`${STORAGE_PREFIX}messages_${sessionId}`);
      } catch (error) {
        console.error("Error clearing messages:", error);
      }
    },
  },

  artifacts: {
    getBySession<T = unknown>(sessionId: string): T[] {
      try {
        const data = localStorage.getItem(`${STORAGE_PREFIX}artifacts_${sessionId}`);
        return data ? JSON.parse(data) : [];
      } catch {
        return [];
      }
    },

    saveForSession(sessionId: string, artifacts: unknown[]): void {
      try {
        localStorage.setItem(`${STORAGE_PREFIX}artifacts_${sessionId}`, JSON.stringify(artifacts));
      } catch (error) {
        console.error("Error saving artifacts:", error);
      }
    },

    clearSession(sessionId: string): void {
      try {
        localStorage.removeItem(`${STORAGE_PREFIX}artifacts_${sessionId}`);
      } catch (error) {
        console.error("Error clearing artifacts:", error);
      }
    },
  },

  settings: {
    get<T>(key: string, defaultValue: T): T {
      try {
        const data = localStorage.getItem(`${STORAGE_PREFIX}settings_${key}`);
        return data ? JSON.parse(data) : defaultValue;
      } catch {
        return defaultValue;
      }
    },

    set<T>(key: string, value: T): void {
      try {
        localStorage.setItem(`${STORAGE_PREFIX}settings_${key}`, JSON.stringify(value));
      } catch (error) {
        console.error("Error saving setting:", error);
      }
    },
  },

  clear(): void {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
        if (key.startsWith(STORAGE_PREFIX)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.error("Error clearing storage:", error);
    }
  },
};

