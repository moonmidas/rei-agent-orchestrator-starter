
def ensure_branch_and_pr(task: dict, branch_name: str | None, pr_url: str | None):
    if task.get('work_type') != 'code':
        return
    if not branch_name:
        raise ValueError('code task requires branch creation')
    if not pr_url:
        raise ValueError('code task requires PR URL')
