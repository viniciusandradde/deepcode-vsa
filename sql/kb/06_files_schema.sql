-- Files table for uploads and attachments
CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY,
  thread_id TEXT,
  client_id TEXT,
  empresa TEXT,
  name TEXT NOT NULL,
  mime TEXT NOT NULL,
  size INT NOT NULL,
  sha256 TEXT NOT NULL,
  bucket TEXT NOT NULL,
  object_key TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  status TEXT DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_files_thread_id ON files(thread_id);
CREATE INDEX IF NOT EXISTS idx_files_expires_at ON files(expires_at);
