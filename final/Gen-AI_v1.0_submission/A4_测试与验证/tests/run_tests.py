"""批量对拍执行器入口（单题）。

    # 1) 链路自检：用期望值当实际值，应全 pass
    python tests/run_tests.py --cases tests/cases/P03.csv \
        --io tests/cases/_fixtures/P03.io.json \
        --out tests/results/P03.jsonl --backend echo

    # 2) 接成员2 的逐拍实际输出（D2 起的正路）
    python tests/run_tests.py --cases tests/cases/P03.csv \
        --io tests/cases/_fixtures/P03.io.json \
        --out tests/results/P03.jsonl \
        --backend replay --actual experiments/runs/E3/P03_r1_s42/test/actual

    # 3) 没有 actual 时直接调外部命令跑 ST（subprocess 硬超时）
    python tests/run_tests.py --cases tests/cases/P03.csv \
        --io tests/cases/_fixtures/P03.io.json \
        --out tests/results/P03.jsonl \
        --backend exec --program path/to/final.st \
        --runner-cmd '["python","baseline/run_one.py"]' --timeout 900

四个后端与 actual CSV 契约见 tests/README.md 第 3 节。
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runner.actual_io import ActualError, read_status          # noqa: E402
from runner.backends import BackendError, build_backend        # noqa: E402
from runner.case_loader import CaseError, load_cases, load_io  # noqa: E402
from runner.verdict import PASS, judge                         # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True, help="用例 CSV")
    ap.add_argument("--io", required=True, help="cases/_fixtures/<题号>.io.json")
    ap.add_argument("--out", required=True, help="结果 JSONL")
    ap.add_argument("--backend", default="echo",
                    choices=["echo", "broken", "replay", "exec"])
    ap.add_argument("--actual", help="replay：actual CSV 文件或 <run>/test/actual 目录")
    ap.add_argument("--run-dir", help="replay：run 目录，读 <run>/test/status.json")
    ap.add_argument("--runner-cmd", help="exec：命令模板，支持 {program} {inputs} {outputs}")
    ap.add_argument("--program", default="<none>", help="exec：被测 ST 源文件")
    ap.add_argument("--workdir", help="exec：子进程工作目录")
    ap.add_argument("--timeout", type=float, default=900.0)
    a = ap.parse_args(argv)

    try:
        task_id, ins, outs = load_io(a.io)
        _, cases = load_cases(a.cases, a.io)
    except (CaseError, ActualError) as e:
        print("用例/接口校验失败：%s" % e, file=sys.stderr)
        return 2

    try:
        status = read_status(a.run_dir) if a.run_dir else None
        backend = build_backend(a.backend, actual=a.actual, status=status,
                                out_types=outs, runner_cmd=a.runner_cmd,
                                timeout_s=a.timeout, workdir=a.workdir)
    except (BackendError, ActualError) as e:
        print("后端初始化失败：%s" % e, file=sys.stderr)
        return 2

    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = {k: 0 for k in ("pass", "fail", "timeout", "error")}
    with out_path.open("w", encoding="utf-8") as f:
        for case in cases:
            try:
                r = judge(case, backend, a.program, a.timeout)
            except Exception as e:                       # 单题跑崩不影响整批
                r = {"case_id": case.case_id, "status": "error",
                     "mismatch": {"error": repr(e),
                                  "trace": traceback.format_exc()[-800:]},
                     "latency_s": None}
            n[r["status"]] = n.get(r["status"], 0) + 1
            f.write(json.dumps({"task_id": task_id, **r}, ensure_ascii=False) + "\n")

    print("%s: pass=%d fail=%d timeout=%d error=%d"
          % (task_id, n["pass"], n["fail"], n["timeout"], n["error"]))
    print("-> %s" % out_path)
    return 0 if (n["fail"] == 0 and n["timeout"] == 0 and n["error"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
