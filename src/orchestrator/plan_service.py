import json
import subprocess
from pathlib import Path

from .decompose import decompose_plan
from .db.repository import Repository
from .approval import ensure_same_thread


class PlanService:
    def __init__(self, repo: Repository, parser_script: str | None = None):
        self.repo = repo
        self.parser_script = parser_script or str(Path(__file__).resolve().parents[2] / 'skills' / 'execute-plan' / 'scripts' / 'parse_execute_plan.js')

    def parse(self, raw_text: str) -> dict:
        cp = subprocess.run(['node', self.parser_script, '--text', raw_text], check=True, capture_output=True, text=True)
        return json.loads(cp.stdout)

    def create_from_command(self, raw_text: str, source_thread_id: str, source_message_id: str | None = None) -> tuple[str, list[str]]:
        parsed = self.parse(raw_text)
        if parsed.get('requires_clarification'):
            raise ValueError(parsed.get('clarification_question', 'plan clarification required'))
        plan_text = parsed['parsed']['plan']
        plan_id = self.repo.create_plan(source_thread_id, raw_text, plan_text, parsed['parsed'].get('mode', 'standard'))
        task_ids = []
        for idx, task in enumerate(decompose_plan(plan_text), start=1):
            tid = self.repo.create_task(plan_id, task.title, task.work_type, idx, task.description, None)
            self.repo.add_event('task.created', {'sequence': idx, 'depends_on': task.depends_on}, plan_id=plan_id, task_id=tid)
            task_ids.append(tid)
        self.repo.add_event('plan.created', {'task_count': len(task_ids), 'source_message_id': source_message_id}, plan_id=plan_id)
        return plan_id, task_ids

    def approve(self, plan_id: str, source_thread_id: str, approval_thread_id: str, approver_id: str, approval_text: str = 'approve'):
        ensure_same_thread(source_thread_id, approval_thread_id)
        self.repo.approve_plan(plan_id, approver_id, approval_thread_id, approval_text)
        self.repo.add_event('plan.approved', {'approver_id': approver_id}, plan_id=plan_id)
