import unittest

from src.orchestrator.routing import resolve_agent


class TestRouting(unittest.TestCase):
    def test_code_falls_back_to_chad_if_mapped_agent_missing(self):
        cfg = {'routing': {'map': {'code': 'missing'}, 'devFallbackAgent': 'chad'}}
        agent = resolve_agent({'work_type': 'code'}, cfg, {'chad'})
        self.assertEqual(agent, 'chad')

    def test_non_code_missing_agent_errors(self):
        cfg = {'routing': {'map': {'content': 'missing'}, 'devFallbackAgent': 'chad'}}
        with self.assertRaises(ValueError):
            resolve_agent({'work_type': 'content'}, cfg, {'chad'})


if __name__ == '__main__':
    unittest.main()
