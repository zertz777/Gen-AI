"""只读检查源码/数据/记录，并生成可审阅的验收状态。"""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent.src.parse import parse_task
from agent.src.task_card import make_skeleton,build_context
from agent.src.logging import FIELDS,write_json

ROOT=Path(__file__).resolve().parents[1]

def main():
    hashes=[]
    for line in (ROOT/'data/sha256sums.txt').read_text(encoding='utf-8').splitlines():
        expected,path=line.split(None,1)
        p=ROOT/'data'/path.strip()
        hashes.append({'path':path.strip(),'ok':hashlib.sha256(p.read_bytes()).hexdigest()==expected})
    cards=[parse_task(p,root=ROOT) for p in sorted((ROOT/'data/tasks').glob('*.yaml'))]
    contexts=[build_context(c) for c in cards]
    logs=[]
    for path in sorted((ROOT/'agent/logs').rglob('run.jsonl')):
        rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]
        logs.append({'path':path.relative_to(ROOT).as_posix(),
                     'ok':len(rows)==1 and set(rows[0])==set(FIELDS)})
    compiler_cases=[]
    evidence=ROOT/'validation/codesys_release_v1.1/summary.json'
    if evidence.exists():
        summary=json.loads(evidence.read_text(encoding='utf-8'))
        for row in summary.get('cases',[]):
            folder=evidence.parent/row['artifact_path']
            source=folder/'source.st'
            native=folder/'result.json'
            if source.is_file() and native.is_file():
                result=json.loads(native.read_text(encoding='utf-8-sig'))
                if result.get('compiler')=='CODESYS' and result.get('source_sha256')==hashlib.sha256(source.read_bytes()).hexdigest():
                    compiler_cases.append(dict(case_id=row['case_id'],kind=row['kind'],
                        status=result['status'],code_generated=result.get('code_generated',False)))
    skeleton_cases=[row for row in compiler_cases if row['kind']=='task_skeleton']
    report={'scope':'data/fixture/compiler-evidence consistency; no model-quality or functional-test claim',
        'source_hash_files':len(hashes),'source_hashes_passed':sum(x['ok'] for x in hashes),
        'parsed_tasks':len(cards),'skeletons_generated':sum(bool(make_skeleton(c)) for c in cards),
        'degraded_task_ids':[c['task_id'] for c in cards if c['degraded']],
        'max_context_estimate':max(c['estimated_tokens'] for c in contexts),
        'mandatory_context_overflows':sum(c['overflow'] for c in contexts),
        'log_groups':len(logs),'log_schema_passed':sum(x['ok'] for x in logs),
        'real_model_calls_performed':False,'real_authoritative_compile_performed':bool(compiler_cases),
        'authoritative_cases_with_matching_source_hash':len(compiler_cases),
        'authoritative_skeletons_passed':sum(row['status']=='pass' and row['code_generated'] for row in skeleton_cases),
        'authoritative_skeletons_failed':[row['case_id'] for row in skeleton_cases if row['status']!='pass'],
        'real_member4_tests_performed':False,'hash_details':hashes,'log_details':logs}
    write_json(ROOT/'validation/delivery_check.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('hash_details','log_details')},ensure_ascii=False,indent=2))
    return 0 if all(x['ok'] for x in hashes+logs) and len(cards)==34 else 1

if __name__=='__main__':
    raise SystemExit(main())
