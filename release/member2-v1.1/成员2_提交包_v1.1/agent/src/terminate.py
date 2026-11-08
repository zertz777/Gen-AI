"""有界终止与候选排序：功能通过数、修复轮次、实际token。"""
import time

class StopRun(RuntimeError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)

def check_limits(deadline, used_tokens, token_budget):
    if time.monotonic() >= deadline:
        raise StopRun('timeout')
    if used_tokens >= token_budget:
        raise StopRun('budget')

def rank(candidate):
    compiled = candidate['compile']['status'] == 'pass'
    return (int(compiled), candidate['test'].get('passed', 0) if compiled else -1,
            -candidate.get('repair_rounds', 0), -candidate.get('token_count', 0))

def success(candidate):
    t = candidate['test']
    return (candidate['compile']['status'] == 'pass' and t.get('status') == 'pass'
            and t.get('total', 0) > 0 and t['passed'] == t['total'])

def classify(candidate, reason=None):
    if reason:
        return ('best-effort:' if candidate and candidate['compile']['status'] == 'pass'
                else 'abandoned:') + reason
    if not candidate:
        return 'abandoned:tool_error'
    c, t = candidate['compile'], candidate['test']
    if c['status'] == 'timeout' or t.get('status') == 'timeout':
        return 'abandoned:timeout'
    if c['status'] == 'tool_error' or t.get('status') == 'tool_error':
        return 'abandoned:tool_error'
    if c['status'] != 'pass':
        return 'abandoned:compile_fail'
    if success(candidate):
        return 'passed'
    return 'best-effort:' + ('tests_missing' if t.get('status') == 'skipped' else 'test_fail')
