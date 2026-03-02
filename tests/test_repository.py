import tempfile
import unittest
from pathlib import Path

from src.orchestrator.db.migrations import connect, run_migrations
from src.orchestrator.db.repository import Repository


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        db = Path(self.td.name) / 'o.db'
        self.conn = connect(str(db))
        run_migrations(self.conn)
        self.repo = Repository(self.conn)

    def tearDown(self):
        self.td.cleanup()

    def test_plan_task_approval_run_lifecycle(self):
        plan = self.repo.create_plan('thread-1', '/execute-plan do thing', 'do thing')
        task = self.repo.create_task(plan, 'Implement', 'code', 1)
        self.repo.approve_plan(plan, 'user-1', 'thread-1', 'approve')

        pstate = self.conn.execute('select status from plans where id=?', (plan,)).fetchone()[0]
        tstate = self.conn.execute('select status from tasks where id=?', (task,)).fetchone()[0]
        self.assertEqual(pstate, 'approved')
        self.assertEqual(tstate, 'approved')

        run = self.repo.create_run(task, 'chad', 'dedupe-1')
        self.repo.update_run_state(run, 'running')
        rstate = self.conn.execute('select state from runs where id=?', (run,)).fetchone()[0]
        self.assertEqual(rstate, 'running')

        self.repo.add_event('run.state_changed', {'state': 'running'}, run_id=run, task_id=task, plan_id=plan)
        self.repo.add_artifact(task, 'log', '/tmp/log.txt', run_id=run)
        ev_count = self.conn.execute('select count(*) from events').fetchone()[0]
        art_count = self.conn.execute('select count(*) from artifacts').fetchone()[0]
        self.assertEqual(ev_count, 1)
        self.assertEqual(art_count, 1)


if __name__ == '__main__':
    unittest.main()
