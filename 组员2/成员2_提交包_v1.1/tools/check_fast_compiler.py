"""对已安装MATIEC做真实语法/类型快检，不调用模型，不宣称PLC功能通过。"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agent.src.parse import parse_task
from agent.src.task_card import make_skeleton
from agent.src.tools import run_process, normalize_errors
from tools.check_codesys_compiler import probes

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',required=True)
    parser.add_argument('--out',default='validation/matiec_live')
    parser.add_argument('--tasks')
    args=parser.parse_args()
    exe=Path(args.exe).resolve()
    if not exe.is_file():parser.error('找不到iec2c.exe')
    output=Path(args.out).resolve()
    if output.exists() and any(output.iterdir()):parser.error('请使用新的空输出目录')
    output.mkdir(parents=True,exist_ok=True)
    cases=probes()
    if args.tasks:
        task_path=Path(args.tasks)
        paths=sorted(task_path.glob('*.yaml')) if task_path.is_dir() else [task_path]
        for path in paths:
            card=parse_task(path,root=ROOT)
            cases.append({'case_id':'task_'+path.stem+'_skeleton','kind':'task_skeleton',
                          'expected':'observe','source':make_skeleton(card)})
    rows=[]
    for case in cases:
        folder=output/case['case_id'];folder.mkdir()
        source=folder/'source.st';source.write_bytes(case.pop('source').encode('utf-8'))
        process=run_process([str(exe),'-f','-I',str(exe.parent/'lib'),'-T',str(folder),str(source)],
                            timeout_s=3,cwd=str(ROOT))
        for key in ('stdout','stderr'):(folder/(key+'.txt')).write_text(process[key],encoding='utf-8')
        row={**case,'status':process['status'],'elapsed_s':process['elapsed_s'],
             'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
             'errors':normalize_errors(process['stdout']+'\n'+process['stderr']),
             'evidence_kind':'live_fast_compiler','functional_tests_run':False}
        (folder/'result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
        rows.append(row)
        print(case['case_id'],process['status'],process['elapsed_s'],flush=True)
    result={'compiler':'MATIEC','recorded_at':datetime.now(timezone.utc).isoformat(),
            'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
            'evidence_kind':'live_fast_compiler','authoritative_compilation':False,
            'functional_tests_run':False,'case_count':len(rows),'cases':rows}
    (output/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # Only the known-good/known-bad probes establish successful fast-tool wiring.
    ok=all(r['status']==r['expected'] for r in rows if r['expected'] in ('pass','fail'))
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
