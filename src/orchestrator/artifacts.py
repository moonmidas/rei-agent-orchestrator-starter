def assert_required_artifacts(task: dict, artifacts: list[dict]):
    if task.get('work_type') != 'ui':
        return
    has_screenshot = any(a.get('artifact_type') == 'screenshot' for a in artifacts)
    if not has_screenshot:
        raise ValueError('ui task requires screenshot artifact')
