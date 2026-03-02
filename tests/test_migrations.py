import os
import tempfile
import unittest
from pathlib import Path

from src.orchestrator.db.migrations import connect, run_migrations


class TestMigrations(unittest.TestCase):
    def test_fresh_db_creates_core_tables(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / 'orchestrator.db'
            conn = connect(str(db))
            applied = run_migrations(conn)
            self.assertTrue(applied)
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            for required in {'plans', 'tasks', 'runs', 'approvals', 'events', 'artifacts', 'ci_checks'}:
                self.assertIn(required, tables)


if __name__ == '__main__':
    unittest.main()
