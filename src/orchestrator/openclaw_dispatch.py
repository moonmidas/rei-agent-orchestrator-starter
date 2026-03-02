import json
import shlex
import subprocess
from dataclasses import dataclass


@dataclass
class DispatchResult:
    session_key: str
    command: list[str]
    raw: dict


def _replace_tokens(value: str, mapping: dict[str, str]) -> str:
    out = value
    for k, v in mapping.items():
        out = out.replace('{' + k + '}', v)
    return out


class OpenClawDispatchAdapter:
    def __init__(self, config: dict):
        self.config = config

    def _build_command(self, task: dict, run_id: str, agent: str) -> list[str]:
        runtime_cfg = self.config.get('runtime', {}).get('openclawDispatch', {})
        base = runtime_cfg.get('command') or [
            'openclaw', 'sessions', 'spawn',
            '--agent', '{agent}',
            '--label', 'orchestrator:{run_id}',
            '--task-id', '{task_id}',
            '--plan-id', '{plan_id}',
        ]
        mapping = {
            'agent': agent,
            'run_id': run_id,
            'task_id': str(task['id']),
            'plan_id': str(task['plan_id']),
            'title': str(task.get('title') or ''),
            'description': str(task.get('description') or ''),
        }
        return [_replace_tokens(str(p), mapping) for p in base]

    def dispatch(self, task: dict, run_id: str, agent: str) -> DispatchResult:
        cmd = self._build_command(task, run_id, agent)
        cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
        raw = self._parse_output(cp.stdout)
        session_key = raw.get('session_key') or raw.get('sessionKey') or raw.get('id')
        if not session_key:
            raise ValueError('openclaw dispatch output missing session key')
        return DispatchResult(session_key=str(session_key), command=cmd, raw=raw)

    @staticmethod
    def _parse_output(stdout: str) -> dict:
        txt = stdout.strip()
        if not txt:
            return {}
        try:
            parsed = json.loads(txt)
            if isinstance(parsed, dict):
                return parsed
            return {'result': parsed}
        except json.JSONDecodeError:
            pass

        out = {}
        for line in txt.splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                out[k.strip()] = v.strip()
        if out:
            return out
        return {'stdout': txt}

    @staticmethod
    def command_for_log(cmd: list[str]) -> str:
        return ' '.join(shlex.quote(c) for c in cmd)
