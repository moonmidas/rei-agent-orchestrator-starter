
def ensure_same_thread(source_thread_id: str, approval_thread_id: str):
    if source_thread_id != approval_thread_id:
        raise ValueError('approval must be in the same Discord thread')
