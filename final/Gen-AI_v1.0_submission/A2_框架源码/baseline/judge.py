"""供Aider --test-cmd调用；与自研使用完全相同的Toolchain。"""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent.src.tools import Toolchain

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--job',required=True)
    args=parser.parse_args()
    job=json.loads(Path(args.job).read_text(encoding='utf-8'))
    tool=Toolchain(job['tools'],job['deadline'],job['artifact_dir'],mode='live')
    source=Path(job['source']).read_text(encoding='utf-8')
    tag='aider_check_'+uuid.uuid4().hex[:12]
    compilation=tool.compile(source,tag)
    print(json.dumps(compilation,ensure_ascii=False))
    if compilation['status']!='pass':
        return 1
    tests=tool.test(source,tag)
    print(json.dumps(tests,ensure_ascii=False))
    return 0 if tests['status']=='pass' and tests['total']>0 else 1

if __name__=='__main__':
    raise SystemExit(main())
