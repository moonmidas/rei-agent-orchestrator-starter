#!/usr/bin/env python3
import argparse

from .config import load_config
from .db.migrations import connect, run_migrations
from .db.repository import Repository
from .plan_service import PlanService
from .dispatch import DispatchEngine


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
    engine = DispatchEngine(repo, cfg)
    run_id = engine.dispatch_task(row, args.branch, args.pr_url)
    print(f'run_id={run_id}')
    return 0


def cmd_ci_update(args: argparse.Namespace) -> int:
    cfg, _, repo = _repo(args)
    engine = DispatchEngine(repo, cfg)
    checks = [{'status': s.strip()} for s in args.statuses.split(',') if s.strip()]
    state = engine.process_ci(args.run_id, checks)
    print(f'state={state}')
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
    dn.set_defaults(func=cmd_dispatch_next)

    cu = sub.add_parser('ci-update')
    cu.add_argument('--config')
    cu.add_argument('--run-id', required=True)
    cu.add_argument('--statuses', required=True, help='comma-separated: pending,success,failed')
    cu.set_defaults(func=cmd_ci_update)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
