import json
import uuid
from typing import Any


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Repository:
    def __init__(self, conn):
        self.conn = conn

    def create_plan(self, thread_id: str, raw_command: str, summary: str, mode: str = 'standard') -> str:
        plan_id = _uid('plan')
        self.conn.execute(
            'INSERT INTO plans(id,source_thread_id,raw_command,summary,mode,status) VALUES (?,?,?,?,?,?)',
            (plan_id, thread_id, raw_command, summary, mode, 'awaiting_approval'),
        )
        self.conn.commit()
        return plan_id

    def create_task(self, plan_id: str, title: str, work_type: str, sequence_no: int, description: str = '', target_agent: str | None = None) -> str:
        task_id = _uid('task')
        self.conn.execute(
            'INSERT INTO tasks(id,plan_id,title,description,work_type,sequence_no,target_agent,status) VALUES (?,?,?,?,?,?,?,?)',
            (task_id, plan_id, title, description, work_type, sequence_no, target_agent, 'awaiting_approval'),
        )
        self.conn.commit()
        return task_id

    def approve_plan(self, plan_id: str, approver_id: str, thread_id: str, approval_text: str) -> None:
        self.conn.execute('UPDATE plans SET status=\'approved\', updated_at=datetime(\'now\') WHERE id=?', (plan_id,))
        self.conn.execute('UPDATE tasks SET status=\'approved\', updated_at=datetime(\'now\') WHERE plan_id=? AND status=\'awaiting_approval\'', (plan_id,))
        self.conn.execute(
            'INSERT INTO approvals(plan_id,thread_id,approver_id,approval_text) VALUES (?,?,?,?)',
            (plan_id, thread_id, approver_id, approval_text),
        )
        self.conn.commit()

    def create_run(self, task_id: str, agent_id: str, dedupe_key: str, state: str = 'queued') -> str:
        run_id = _uid('run')
        self.conn.execute(
            "INSERT INTO runs(id,task_id,agent_id,state,dedupe_key,started_at,heartbeat_at) VALUES (?,?,?,?,?,datetime('now'),datetime('now'))",
            (run_id, task_id, agent_id, state, dedupe_key),
        )
        self.conn.commit()
        return run_id

    def update_run_state(self, run_id: str, state: str, error: str | None = None):
        self.conn.execute(
            'UPDATE runs SET state=?, error=?, updated_at=datetime(\'now\'), heartbeat_at=datetime(\'now\') WHERE id=?',
            (state, error, run_id),
        )
        self.conn.commit()


    def attach_dispatch_session(self, run_id: str, session_key: str, dispatch_command: str, response: dict[str, Any]):
        self.conn.execute(
            "UPDATE runs SET openclaw_session_key=?, dispatch_command=?, dispatch_response_json=?, dispatch_error_json=NULL, updated_at=datetime('now') WHERE id=?",
            (session_key, dispatch_command, json.dumps(response, sort_keys=True), run_id),
        )
        self.conn.commit()

    def record_dispatch_attempt(self, run_id: str, attempted_agent: str, session_key: str | None = None, dispatch_command: str | None = None, response: dict[str, Any] | None = None, error: dict[str, Any] | None = None):
        self.conn.execute(
            """
            INSERT INTO dispatch_attempts(run_id,attempted_agent,session_key,dispatch_command,dispatch_response_json,dispatch_error_json)
            VALUES (?,?,?,?,?,?)
            """,
            (
                run_id,
                attempted_agent,
                session_key,
                dispatch_command,
                json.dumps(response or {}, sort_keys=True),
                json.dumps(error or {}, sort_keys=True),
            ),
        )
        if error:
            self.conn.execute(
                "UPDATE runs SET dispatch_error_json=?, updated_at=datetime('now') WHERE id=?",
                (json.dumps(error, sort_keys=True), run_id),
            )
        self.conn.commit()

    def add_event(self, event_type: str, payload: dict[str, Any], plan_id: str | None = None, task_id: str | None = None, run_id: str | None = None):
        self.conn.execute(
            'INSERT INTO events(plan_id,task_id,run_id,event_type,payload_json) VALUES (?,?,?,?,?)',
            (plan_id, task_id, run_id, event_type, json.dumps(payload, sort_keys=True)),
        )
        self.conn.commit()

    def add_artifact(self, task_id: str, artifact_type: str, path: str, run_id: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        artifact_id = _uid('artifact')
        self.conn.execute(
            'INSERT INTO artifacts(id,task_id,run_id,artifact_type,path,metadata_json) VALUES (?,?,?,?,?,?)',
            (artifact_id, task_id, run_id, artifact_type, path, json.dumps(metadata or {}, sort_keys=True)),
        )
        self.conn.commit()
        return artifact_id


    def upsert_ci_check(self, check_id: str, run_id: str, provider: str, status: str, details: dict[str, Any] | None = None):
        self.conn.execute(
            """
            INSERT INTO ci_checks(id,run_id,provider,status,details_json,updated_at)
            VALUES (?,?,?,?,?,datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
              status=excluded.status,
              details_json=excluded.details_json,
              updated_at=datetime('now')
            """,
            (check_id, run_id, provider, status, json.dumps(details or {}, sort_keys=True)),
        )
        self.conn.commit()

    def get_run_by_dedupe_key(self, dedupe_key: str):
        return self.conn.execute('SELECT * FROM runs WHERE dedupe_key=?', (dedupe_key,)).fetchone()

    def get_or_create_run(self, task_id: str, agent_id: str, dedupe_key: str, state: str = 'queued') -> str:
        row = self.conn.execute('SELECT id FROM runs WHERE dedupe_key=?', (dedupe_key,)).fetchone()
        if row:
            return row[0]
        return self.create_run(task_id, agent_id, dedupe_key, state)
