import json
import unittest
from unittest.mock import patch

from src.orchestrator.github import GitHubClient


class TestGitHubClient(unittest.TestCase):
    @patch('src.orchestrator.github.subprocess.run')
    def test_ensure_pr_returns_existing(self, mrun):
        mrun.return_value.stdout = json.dumps([{'url': 'https://github.com/a/b/pull/1'}])
        cli = GitHubClient('a/b')
        self.assertEqual(cli.ensure_pr('task/x'), 'https://github.com/a/b/pull/1')

    @patch('src.orchestrator.github.subprocess.run')
    def test_ci_checks_mapping(self, mrun):
        payload = {
            'workflow_runs': [
                {'id': 1, 'name': 'ci', 'status': 'in_progress', 'conclusion': None, 'html_url': 'u1'},
                {'id': 2, 'name': 'ci2', 'status': 'completed', 'conclusion': 'success', 'html_url': 'u2'},
            ]
        }
        mrun.return_value.stdout = json.dumps(payload)
        cli = GitHubClient('a/b')
        checks = cli.ci_checks_for_branch('task/x')
        self.assertEqual(checks[0]['status'], 'pending')
        self.assertEqual(checks[1]['status'], 'success')


if __name__ == '__main__':
    unittest.main()
