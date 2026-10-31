"""执行后端：把"一条用例"跑出逐拍实际输出。

四个后端，接口一致：run(program, case) -> [{"cycle": 1, "out": {...}}, ...]

    echo   用期望值当实际值（验证链路，应全 pass）
    broken 翻转第一拍第一个 BOOL 输出（验证 compare 能定位失配）
    replay 读成员2 产出的 actual CSV（D2 起的主用通道）
    exec   直接调外部命令跑 ST，subprocess 硬超时（无 actual 时的兜底）

超时与故障分开：
    BackendTimeout  -> 判 timeout（不算模型失败）
    BackendError    -> 判 error（工具故障，成员3 统计时单列）

exec 的命令模板（用 --runner-cmd 传）支持这些占位符：
    {program} {inputs} {outputs} {case_id} {task_id}
其中 inputs 是本次用例的输入序列 CSV（cycle 从 0 起，0 是初态），
outputs 是要求被测程序写出的 actual CSV（格式见 runner/actual_io.py）。
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
from pathlib import Path

from .actual_io import ActualError, ActualStore


class BackendTimeout(Exception):
    """执行超时。"""


class BackendError(Exception):
    """工具故障：命令退出码非 0、actual 不合法等。"""


class Backend:
    def run(self, program, case):
        raise NotImplementedError


class EchoBackend(Backend):
    """把期望输出当成实际输出返回，用来验证 loader/compare/verdict 链路。"""

    def run(self, program, case):
        return [{"cycle": c["cycle"], "out": dict(c["out"])} for c in case.cycles[1:]]


class BrokenBackend(EchoBackend):
    """翻转第一拍的第一个 BOOL 输出（或 BOOL 数组的第一个元素）。"""

    def run(self, program, case):
        out = super().run(program, case)
        if out:
            first = out[0]["out"]
            for k, v in first.items():
                if isinstance(v, bool):
                    first[k] = not v
                    return out
                if isinstance(v, list) and v and isinstance(v[0], bool):
                    first[k] = [not v[0]] + list(v[1:])
                    return out
        return out


class ReplayBackend(Backend):
    """读 actual CSV。status=timeout 时整题判超时，不去读不存在的文件。"""

    def __init__(self, store, out_types, status=None):
        self.store = store
        self.out_types = out_types
        self.status = status or {}

    def run(self, program, case):
        if self.status.get("status") == "timeout":
            raise BackendTimeout(self.status.get("reason") or "status.json: timeout")
        expected = [c["cycle"] for c in case.cycles[1:]]
        try:
            return self.store.load(case.case_id, expected, self.out_types)
        except ActualError as e:
            raise BackendError(str(e)) from e


class ExecBackend(Backend):
    """调外部命令跑一条用例，subprocess.run(timeout=) 提供硬超时。"""

    def __init__(self, cmd_template, out_types, timeout_s=900.0, workdir=None,
                 extra=None):
        if not cmd_template:
            raise BackendError("exec 后端需要 --runner-cmd")
        self.cmd_template = cmd_template
        self.out_types = out_types
        self.timeout_s = timeout_s
        self.workdir = workdir
        self.extra = dict(extra or {})

    def run(self, program, case):
        expected = [c["cycle"] for c in case.cycles[1:]]
        with tempfile.TemporaryDirectory(prefix="exec_") as td:
            inputs = Path(td) / "inputs.csv"
            outputs = Path(td) / "outputs.csv"
            self._write_inputs(inputs, case)
            cmd = self._render(program, inputs, outputs, case)
            try:
                r = subprocess.run(cmd, cwd=self.workdir or None,
                                   capture_output=True, text=True,
                                   timeout=self.timeout_s)
            except subprocess.TimeoutExpired as e:
                raise BackendTimeout("runner 超过 %.0f s 未返回" % self.timeout_s) from e
            if r.returncode != 0:
                tail = (r.stderr or r.stdout or "").strip().splitlines()[-5:]
                raise BackendError("runner 退出码 %d：%s" % (r.returncode, " | ".join(tail)))
            if not outputs.exists():
                raise BackendError("runner 没有写出 %s" % outputs)

            # 把单文件 actual 包一层目录，复用同一套校验
            store = ActualStore(outputs)
            try:
                return store.load(case.case_id, expected, self.out_types)
            except ActualError as e:
                raise BackendError(str(e)) from e

    @staticmethod
    def _write_inputs(path, case):
        ins = list(case.cycles[0]["in"].keys())
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["cycle"] + ins)
            for c in case.cycles:                       # 含 cycle=0 初态
                w.writerow([c["cycle"]] + [_fmt(c["in"][k]) for k in ins])

    def _render(self, program, inputs, outputs, case):
        vals = {
            "program": str(program),
            "source": str(program),
            "inputs": str(inputs),
            "outputs": str(outputs),
            "case_id": case.case_id,
            "task_id": case.case_id.split("-")[0],
        }
        vals.update(self.extra)
        tpl = (self.cmd_template or "").strip()
        # JSON 数组形式：先解析再逐项替换，避免把 Windows 路径塞进 JSON 字符串里
        # 产生非法转义（"C:\Users" 里的 \U 会被 json 拒绝）。
        if tpl.startswith("["):
            try:
                argv = json.loads(tpl)
            except json.JSONDecodeError as e:
                raise BackendError("--runner-cmd 不是合法 JSON 数组：%s" % e) from e
            if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
                raise BackendError("--runner-cmd 的 JSON 必须是字符串数组")
            try:
                return [tok.format(**vals) for tok in argv]
            except KeyError as e:
                raise BackendError("--runner-cmd 里有未知占位符：%s" % e) from e
        try:
            text = tpl.format(**vals)
        except KeyError as e:
            raise BackendError("--runner-cmd 里有未知占位符：%s" % e) from e
        return split_cmd(text)


_CMD_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'|(\S+)')


def split_cmd(s):
    """把命令模板切成 argv。

    支持两种写法：
      - JSON 数组：["C:/Python/python.exe", "run_one.py", "--x", "1"]
      - 带引号的命令行："C:/Program Files/x.exe" run_one.py

    自己切而不是用 shlex：Windows 路径里的反斜杠不能被当转义符吃掉。
    """
    s = (s or "").strip()
    if s.startswith("["):
        try:
            argv = json.loads(s)
        except json.JSONDecodeError as e:
            raise BackendError("--runner-cmd 不是合法 JSON 数组：%s" % e) from e
        if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
            raise BackendError("--runner-cmd 的 JSON 必须是字符串数组")
        return argv
    argv = [a or b or c for a, b, c in _CMD_RE.findall(s)]
    if not argv:
        raise BackendError("--runner-cmd 为空")
    return argv


def _fmt(v):
    """写回输入 CSV：数组/结构体用 JSON，BOOL 用 TRUE/FALSE，其余原样。"""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False).replace("true", "TRUE").replace("false", "FALSE")
    return str(v)


def build_backend(name, *, actual=None, status=None, out_types=None,
                  runner_cmd=None, timeout_s=900.0, workdir=None):
    if name == "replay":
        if not actual:
            raise BackendError("replay 后端需要 --actual（文件或目录）")
        return ReplayBackend(ActualStore(actual), out_types or {}, status)
    if name == "exec":
        return ExecBackend(runner_cmd, out_types or {}, timeout_s, workdir)
    if name == "broken":
        return BrokenBackend()
    return EchoBackend()
