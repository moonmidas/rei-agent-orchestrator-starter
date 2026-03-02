import tempfile
import unittest
from pathlib import Path

from src.orchestrator.config import load_config
from src.orchestrator.db.migrations import connect, run_migrations
from src.orchestrator.db.repository import Repository
from src.orchestrator.dispatch import DispatchEngine


class _FakeGitHub:
    def ensure_pr(self, branch, base='main', title=None, body=''):
        return f'https://github.com/o/r/pull/{branch.split("/")[-1]}'


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.conn = connect(str(Path(self.td.name) / 'o.db'))
        run_migrations(self.conn)
        self.repo = Repository(self.conn)
        self.plan = self.repo.create_plan('th', '/execute-plan code and ui', 'code and ui')
        self.code_task = self.repo.create_task(self.plan, 'Implement code', 'code', 1)
        self.ui_task = self.repo.create_task(self.plan, 'Update UI', 'ui', 2)
        self.repo.approve_plan(self.plan, 'u1', 'th', 'approve')
        self.cfg = load_config(None)
        self.engine = DispatchEngine(self.repo, self.cfg, {'chad'})

    def tearDown(self):
        self.td.cleanup()

    def _task(self, task_id):
        return self.conn.execute('select * from tasks where id=?', (task_id,)).fetchone()

    def test_code_requires_branch_and_pr(self):
        with self.assertRaisesRegex(ValueError, 'branch creation'):
            self.engine.dispatch_task(self._task(self.code_task))
        run = self.engine.dispatch_task(self._task(self.code_task), branch_name='task/code', pr_url='https://example/pr/1')
        self.assertTrue(run)

    def test_code_pr_autocreation_via_github(self):
        engine = DispatchEngine(self.repo, self.cfg, {'chad'}, github_client=_FakeGitHub())
        run = engine.dispatch_task(self._task(self.code_task), branch_name='task/code')
        task = self.conn.execute('select pr_url from tasks where id=?', (self.code_task,)).fetchone()
        self.assertIn('github.com', task['pr_url'])
        self.assertTrue(run)

    def test_ci_polling_transition(self):
        run = self.engine.dispatch_task(self._task(self.code_task), branch_name='task/code', pr_url='https://example/pr/1')
        self.assertEqual(self.engine.process_ci(run, [{'status': 'pending', 'provider': 'gha', 'id': '1'}]), 'waiting_ci')
        self.assertEqual(self.engine.process_ci(run, [{'status': 'success', 'provider': 'gha', 'id': '1'}]), 'completed')
        status = self.conn.execute('select status from tasks where id=?', (self.code_task,)).fetchone()[0]
        self.assertEqual(status, 'done')

    def test_ui_requires_screenshot_artifact(self):
        run = self.engine.dispatch_task(self._task(self.ui_task))
        with self.assertRaises(ValueError):
            self.engine.complete_task(self._task(self.ui_task), [])
        self.repo.add_artifact(self.ui_task, 'screenshot', '/tmp/shot.png', run)
        self.engine.complete_task(self._task(self.ui_task))
        status = self.conn.execute('select status from tasks where id=?', (self.ui_task,)).fetchone()[0]
        self.assertEqual(status, 'done')

    def test_dispatch_idempotency_dedupe_key(self):
        row = self._task(self.ui_task)
        run1 = self.engine.dispatch_task(row)
        run2 = self.engine.dispatch_task(row)
        self.assertEqual(run1, run2)


if __name__ == '__main__':
    unittest.main()
