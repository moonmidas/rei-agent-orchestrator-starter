import json
import subprocess


class MilestoneNotifier:
    def __init__(self, config: dict):
        self.config = config

    def _send_command(self, thread_id: str, message: str) -> list[str]:
        cfg = self.config.get('discord', {}).get('milestones', {})
        cmd = cfg.get('sendCommand') or [
            'openclaw', 'message', 'send',
            '--channel', 'discord',
            '--target', '{thread_id}',
            '--message', '{message}',
        ]
        out = []
        for c in cmd:
            out.append(str(c).replace('{thread_id}', thread_id).replace('{message}', message))
        return out

    def notify(self, repo, event_type: str, plan_id: str | None, task_id: str | None, run_id: str | None, origin_thread_id: str | None, text: str):
        if not origin_thread_id:
            return
        cfg = self.config.get('discord', {}).get('milestones', {})
        target = cfg.get('targetThreadId') or origin_thread_id
        dedupe_key = f"milestone:{target}:{event_type}:{run_id or task_id or plan_id}"
        existing = repo.conn.execute('select 1 from events where event_type=? limit 1', (dedupe_key,)).fetchone()
        if existing:
            return
        cmd = self._send_command(target, text)
        error = None
        try:
            cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
            response = {'stdout': cp.stdout.strip(), 'stderr': cp.stderr.strip()}
        except subprocess.CalledProcessError as e:
            error = {'stdout': (e.stdout or '').strip(), 'stderr': (e.stderr or '').strip(), 'returncode': e.returncode}
            response = {}
        repo.add_event(dedupe_key, {'target': target, 'text': text, 'response': response, 'error': error}, plan_id=plan_id, task_id=task_id, run_id=run_id)
