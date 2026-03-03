import json
import os
import tempfile
import unittest
from pathlib import Path

from src.orchestrator.config import load_config


class TestConfigDefaults(unittest.TestCase):
    def test_default_database_path_uses_openclaw_home_dotopenclaw(self):
        with tempfile.TemporaryDirectory() as td:
            prev = os.environ.get('OPENCLAW_HOME')
            os.environ['OPENCLAW_HOME'] = td
            try:
                cfg = load_config(None)
            finally:
                if prev is None:
                    os.environ.pop('OPENCLAW_HOME', None)
                else:
                    os.environ['OPENCLAW_HOME'] = prev

            expected = str(Path(td) / '.openclaw' / 'orchestrator' / 'orchestrator.db')
            self.assertEqual(cfg['database']['path'], expected)

    def test_example_template_db_path_matches_runtime_default(self):
        template_path = Path(__file__).resolve().parent.parent / 'templates' / 'orchestrator.config.example.json'
        template = json.loads(template_path.read_text())
        self.assertEqual(
            template['database']['path'],
            '${OPENCLAW_HOME}/.openclaw/orchestrator/orchestrator.db',
        )


if __name__ == '__main__':
    unittest.main()
