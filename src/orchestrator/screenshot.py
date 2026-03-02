import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScreenshotCapture:
    command_template: str

    def capture(self, url: str, output_path: str) -> dict:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = self.command_template.format(url=url, output=str(out))
        subprocess.run(shlex.split(cmd), check=True, capture_output=True, text=True)
        return {'path': str(out), 'size_bytes': out.stat().st_size if out.exists() else 0, 'command': cmd, 'url': url}
