#!/usr/bin/env python3
import argparse
from pathlib import Path

from .config import load_config
from .db.migrations import connect, run_migrations
from .db.repository import Repository
from .plan_service import PlanService
from .dispatch import DispatchEngine
from .watchdog import Watchdog
from .github import GitHubClient
from .screenshot import ScreenshotCapture


def _repo(args):
    cfg = load_config(args.config)
    conn = connect(cfg['database']['path'])
    run_migrations(conn)
    return cfg, conn, Repository(conn)


def cmd_migrate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    conn = connect(cfg['database']['path'])
    applied = run_migrations(conn)
    print(f"db={cfg['database']['path']}")
    print('applied=' + (','.join(applied) if applied else 'none'))
    return 0


def cmd_execute_plan(args: argparse.Namespace) -> int:
    _, _, repo = _repo(args)
    svc = PlanService(repo)
    plan_id, task_ids = svc.create_from_command(args.text, args.thread_id, args.message_id)
    print(f'plan_id={plan_id}')
    print(f'task_count={len(task_ids)}')
    print('status=awaiting_approval')
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    _, conn, repo = _repo(args)
    row = conn.execute('select source_thread_id from plans where id=?', (args.plan_id,)).fetchone()
    if not row:
        raise SystemExit('plan not found')
    svc = PlanService(repo)
    svc.approve(args.plan_id, row['source_thread_id'], args.thread_id, args.approver, args.text)
    print(f'plan_id={args.plan_id}')
    print('status=approved')
    return 0


def cmd_dispatch_next(args: argparse.Namespace) -> int:
    cfg, conn, repo = _repo(args)
    row = conn.execute("select * from tasks where plan_id=? and status='approved' order by sequence_no limit 1", (args.plan_id,)).fetchone()
    if not row:
        print('dispatch=noop')
        return 0
    gh = None
    if args.github_repo:
        gh = GitHubClient(args.github_repo)
    elif cfg.get('github', {}).get('repo'):
        gh = GitHubClient(cfg['github']['repo'])
    engine = DispatchEngine(repo, cfg, github_client=gh)
    run_id = engine.dispatch_task(row, args.branch, args.pr_url)
    print(f'run_id={run_id}')
    return 0


def cmd_ci_update(args: argparse.Namespace) -> int:
    cfg, _, repo = _repo(args)
    engine = DispatchEngine(repo, cfg)
    checks = [{'status': s.strip(), 'provider': 'manual'} for s in args.statuses.split(',') if s.strip()]
    state = engine.process_ci(args.run_id, checks)
    print(f'state={state}')
    return 0


def cmd_ci_poll(args: argparse.Namespace) -> int:
    cfg, conn, repo = _repo(args)
    run = conn.execute('select * from runs where id=?', (args.run_id,)).fetchone()
    if not run:
        raise SystemExit('run not found')
    branch = args.branch or run['branch_name']
    if not branch:
        raise SystemExit('branch is required for ci-poll')
    gh_repo = args.github_repo or cfg.get('github', {}).get('repo')
    if not gh_repo:
        raise SystemExit('github repo required via --github-repo or config.github.repo')
    gh = GitHubClient(gh_repo)
    checks = gh.ci_checks_for_branch(branch)
    engine = DispatchEngine(repo, cfg)
    state = engine.process_ci(args.run_id, checks)
    print(f'state={state}')
    return 0


def cmd_capture_screenshot(args: argparse.Namespace) -> int:
    cfg, _, repo = _repo(args)
    row = repo.conn.execute('select * from tasks where id=?', (args.task_id,)).fetchone()
    if not row:
        raise SystemExit('task not found')
    command_tmpl = args.command_template or cfg.get('screenshot', {}).get('command', 'npx playwright screenshot {url} {output}')
    out_dir = Path(args.output_dir or (Path(cfg['openclawHome']) / 'orchestrator' / 'artifacts'))
    out_path = out_dir / f"{args.task_id}.png"
    result = ScreenshotCapture(command_tmpl).capture(args.url, str(out_path))
    artifact_id = repo.add_artifact(args.task_id, 'screenshot', result['path'], args.run_id, metadata=result)
    print(f'artifact_id={artifact_id}')
    print(f'path={result["path"]}')
    return 0


def cmd_worker_tick(args: argparse.Namespace) -> int:
    _, _, repo = _repo(args)
    wd = Watchdog(repo, stale_minutes=args.stale_minutes)
    count = wd.run_tick()
    print(f'stale_processed={count}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog='orchestrator')
    sub = parser.add_subparsers(dest='command', required=True)

    m = sub.add_parser('migrate')
    m.add_argument('--config')
    m.set_defaults(func=cmd_migrate)

    ex = sub.add_parser('execute-plan')
    ex.add_argument('--config')
    ex.add_argument('--text', required=True)
    ex.add_argument('--thread-id', required=True)
    ex.add_argument('--message-id')
    ex.set_defaults(func=cmd_execute_plan)

    ap = sub.add_parser('approve')
    ap.add_argument('--config')
    ap.add_argument('--plan-id', required=True)
    ap.add_argument('--thread-id', required=True)
    ap.add_argument('--approver', required=True)
    ap.add_argument('--text', default='approve')
    ap.set_defaults(func=cmd_approve)

    dn = sub.add_parser('dispatch-next')
    dn.add_argument('--config')
    dn.add_argument('--plan-id', required=True)
    dn.add_argument('--branch')
    dn.add_argument('--pr-url')
    dn.add_argument('--github-repo')
    dn.set_defaults(func=cmd_dispatch_next)

    cu = sub.add_parser('ci-update')
    cu.add_argument('--config')
    cu.add_argument('--run-id', required=True)
    cu.add_argument('--statuses', required=True, help='comma-separated: pending,success,failed')
    cu.set_defaults(func=cmd_ci_update)

    cp = sub.add_parser('ci-poll')
    cp.add_argument('--config')
    cp.add_argument('--run-id', required=True)
    cp.add_argument('--branch')
    cp.add_argument('--github-repo')
    cp.set_defaults(func=cmd_ci_poll)

    ss = sub.add_parser('capture-screenshot')
    ss.add_argument('--config')
    ss.add_argument('--task-id', required=True)
    ss.add_argument('--run-id')
    ss.add_argument('--url', required=True)
    ss.add_argument('--output-dir')
    ss.add_argument('--command-template')
    ss.set_defaults(func=cmd_capture_screenshot)

    wt = sub.add_parser('worker-tick')
    wt.add_argument('--config')
    wt.add_argument('--stale-minutes', type=int, default=5)
    wt.set_defaults(func=cmd_worker_tick)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
