ALTER TABLE runs ADD COLUMN openclaw_session_key TEXT;
ALTER TABLE runs ADD COLUMN dispatch_command TEXT;
ALTER TABLE runs ADD COLUMN dispatch_response_json TEXT;

CREATE INDEX IF NOT EXISTS idx_runs_openclaw_session_key ON runs(openclaw_session_key);
