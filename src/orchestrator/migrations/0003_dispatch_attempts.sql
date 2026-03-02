ALTER TABLE runs ADD COLUMN dispatch_error_json TEXT;

CREATE TABLE IF NOT EXISTS dispatch_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  attempted_agent TEXT NOT NULL,
  session_key TEXT,
  dispatch_command TEXT,
  dispatch_response_json TEXT,
  dispatch_error_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dispatch_attempts_run_id ON dispatch_attempts(run_id);
