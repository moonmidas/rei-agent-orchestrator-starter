from .artifacts import assert_required_artifacts
from .ci import aggregate_ci
from .git_pr import ensure_branch_and_pr
from .routing import resolve_agent


class DispatchEngine:
    def __init__(self, repo, config: dict, available_agents: set[str] | None = None):
        self.repo = repo
        self.config = config
        self.available_agents = available_agents or {'main', 'chad', 'halbert'}

    def dispatch_task(self, task_row, branch_name: str | None = None, pr_url: str | None = None) -> str:
        task = dict(task_row)
        ensure_branch_and_pr(task, branch_name, pr_url)
        agent = resolve_agent(task, self.config, self.available_agents)
        dedupe = f"dispatch:{task['id']}"
        run_id = self.repo.get_or_create_run(task['id'], agent, dedupe, 'running')
        self.repo.add_event('run.dispatched', {'agent': agent}, task_id=task['id'], run_id=run_id, plan_id=task['plan_id'])
        if branch_name or pr_url:
            self.repo.conn.execute('update tasks set pr_url=?, status=\'in_progress\' where id=?', (pr_url, task['id']))
            self.repo.conn.commit()
        return run_id

    def process_ci(self, run_id: str, checks: list[dict]) -> str:
        state = aggregate_ci(checks)
        mapped = {'pending': 'waiting_ci', 'success': 'completed', 'failed': 'failed'}[state]
        self.repo.update_run_state(run_id, mapped)
        self.repo.add_event('ci.updated', {'state': state}, run_id=run_id)
        return mapped

    def complete_task(self, task_row, artifacts: list[dict] | None = None):
        task = dict(task_row)
        if artifacts is None:
            rows = self.repo.conn.execute('select artifact_type from artifacts where task_id=?', (task['id'],)).fetchall()
            artifacts = [dict(r) for r in rows]
        assert_required_artifacts(task, artifacts)
        self.repo.conn.execute("update tasks set status='done', completed_at=datetime('now') where id=?", (task['id'],))
        self.repo.conn.commit()
