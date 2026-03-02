import json
import subprocess
from dataclasses import dataclass

from .approval import ensure_same_thread


@dataclass
class ApprovalIngestResult:
    approved: bool
    approver_id: str | None = None
    message_id: str | None = None
    approval_text: str | None = None


class DiscordApprovalBridge:
    def __init__(self, config: dict):
        self.config = config

    def _keywords(self) -> list[str]:
        kws = self.config.get('discord', {}).get('approval', {}).get('keywords', ['approve', '/approve', 'lgtm'])
        return [k.lower() for k in kws]

    def _fetch_command(self, thread_id: str, limit: int) -> list[str]:
        cfg = self.config.get('discord', {}).get('approval', {})
        cmd = cfg.get('fetchCommand') or [
            'openclaw', 'message', 'read',
            '--target', '{thread_id}',
            '--limit', '{limit}',
            '--channel', 'discord',
        ]
        return [str(x).replace('{thread_id}', thread_id).replace('{limit}', str(limit)) for x in cmd]

    def _parse_messages(self, stdout: str) -> list[dict]:
        txt = stdout.strip()
        if not txt:
            return []
        try:
            data = json.loads(txt)
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict)]
            if isinstance(data, dict):
                if isinstance(data.get('messages'), list):
                    return [d for d in data['messages'] if isinstance(d, dict)]
                return [data]
        except json.JSONDecodeError:
            pass
        out = []
        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    out.append(obj)
            except json.JSONDecodeError:
                continue
        return out

    def poll_and_resolve(self, repo, plan_id: str, source_thread_id: str, thread_id: str, limit: int = 25) -> ApprovalIngestResult:
        ensure_same_thread(source_thread_id, thread_id)
        cmd = self._fetch_command(thread_id, limit)
        cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
        messages = self._parse_messages(cp.stdout)
        if not messages:
            return ApprovalIngestResult(approved=False)

        keywords = self._keywords()
        for m in messages:
            msg_thread = str(m.get('thread_id') or m.get('threadId') or m.get('channel_id') or m.get('channelId') or '')
            if msg_thread and msg_thread != source_thread_id:
                continue
            text = str(m.get('content') or m.get('text') or '').strip()
            if not text:
                continue
            low = text.lower()
            if not any(k in low for k in keywords):
                continue
            approver = str(m.get('author_id') or m.get('authorId') or m.get('user_id') or 'unknown')
            repo.approve_plan(plan_id, approver, source_thread_id, text)
            repo.add_event('plan.approved.discord', {
                'approver_id': approver,
                'approval_message_id': m.get('id') or m.get('message_id'),
            }, plan_id=plan_id)
            return ApprovalIngestResult(
                approved=True,
                approver_id=approver,
                message_id=str(m.get('id') or m.get('message_id') or ''),
                approval_text=text,
            )
        return ApprovalIngestResult(approved=False)
