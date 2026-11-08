"""只接受可定位的增量替换；逐轮差异与回归判定由入口记录。"""
import difflib
import json
import re

TEMPLATES = {
    'undeclared': '声明缺失的变量，保持原I/O名称与类型。',
    'type': '修正类型或显式转换，禁止更改外部接口。',
    'library': '使用已配置库的等价实现；无法替代时明确保留缺库错误。',
    'syntax': '修正ST语法，保留已通过的逻辑。',
    'logic': '按失败周期的输入/期望/实际值修复逻辑，保留已通过用例。'}

def error_kind(errors):
    text = ' '.join(str(e.get('code','')) + ' ' + str(e.get('message','')) for e in errors).lower()
    for kind, words in [('undeclared', ['undeclared','unknown variable','未声明']),
                        ('library', ['library','库']), ('type', ['type','类型'])]:
        if any(w in text for w in words):
            return kind
    return 'syntax' if errors else 'logic'

def feedback(source, compilation, tests):
    lines, blocks = source.splitlines(), []
    errors = compilation.get('errors', [])
    # 仅提供错误位置附近±3行；无行号时不回灌全文。
    for err in errors[:8]:
        n = err.get('line')
        blocks.append(json.dumps({k: err.get(k) for k in ('code','severity','line','message')}, ensure_ascii=False))
        if isinstance(n, int) and n > 0:
            blocks.append('\n'.join(f'{i+1}: {lines[i]}' for i in range(max(0,n-4), min(len(lines),n+3))))
    for fail in tests.get('failures', [])[:5]:
        blocks.append(json.dumps(fail, ensure_ascii=False))
    return TEMPLATES[error_kind(errors)] + '\n' + '\n'.join(blocks)

def apply_patch(source, response):
    match = re.search(r'```(?:json)?\s*\n(.*?)```', response, re.S)
    obj = json.loads(match.group(1) if match else response)
    patches = obj.get('patches') if isinstance(obj, dict) else obj
    if not isinstance(patches, list) or not patches:
        raise ValueError('Expected nonempty patches list')
    if len(patches) > 12:
        raise ValueError('Too many patch edits')
    result = source
    for patch in patches:
        old, new = patch['old'], patch['new']
        if not isinstance(old, str) or not old or not isinstance(new, str) or result.count(old) != 1:
            raise ValueError('Patch target must occur exactly once')
        if old.strip() == source.strip():
            raise ValueError('Full-file replacement is prohibited')
        if len(old.splitlines()) > max(12, len(source.splitlines())//2):
            raise ValueError('Full-file replacement is prohibited')
        result = result.replace(old, new, 1)
    if result == source:
        raise ValueError('Patch makes no change')
    return result

def diff(old, new):
    return ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        fromfile='before.st', tofile='after.st'))

def regresses(previous, current):
    if previous['compile']['status'] == 'pass' and current['compile']['status'] != 'pass':
        return True
    if previous['test'].get('status') in ('pass','fail') and current['test'].get('status') not in ('pass','fail'):
        return True
    return not set(previous['test'].get('passed_ids', [])).issubset(current['test'].get('passed_ids', []))
