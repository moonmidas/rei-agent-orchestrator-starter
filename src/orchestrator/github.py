import json
import subprocess
from dataclasses import dataclass


@dataclass
class GitHubClient:
    repo: str

    def _gh(self, *args: str) -> str:
        cp = subprocess.run(['gh', *args], check=True, capture_output=True, text=True)
        return cp.stdout.strip()

    def ensure_pr(self, branch: str, base: str = 'main', title: str | None = None, body: str = '') -> str:
        existing = self._gh('pr', 'list', '--repo', self.repo, '--head', branch, '--state', 'open', '--json', 'url')
        data = json.loads(existing or '[]')
        if data:
            return data[0]['url']

        if not title:
            title = f"Orchestrator task: {branch}"
        created = self._gh(
            'pr',
            'create',
            '--repo',
            self.repo,
            '--base',
            base,
            '--head',
            branch,
            '--title',
            title,
            '--body',
            body,
        )
        return created.splitlines()[-1].strip()

    def ci_checks_for_branch(self, branch: str) -> list[dict]:
        raw = self._gh('api', f'repos/{self.repo}/actions/runs?branch={branch}&per_page=20')
        data = json.loads(raw or '{}')
        checks = []
        for run in data.get('workflow_runs', []):
            status = run.get('status', 'queued')
            conclusion = run.get('conclusion')
            mapped = 'pending'
            if status == 'completed':
                mapped = 'success' if conclusion == 'success' else 'failed'
            checks.append(
                {
                    'id': str(run.get('id')),
                    'provider': 'github_actions',
                    'status': mapped,
                    'details': {
                        'name': run.get('name'),
                        'html_url': run.get('html_url'),
                        'conclusion': conclusion,
                        'status': status,
                    },
                }
            )
        if not checks:
            checks.append({'id': f'gha:{branch}:none', 'provider': 'github_actions', 'status': 'pending', 'details': {'reason': 'no_runs'}})
        return checks
