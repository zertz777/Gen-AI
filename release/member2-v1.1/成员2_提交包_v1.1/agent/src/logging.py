"""22字段结果契约；过程事件另存，避免下游误把每轮当一次实验。"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

FIELDS = ('run_id setting_id framework model task_id task_version repeat_idx seed '
          'start_ts latency_s candidates repair_rounds compile_status compile_stage '
          'compile_errors test_total test_passed verify_status final_status '
          'artifact_path tokens_in tokens_out').split()

def now():
    return datetime.now(timezone.utc).isoformat()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)

def event(directory, kind, **data):
    path = Path(directory) / 'events.jsonl'
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'ts': now(), 'event': kind, **data}, ensure_ascii=False) + '\n')

def save_result(directory, result):
    if set(result) != set(FIELDS):
        raise ValueError('Result fields differ from the 22-field contract')
    write_json(Path(directory) / 'result.json', result)
    (Path(directory) / 'run.jsonl').write_text(
        json.dumps(result, ensure_ascii=False) + '\n', encoding='utf-8')
