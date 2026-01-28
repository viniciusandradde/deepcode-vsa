-- Tabela para gerenciar delete lógico de threads de chat.
-- Threads arquivadas deixam de aparecer na listagem da API,
-- mas os checkpoints permanecem para fins de auditoria.

CREATE TABLE IF NOT EXISTS archived_threads (
    thread_id   TEXT PRIMARY KEY,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason      TEXT NULL
);

-- Tabela de threads arquivadas (delete lógico das sessões de chat)
CREATE TABLE IF NOT EXISTS public.archived_threads (
    thread_id TEXT PRIMARY KEY,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason TEXT
);

