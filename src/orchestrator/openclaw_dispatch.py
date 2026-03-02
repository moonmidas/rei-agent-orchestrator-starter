import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any


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
            'openclaw', 'agent',
            '--agent', '{agent}',
            '--session-id', 'orchestrator:{run_id}',
            '--message', '{dispatch_message}',
            '--json',
        ]
        mapping = {
            'agent': agent,
            'run_id': run_id,
            'task_id': str(task['id']),
            'plan_id': str(task['plan_id']),
            'title': str(task.get('title') or ''),
            'description': str(task.get('description') or ''),
            'dispatch_message': (
                'orchestrator dispatch '
                f"run_id={run_id} task_id={task['id']} plan_id={task['plan_id']} "
                f"title={str(task.get('title') or '').strip()}"
            ).strip(),
        }
        return [_replace_tokens(str(p), mapping) for p in base]

    def dispatch(self, task: dict, run_id: str, agent: str) -> DispatchResult:
        cmd = self._build_command(task, run_id, agent)
        cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
        raw = self._parse_output(cp.stdout)
        session_key = self._extract_session_key(raw)
        if not session_key:
            raise ValueError('openclaw dispatch output missing session key/session id')
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

        out: dict[str, Any] = {}
        json_lines: list[Any] = []
        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                out[k.strip()] = v.strip()
                continue
            try:
                json_lines.append(json.loads(line))
            except json.JSONDecodeError:
                pass

        if json_lines:
            out['json_lines'] = json_lines
        if out:
            return out
        return {'stdout': txt}

    @staticmethod
    def _extract_session_key(raw: Any) -> str | None:
        preferred_keys = ('session_key', 'sessionKey', 'session_id', 'sessionId')
        fallback_keys = ('session', 'sessionID', 'id')

        def walk(value: Any) -> str | None:
            if isinstance(value, dict):
                for key in preferred_keys:
                    if key in value and value[key]:
                        return str(value[key])
                for key in fallback_keys:
                    if key in value and value[key] and key != 'id':
                        return str(value[key])
                for key in fallback_keys:
                    if key == 'id' and key in value and value[key]:
                        return str(value[key])
                for item in value.values():
                    found = walk(item)
                    if found:
                        return found
            elif isinstance(value, list):
                for item in value:
                    found = walk(item)
                    if found:
                        return found
            return None

        return walk(raw)

    @staticmethod
    def command_for_log(cmd: list[str]) -> str:
        return ' '.join(shlex.quote(c) for c in cmd)
