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

    def get_or_create_run(self, task_id: str, agent_id: str, dedupe_key: str, state: str = 'queued') -> str:
        row = self.conn.execute('SELECT id FROM runs WHERE dedupe_key=?', (dedupe_key,)).fetchone()
        if row:
            return row[0]
        return self.create_run(task_id, agent_id, dedupe_key, state)
