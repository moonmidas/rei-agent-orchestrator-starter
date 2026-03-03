import json
import os
from pathlib import Path


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get('OPENCLAW_HOME', str(Path.home())))


def load_config(path: str | None = None) -> dict:
    openclaw_home = resolve_openclaw_home()
    config_path = Path(path) if path else openclaw_home / '.openclaw' / 'orchestrator' / 'config.json'
    if config_path.exists():
        cfg = json.loads(config_path.read_text())
    else:
        cfg = {}

    db_path = cfg.get('database', {}).get('path', '${OPENCLAW_HOME}/.openclaw/orchestrator/orchestrator.db')
    db_path = db_path.replace('${OPENCLAW_HOME}', str(openclaw_home))

    cfg.setdefault('database', {})['path'] = db_path
    cfg.setdefault('openclawHome', str(openclaw_home))
    cfg.setdefault('routing', {}).setdefault('map', {'code': 'chad', 'default': 'chad'})
    cfg['routing'].setdefault('devFallbackAgent', 'chad')
    cfg.setdefault('merge', {}).setdefault('autoMerge', False)
    return cfg
