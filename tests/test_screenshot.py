import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.orchestrator.screenshot import ScreenshotCapture


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


if __name__ == '__main__':
    unittest.main()
