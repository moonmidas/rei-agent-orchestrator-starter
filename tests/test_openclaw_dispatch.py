import subprocess
import unittest
from unittest.mock import patch

from src.orchestrator.openclaw_dispatch import OpenClawDispatchAdapter


class TestOpenClawDispatchAdapter(unittest.TestCase):
    def test_default_command_uses_openclaw_agent(self):
        adapter = OpenClawDispatchAdapter(config={})
        cmd = adapter._build_command(
            task={'id': 't1', 'plan_id': 'p1', 'title': 'Implement API'},
            run_id='run-1',
            agent='chad',
        )
        self.assertEqual(cmd[:2], ['openclaw', 'agent'])
        self.assertIn('--session-id', cmd)
        self.assertIn('orchestrator:run-1', cmd)
        self.assertIn('--json', cmd)
        self.assertIn('--message', cmd)

    def test_dispatch_parses_nested_session_id_from_json(self):
        adapter = OpenClawDispatchAdapter(config={})
        cp = subprocess.CompletedProcess(
            args=['openclaw'],
            returncode=0,
            stdout='{"status":"ok","result":{"meta":{"agentMeta":{"sessionId":"sess-123"}}}}',
            stderr='',
        )
        with patch('src.orchestrator.openclaw_dispatch.subprocess.run', return_value=cp):
            result = adapter.dispatch({'id': 't1', 'plan_id': 'p1', 'title': 'x'}, 'run-1', 'chad')
        self.assertEqual(result.session_key, 'sess-123')

    def test_dispatch_parses_key_value_output(self):
        adapter = OpenClawDispatchAdapter(config={
            'runtime': {
                'openclawDispatch': {
                    'command': ['openclaw', 'agent', '--agent', '{agent}', '--message', 'x']
                }
            }
        })
        cp = subprocess.CompletedProcess(
            args=['openclaw'],
            returncode=0,
            stdout='run_id=abc\nsession_key=session-42\n',
            stderr='',
        )
        with patch('src.orchestrator.openclaw_dispatch.subprocess.run', return_value=cp):
            result = adapter.dispatch({'id': 't1', 'plan_id': 'p1', 'title': 'x'}, 'run-1', 'chad')
        self.assertEqual(result.session_key, 'session-42')


if __name__ == '__main__':
    unittest.main()
