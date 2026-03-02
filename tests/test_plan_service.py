import tempfile
import unittest
from pathlib import Path

from src.orchestrator.db.migrations import connect, run_migrations
from src.orchestrator.db.repository import Repository
from src.orchestrator.plan_service import PlanService
from src.orchestrator.decompose import decompose_plan


class TestPlanService(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        conn = connect(str(Path(self.td.name) / 'o.db'))
        run_migrations(conn)
        self.conn = conn
        self.repo = Repository(conn)
        self.svc = PlanService(self.repo)

    def tearDown(self):
        self.td.cleanup()

    def test_execute_plan_persists_plan_and_tasks(self):
        plan_id, task_ids = self.svc.create_from_command('/execute-plan implement api. add tests. capture UI screenshot', 'thread-22')
        self.assertTrue(plan_id)
        self.assertGreaterEqual(len(task_ids), 2)
        count = self.conn.execute('select count(*) from tasks where plan_id=?', (plan_id,)).fetchone()[0]
        self.assertEqual(count, len(task_ids))

    def test_decompose_deterministic_order(self):
        tasks = decompose_plan('first step\nsecond step\nthird step')
        self.assertEqual([t.title for t in tasks], ['first step', 'second step', 'third step'])
        self.assertEqual(tasks[1].depends_on, [1])
        self.assertEqual(tasks[2].depends_on, [2])

    def test_approval_same_thread_gate(self):
        plan_id, _ = self.svc.create_from_command('/execute-plan write docs', 'thread-a')
        with self.assertRaises(ValueError):
            self.svc.approve(plan_id, 'thread-a', 'thread-b', 'u1')
        self.svc.approve(plan_id, 'thread-a', 'thread-a', 'u1')
        status = self.conn.execute('select status from plans where id=?', (plan_id,)).fetchone()[0]
        self.assertEqual(status, 'approved')


if __name__ == '__main__':
    unittest.main()
