def resolve_agent(task: dict, config: dict, available_agents: set[str]) -> str:
    if task.get('target_agent') and config.get('routing', {}).get('allowTargetOverride', True):
        return task['target_agent']

    wtype = task.get('work_type', 'other')
    mapping = config.get('routing', {}).get('map', {})
    preferred = mapping.get(wtype) or mapping.get('default') or config.get('routing', {}).get('devFallbackAgent', 'chad')

    if preferred in available_agents:
        return preferred
    if wtype == 'code':
        return config.get('routing', {}).get('devFallbackAgent', 'chad')
    raise ValueError(f"agent '{preferred}' unavailable for work_type={wtype}")
