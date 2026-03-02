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


class DispatchError(RuntimeError):
    def __init__(self, message: str, command: list[str], raw: dict[str, Any] | None = None):
        super().__init__(message)
        self.command = command
        self.raw = raw or {}


def _replace_tokens(value: str, mapping: dict[str, str]) -> str:
    out = value
    for k, v in mapping.items():
        out = out.replace('{' + k + '}', v)
    return out


class OpenClawDispatchAdapter:
    def __init__(self, config: dict):
        self.config = config
        self._probed = False
        self._known_agents: set[str] = set()

    def _runtime_cfg(self) -> dict:
        return self.config.get('runtime', {}).get('openclawDispatch', {})

    def _canonical_command_template(self) -> list[str]:
        return self._runtime_cfg().get('command') or [
            'openclaw', 'agent',
            '--agent', '{agent}',
            '--session-id', 'orchestrator:{run_id}',
            '--message', '{dispatch_message}',
            '--json',
        ]

    def _build_command(self, task: dict, run_id: str, agent: str) -> list[str]:
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
        return [_replace_tokens(str(p), mapping) for p in self._canonical_command_template()]

    def probe_capabilities(self) -> None:
        if self._probed:
            return
        cp = subprocess.run(['openclaw', 'agents', 'list', '--json'], check=True, capture_output=True, text=True)
        parsed = self._parse_output(cp.stdout)
        agents = self._extract_agents(parsed)
        if not agents:
            raise ValueError('openclaw capability probe failed: no agents discovered from openclaw agents list --json')
        self._known_agents = agents
        self._probed = True

    def dispatch(self, task: dict, run_id: str, agent: str) -> DispatchResult:
        self.probe_capabilities()
        effective_agent = (agent or self.config.get('routing', {}).get('devFallbackAgent') or 'chad').strip() or 'chad'
        if effective_agent not in self._known_agents:
            raise DispatchError(
                f"dispatch blocked: agent '{effective_agent}' does not exist (known: {', '.join(sorted(self._known_agents))})",
                [],
                {'known_agents': sorted(self._known_agents), 'requested_agent': effective_agent},
            )

        cmd = self._build_command(task, run_id, effective_agent)
        try:
            cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raw_err = {
                'stdout': (e.stdout or '').strip(),
                'stderr': (e.stderr or '').strip(),
                'returncode': e.returncode,
            }
            raise DispatchError('openclaw dispatch command failed', cmd, raw_err) from e

        raw = self._parse_output(cp.stdout)
        session_key = self._extract_session_key(raw)
        if not session_key:
            raise DispatchError('openclaw dispatch output missing session key/session id', cmd, raw)
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
    def _extract_agents(raw: Any) -> set[str]:
        out: set[str] = set()

        def maybe_add(value: Any):
            if isinstance(value, str) and value.strip():
                out.add(value.strip())

        def walk(value: Any):
            if isinstance(value, dict):
                if 'agents' in value and isinstance(value['agents'], list):
                    for a in value['agents']:
                        if isinstance(a, dict):
                            maybe_add(a.get('id'))
                            maybe_add(a.get('name'))
                        else:
                            maybe_add(a)
                maybe_add(value.get('id'))
                maybe_add(value.get('name'))
                for v in value.values():
                    walk(v)
            elif isinstance(value, list):
                for v in value:
                    walk(v)

        walk(raw)
        return out

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
