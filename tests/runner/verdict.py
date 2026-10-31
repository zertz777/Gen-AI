"""三态判定：pass / fail / timeout（工具故障另记 error）。

超时是独立状态，绝不并入 fail——否则成员3 的四组数据不可比。
工具故障（actual 缺列、runner 退出码非 0）也单独成 error 态，同样不算模型失败。
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from .backends import BackendError, BackendTimeout

PASS, FAIL, TIMEOUT, ERROR = "pass", "fail", "timeout", "error"


def run_with_timeout(fn, args, timeout_s):
    """软超时守卫，返回 (结果, 是否超时)。

    注意：超时后线程仍在后台跑完（Python 没法强杀线程），所以这里用
    shutdown(wait=False) 不阻塞主流程。真正的硬超时由 ExecBackend 的
    subprocess.run(timeout=) 提供——它会把子进程 kill 掉。
    """
    pool = ThreadPoolExecutor(max_workers=1)
    fut = pool.submit(fn, *args)
    try:
        return fut.result(timeout=timeout_s), False
    except FutureTimeout:
        return None, True
    finally:
        pool.shutdown(wait=False)


def judge(case, backend, program, timeout_s=900.0):
    """跑一条用例，返回 {case_id, status, mismatch, reason, latency_s}。"""
    from .compare import compare_case

    t0 = time.perf_counter()
    # exec 后端自己会在 timeout_s 处硬超时；外层线程多给 10 s，避免两者抢跑
    soft = timeout_s + 10.0 if getattr(backend, "timeout_s", None) is not None else timeout_s
    try:
        actual, timed_out = run_with_timeout(backend.run, (program, case), soft)
    except BackendTimeout as e:
        return {"case_id": case.case_id, "status": TIMEOUT, "mismatch": None,
                "reason": str(e), "latency_s": round(time.perf_counter() - t0, 3)}
    except BackendError as e:
        return {"case_id": case.case_id, "status": ERROR,
                "mismatch": {"error": str(e)}, "reason": str(e),
                "latency_s": round(time.perf_counter() - t0, 3)}

    latency = time.perf_counter() - t0
    if timed_out:
        return {"case_id": case.case_id, "status": TIMEOUT, "mismatch": None,
                "reason": "软超时 %.0f s（进程可能仍在跑）" % soft,
                "latency_s": round(latency, 3)}

    ok, mismatch = compare_case(case, actual)
    return {"case_id": case.case_id, "status": PASS if ok else FAIL,
            "mismatch": mismatch, "latency_s": round(latency, 3)}
