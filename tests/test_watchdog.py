import tempfile
import unittest
from pathlib import Path

from src.orchestrator.config import load_config
from src.orchestrator.db.migrations import connect, run_migrations
from src.orchestrator.db.repository import Repository
from src.orchestrator.dispatch import DispatchEngine
from src.orchestrator.watchdog import Watchdog


class _FakeDispatchAdapter:
    def dispatch(self, task, run_id, agent):
        class R:
            session_key = f'session-{run_id}'
            command = ['openclaw', 'sessions', 'spawn']
            raw = {'session_key': session_key}
        return R()

    @staticmethod
    def command_for_log(cmd):
        return ' '.join(cmd)


class TestWatchdog(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.conn = connect(str(Path(self.td.name) / 'o.db'))
        run_migrations(self.conn)
        self.repo = Repository(self.conn)
        self.plan = self.repo.create_plan('th', '/execute-plan code', 'code')
        self.task = self.repo.create_task(self.plan, 'Implement code', 'code', 1)
        self.repo.approve_plan(self.plan, 'u1', 'th', 'approve')
        self.engine = DispatchEngine(self.repo, load_config(None), {'chad'}, dispatch_adapter=_FakeDispatchAdapter())
        self.run = self.engine.dispatch_task(self.conn.execute('select * from tasks where id=?', (self.task,)).fetchone(), 'b', 'https://pr')

    def tearDown(self):
        self.td.cleanup()

    def test_retry_once_then_escalate(self):
        self.conn.execute("update runs set heartbeat_at=datetime('now','-10 minutes') where id=?", (self.run,))
        self.conn.commit()
        wd = Watchdog(self.repo, stale_minutes=1)
        wd.run_tick()
        state = self.conn.execute('select state from runs where id=?', (self.run,)).fetchone()[0]
        self.assertEqual(state, 'retrying')

        self.conn.execute("update runs set heartbeat_at=datetime('now','-10 minutes') where id=?", (self.run,))
        self.conn.commit()
        wd.run_tick()
        state2 = self.conn.execute('select state from runs where id=?', (self.run,)).fetchone()[0]
        self.assertEqual(state2, 'escalated')


if __name__ == '__main__':
    unittest.main()
