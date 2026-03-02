def aggregate_ci(checks: list[dict]) -> str:
    statuses = {c.get('status', 'pending') for c in checks}
    if 'failed' in statuses:
        return 'failed'
    if statuses == {'success'}:
        return 'success'
    return 'pending'
