from .artifacts import assert_required_artifacts
from .ci import aggregate_ci
from .git_pr import ensure_branch_and_pr
from .routing import resolve_agent
from .openclaw_dispatch import OpenClawDispatchAdapter, DispatchError
from .notifications import MilestoneNotifier


class DispatchEngine:
    def __init__(self, repo, config: dict, available_agents: set[str] | None = None, github_client=None, dispatch_adapter=None, notifier=None):
        self.repo = repo
        self.config = config
        self.available_agents = available_agents
        self.github_client = github_client
        self.dispatch_adapter = dispatch_adapter or OpenClawDispatchAdapter(config)
        self.notifier = notifier or MilestoneNotifier(config)

    def _origin_thread_for_task(self, task: dict) -> str | None:
        row = self.repo.conn.execute('select source_thread_id from plans where id=?', (task['plan_id'],)).fetchone()
        return row['source_thread_id'] if row else None

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
        dedupe = f"dispatch:{task['id']}"
        existing = self.repo.get_run_by_dedupe_key(dedupe)
        origin_thread = self._origin_thread_for_task(task)
        if existing:
            run_id = existing['id']
            agent = existing['agent_id']
        else:
            available_agents = set(self.available_agents or [])
            if not available_agents and hasattr(self.dispatch_adapter, 'probe_capabilities'):
                try:
                    self.dispatch_adapter.probe_capabilities()
                except Exception:
                    pass
                available_agents = set(getattr(self.dispatch_adapter, '_known_agents', set()) or set())
            if not available_agents:
                available_agents = {'chad'}
            agent = resolve_agent(task, self.config, available_agents)
            run_id = self.repo.create_run(task['id'], agent, dedupe, 'running')
            self.notifier.notify(self.repo, 'queued', task['plan_id'], task['id'], run_id, origin_thread, f"🟡 queued: task {task['id']} -> {agent}")

        session_key = existing['openclaw_session_key'] if existing else None
        if not session_key:
            try:
                result = self.dispatch_adapter.dispatch(task, run_id, agent)
                session_key = result.session_key
                cmd_for_log = self.dispatch_adapter.command_for_log(result.command)
                self.repo.attach_dispatch_session(run_id, result.session_key, cmd_for_log, result.raw)
                self.repo.record_dispatch_attempt(run_id, agent, session_key=result.session_key, dispatch_command=cmd_for_log, response=result.raw)
            except DispatchError as e:
                self.repo.record_dispatch_attempt(run_id, agent, dispatch_command=self.dispatch_adapter.command_for_log(e.command) if e.command else '', error=e.raw)
                self.repo.update_run_state(run_id, 'failed', str(e))
                self.repo.add_event('run.dispatch_failed', {'agent': agent, 'error': str(e), 'raw': e.raw}, task_id=task['id'], run_id=run_id, plan_id=task['plan_id'])
                self.notifier.notify(self.repo, 'failed', task['plan_id'], task['id'], run_id, origin_thread, f"🔴 failed: task {task['id']} dispatch error")
                raise
            self.repo.add_event(
                'run.dispatched',
                {'agent': agent, 'session_key': result.session_key},
                task_id=task['id'],
                run_id=run_id,
                plan_id=task['plan_id'],
            )
            self.notifier.notify(self.repo, 'dispatched', task['plan_id'], task['id'], run_id, origin_thread, f"🚀 dispatched: task {task['id']} session={session_key}")
        if branch_name or pr_url:
            self.repo.conn.execute('update tasks set pr_url=?, status=\'in_progress\' where id=?', (pr_url, task['id']))
            self.repo.conn.execute('update runs set branch_name=?, pr_url=? where id=?', (branch_name, pr_url, run_id))
            self.repo.conn.commit()
        return run_id

    def process_ci(self, run_id: str, checks: list[dict]) -> str:
        state = aggregate_ci(checks)
        mapped = {'pending': 'waiting_ci', 'success': 'completed', 'failed': 'failed'}[state]
        row = self.repo.conn.execute('select task_id from runs where id=?', (run_id,)).fetchone()
        task_id = row['task_id'] if row else None
        task = self.repo.conn.execute('select * from tasks where id=?', (task_id,)).fetchone() if task_id else None

        if task_id:
            task_state = {'pending': 'waiting_ci', 'success': 'done', 'failed': 'failed'}[state]
            if task_state == 'done':
                try:
                    self.complete_task(task)
                    self.repo.update_run_state(run_id, 'completed')
                except ValueError as e:
                    self.repo.update_run_state(run_id, 'waiting_review', str(e))
                    self.repo.conn.execute('update tasks set status=? where id=?', ('review', task_id))
                    self.repo.conn.commit()
                    self.repo.add_event('run.artifact_gate_failed', {'error': str(e)}, run_id=run_id, task_id=task_id, plan_id=task['plan_id'])
                    mapped = 'waiting_review'
            else:
                self.repo.update_run_state(run_id, mapped)
                self.repo.conn.execute('update tasks set status=? where id=?', (task_state, task_id))
                self.repo.conn.commit()
        else:
            self.repo.update_run_state(run_id, mapped)

        for c in checks:
            check_id = c.get('id') or f"{c.get('provider','ci')}:{run_id}:{c.get('status','pending')}"
            self.repo.upsert_ci_check(check_id, run_id, c.get('provider', 'unknown'), c.get('status', 'pending'), c.get('details', {}))
        self.repo.add_event('ci.updated', {'state': state}, run_id=run_id, task_id=task_id)
        if task:
            origin = self._origin_thread_for_task(dict(task))
            if mapped == 'waiting_ci':
                self.notifier.notify(self.repo, 'waiting_ci', task['plan_id'], task['id'], run_id, origin, f"⏳ waiting_ci: task {task['id']}")
            elif mapped in ('failed', 'completed'):
                emoji = '🔴' if mapped == 'failed' else '✅'
                self.notifier.notify(self.repo, mapped, task['plan_id'], task['id'], run_id, origin, f"{emoji} {mapped}: task {task['id']}")
            elif mapped == 'waiting_review':
                self.notifier.notify(self.repo, 'failed', task['plan_id'], task['id'], run_id, origin, f"🟠 waiting_review: task {task['id']} missing required artifact")
        return mapped

    def complete_task(self, task_row, artifacts: list[dict] | None = None):
        task = dict(task_row)
        if artifacts is None:
            rows = self.repo.conn.execute('select artifact_type from artifacts where task_id=?', (task['id'],)).fetchall()
            artifacts = [dict(r) for r in rows]
        assert_required_artifacts(task, artifacts)
        self.repo.conn.execute("update tasks set status='done', completed_at=datetime('now') where id=?", (task['id'],))
        self.repo.conn.commit()
