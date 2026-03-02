import re
from dataclasses import dataclass


@dataclass
class DecomposedTask:
    title: str
    description: str
    work_type: str
    depends_on: list[int]


def infer_work_type(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ['ui', 'screenshot', 'playwright', 'frontend', 'page']):
        return 'ui'
    if any(k in t for k in ['code', 'refactor', 'implement', 'api', 'test', 'build']):
        return 'code'
    if any(k in t for k in ['docs', 'copy', 'blog', 'content']):
        return 'content'
    if any(k in t for k in ['deploy', 'infra', 'ops', 'cron', 'timer']):
        return 'ops'
    return 'other'


def decompose_plan(plan_text: str) -> list[DecomposedTask]:
    lines = [l.strip('-* \t') for l in re.split(r'\r?\n+', plan_text) if l.strip()]
    if len(lines) <= 1:
        chunks = [c.strip() for c in re.split(r'\s*(?:;|\.| then )\s*', plan_text) if c.strip()]
        lines = chunks or [plan_text.strip()]
    tasks: list[DecomposedTask] = []
    for i, line in enumerate(lines):
        tasks.append(
            DecomposedTask(
                title=line[:120],
                description=line,
                work_type=infer_work_type(line),
                depends_on=[i] if i > 0 else [],
                # deterministic sequence dependency: each task waits on prior index

            )
        )
    return tasks
