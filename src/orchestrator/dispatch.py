from .artifacts import assert_required_artifacts
from .ci import aggregate_ci
from .git_pr import ensure_branch_and_pr
from .routing import resolve_agent
from .openclaw_dispatch import OpenClawDispatchAdapter


class DispatchEngine:
    def __init__(self, repo, config: dict, available_agents: set[str] | None = None, github_client=None, dispatch_adapter=None):
        self.repo = repo
        self.config = config
        self.available_agents = available_agents or {'main', 'chad', 'halbert'}
        self.github_client = github_client
        self.dispatch_adapter = dispatch_adapter or OpenClawDispatchAdapter(config)

    def dispatch_task(self, task_row, branch_name: str | None = None, pr_url: str | None = None) -> str:
        task = dict(task_row)
        if task.get('work_type') == 'code' and not pr_url and branch_name and self.github_client:
            pr_url = self.github_client.ensure_pr(
                branch_name,
                base=self.config.get('github', {}).get('baseBranch', 'main'),
                title=f"{task['id']}: {task['title']}",
                body=f"Automated PR for orchestrator task {task['id']}",
            )
        ensure_branch_and_pr(task, branch_name, pr_url)
        agent = resolve_agent(task, self.config, self.available_agents)
        dedupe = f"dispatch:{task['id']}"
        existing = self.repo.get_run_by_dedupe_key(dedupe)
        run_id = existing['id'] if existing else self.repo.create_run(task['id'], agent, dedupe, 'running')

        session_key = existing['openclaw_session_key'] if existing else None
        if not session_key:
            result = self.dispatch_adapter.dispatch(task, run_id, agent)
            session_key = result.session_key
            self.repo.attach_dispatch_session(
                run_id,
                result.session_key,
                self.dispatch_adapter.command_for_log(result.command),
                result.raw,
            )
            self.repo.add_event(
                'run.dispatched',
                {'agent': agent, 'session_key': result.session_key},
                task_id=task['id'],
                run_id=run_id,
                plan_id=task['plan_id'],
            )
        if branch_name or pr_url:
            self.repo.conn.execute('update tasks set pr_url=?, status=\'in_progress\' where id=?', (pr_url, task['id']))
            self.repo.conn.execute('update runs set branch_name=?, pr_url=? where id=?', (branch_name, pr_url, run_id))
            self.repo.conn.commit()
        return run_id

    def process_ci(self, run_id: str, checks: list[dict]) -> str:
        state = aggregate_ci(checks)
        mapped = {'pending': 'waiting_ci', 'success': 'completed', 'failed': 'failed'}[state]
        self.repo.update_run_state(run_id, mapped)
        row = self.repo.conn.execute('select task_id from runs where id=?', (run_id,)).fetchone()
        task_id = row['task_id'] if row else None
        if task_id:
            task_state = {'pending': 'waiting_ci', 'success': 'done', 'failed': 'failed'}[state]
            if task_state == 'done':
                self.repo.conn.execute("update tasks set status='done', completed_at=datetime('now') where id=?", (task_id,))
            else:
                self.repo.conn.execute('update tasks set status=? where id=?', (task_state, task_id))
            self.repo.conn.commit()
        for c in checks:
            check_id = c.get('id') or f"{c.get('provider','ci')}:{run_id}:{c.get('status','pending')}"
            self.repo.upsert_ci_check(check_id, run_id, c.get('provider', 'unknown'), c.get('status', 'pending'), c.get('details', {}))
        self.repo.add_event('ci.updated', {'state': state}, run_id=run_id, task_id=task_id)
        return mapped

    def complete_task(self, task_row, artifacts: list[dict] | None = None):
        task = dict(task_row)
        if artifacts is None:
            rows = self.repo.conn.execute('select artifact_type from artifacts where task_id=?', (task['id'],)).fetchall()
            artifacts = [dict(r) for r in rows]
        assert_required_artifacts(task, artifacts)
        self.repo.conn.execute("update tasks set status='done', completed_at=datetime('now') where id=?", (task['id'],))
        self.repo.conn.commit()
