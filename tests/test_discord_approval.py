import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.orchestrator.db.migrations import connect, run_migrations
from src.orchestrator.db.repository import Repository
from src.orchestrator.discord_approval import DiscordApprovalBridge


class _CP:
    def __init__(self, out: str):
        self.stdout = out


class TestDiscordApprovalBridge(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.conn = connect(str(Path(self.td.name) / 'o.db'))
        run_migrations(self.conn)
        self.repo = Repository(self.conn)
        self.plan_id = self.repo.create_plan('thread-a', '/execute-plan ship it', 'ship it')

    def tearDown(self):
        self.td.cleanup()

    def test_approves_from_same_thread_message(self):
        bridge = DiscordApprovalBridge({'discord': {'approval': {'keywords': ['approve']}}})
        payload = '[{"id":"m1","thread_id":"thread-a","author_id":"u1","content":"approve please"}]'
        with patch('subprocess.run', return_value=_CP(payload)):
            res = bridge.poll_and_resolve(self.repo, self.plan_id, 'thread-a', 'thread-a')
        self.assertTrue(res.approved)
        status = self.conn.execute('select status from plans where id=?', (self.plan_id,)).fetchone()[0]
        self.assertEqual(status, 'approved')

    def test_ignores_other_thread(self):
        bridge = DiscordApprovalBridge({'discord': {'approval': {'keywords': ['approve']}}})
        payload = '[{"id":"m1","thread_id":"thread-b","author_id":"u1","content":"approve"}]'
        with patch('subprocess.run', return_value=_CP(payload)):
            res = bridge.poll_and_resolve(self.repo, self.plan_id, 'thread-a', 'thread-a')
        self.assertFalse(res.approved)


if __name__ == '__main__':
    unittest.main()
