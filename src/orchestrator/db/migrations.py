import sqlite3
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'migrations'


def connect(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def run_migrations(conn: sqlite3.Connection) -> list[str]:
    conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations (id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT NOT NULL UNIQUE, applied_at TEXT NOT NULL DEFAULT (datetime(\'now\')));')
    applied = {r['version'] for r in conn.execute('SELECT version FROM schema_migrations').fetchall()}
    newly = []
    for sql_path in sorted(MIGRATIONS_DIR.glob('*.sql')):
        version = sql_path.stem
        if version in applied:
            continue
        conn.executescript(sql_path.read_text())
        conn.execute('INSERT INTO schema_migrations(version) VALUES (?)', (version,))
        newly.append(version)
    conn.commit()
    return newly
