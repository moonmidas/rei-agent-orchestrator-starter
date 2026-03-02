import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.orchestrator.db.migrations import connect, run_migrations
from src.orchestrator.db.repository import Repository
from src.orchestrator.notifications import MilestoneNotifier


class _CP:
    def __init__(self):
        self.stdout = '{}'
        self.stderr = ''


class TestMilestoneNotifier(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.conn = connect(str(Path(self.td.name) / 'o.db'))
        run_migrations(self.conn)
        self.repo = Repository(self.conn)
        self.plan_id = self.repo.create_plan('thread-1', '/execute-plan x', 'x')
        self.task_id = self.repo.create_task(self.plan_id, 'T', 'other', 1)
        self.run_id = self.repo.create_run(self.task_id, 'chad', 'd1')
        self.notifier = MilestoneNotifier({})

    def tearDown(self):
        self.td.cleanup()

    def test_dedupe_key_avoids_duplicate_posts(self):
        with patch('src.orchestrator.notifications.subprocess.run', return_value=_CP()) as run:
            self.notifier.notify(self.repo, 'queued', self.plan_id, self.task_id, self.run_id, 'thread-1', 'hello')
            self.notifier.notify(self.repo, 'queued', self.plan_id, self.task_id, self.run_id, 'thread-1', 'hello')
        self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
