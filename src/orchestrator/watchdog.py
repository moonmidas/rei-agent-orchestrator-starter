from datetime import datetime, timedelta, timezone


def _dt(s: str | None):
    if not s:
        return None
    return datetime.fromisoformat(s.replace(' ', 'T'))


class Watchdog:
    def __init__(self, repo, stale_minutes: int = 5):
        self.repo = repo
        self.stale_minutes = stale_minutes

    def run_tick(self):
        stale = []
        rows = self.repo.conn.execute("select * from runs where state in ('running','waiting_ci','retrying')").fetchall()
        now = datetime.now(timezone.utc)
        for r in rows:
            hb = _dt(r['heartbeat_at'])
            if hb is None:
                continue
            age = now - hb.replace(tzinfo=timezone.utc)
            if age > timedelta(minutes=self.stale_minutes):
                stale.append(r)

        for r in stale:
            if r['attempt'] < 2:
                self.repo.conn.execute("update runs set attempt=attempt+1, state='retrying', heartbeat_at=datetime('now') where id=?", (r['id'],))
                self.repo.add_event('run.retry', {'attempt': r['attempt'] + 1}, run_id=r['id'], task_id=r['task_id'])
            else:
                self.repo.conn.execute("update runs set state='escalated', heartbeat_at=datetime('now') where id=?", (r['id'],))
                self.repo.add_event('run.escalated', {'reason': 'stale'}, run_id=r['id'], task_id=r['task_id'])
        self.repo.conn.commit()
        return len(stale)
