#!/usr/bin/env python3
import argparse
from .config import load_config
from .db.migrations import connect, run_migrations


def cmd_migrate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    conn = connect(cfg['database']['path'])
    applied = run_migrations(conn)
    print(f"db={cfg['database']['path']}")
    print('applied=' + (','.join(applied) if applied else 'none'))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog='orchestrator')
    sub = parser.add_subparsers(dest='command', required=True)

    m = sub.add_parser('migrate')
    m.add_argument('--config')
    m.set_defaults(func=cmd_migrate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
