import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.orchestrator.cli import cmd_capture_screenshot
from src.orchestrator.screenshot import ScreenshotCapture


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, task_row):
        self.task_row = task_row

    def execute(self, *_args, **_kwargs):
        return _FakeCursor(self.task_row)


class _FakeRepo:
    def __init__(self, task_row):
        self.conn = _FakeConn(task_row)
        self.artifacts = []

    def add_artifact(self, task_id, artifact_type, path, run_id=None, metadata=None):
        self.artifacts.append(
            {
                'task_id': task_id,
                'artifact_type': artifact_type,
                'path': path,
                'run_id': run_id,
                'metadata': metadata or {},
            }
        )
        return 'artifact_test'


class TestScreenshotCapture(unittest.TestCase):
    @patch('src.orchestrator.screenshot.subprocess.run')
    def test_capture_runs_command_and_returns_metadata(self, mrun):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'a.png'
            out.write_bytes(b'1234')
            cap = ScreenshotCapture('echo take {url} {output}')
            data = cap.capture('https://example.com', str(out))
            self.assertEqual(data['path'], str(out))
            self.assertEqual(data['size_bytes'], 4)
            mrun.assert_called_once()

    @patch('src.orchestrator.cli.ScreenshotCapture.capture')
    @patch('src.orchestrator.cli._repo')
    def test_cli_default_output_dir_uses_dotopenclaw_artifacts(self, m_repo, m_capture):
        with tempfile.TemporaryDirectory() as td:
            fake_repo = _FakeRepo(task_row={'id': 'task_1'})
            cfg = {'openclawHome': td, 'screenshot': {'command': 'echo {url} {output}'}}
            m_repo.return_value = (cfg, None, fake_repo)

            expected_path = Path(td) / '.openclaw' / 'orchestrator' / 'artifacts' / 'task_1.png'
            m_capture.return_value = {'path': str(expected_path), 'size_bytes': 1}

            rc = cmd_capture_screenshot(
                SimpleNamespace(
                    config=None,
                    task_id='task_1',
                    run_id='run_1',
                    url='https://example.com',
                    output_dir=None,
                    command_template=None,
                )
            )

            self.assertEqual(rc, 0)
            m_capture.assert_called_once_with('https://example.com', str(expected_path))
            self.assertEqual(fake_repo.artifacts[0]['path'], str(expected_path))


if __name__ == '__main__':
    unittest.main()
