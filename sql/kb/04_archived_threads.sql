-- Tabela de threads arquivadas (delete lógico das sessões de chat)
CREATE TABLE IF NOT EXISTS public.archived_threads (
    thread_id TEXT PRIMARY KEY,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason TEXT
);

