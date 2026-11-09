"""ST 子集解释器（成员4 的兜底执行通道）。

用途与边界（写死在代码里，避免被误用）：

- **只用于变异测试的底本**：被测对象是成员4 自己写的参考实现，不是模型产物；
- **不能**拿它产出的 actual 冒充成员2 的 L2 结果（那是自证，报告会崩）；
- 支持范围见 `docs/interp.md`：IEC 61131-3 的 FUNCTION_BLOCK / VAR 块 /
  赋值 / IF / CASE / FOR / WHILE / REPEAT / ARRAY / STRUCT / TON / TOF /
  R_TRIG / F_TRIG / CTU。

命令行契约与给成员2 的 `runner-cmd` 完全一致，两边可互换：

    python tests/runner/interp/run.py --source x.st \
        --inputs inputs.csv --outputs outputs.csv --case-id P03-01

或一次跑完整题（给变异测试用）：

    python tests/runner/interp/run.py --source x.st \
        --cases tests/cases/P03.csv --io tests/cases/_fixtures/P03.io.json \
        --out-dir verify/mutants/M-P03-1/test/actual
"""

from .eval import Interpreter, InterpError  # noqa: F401
from .parser import parse  # noqa: F401
from .st_types import StTypeError, TypeSpec, format_value, parse_literal  # noqa: F401

__all__ = [
    "Interpreter",
    "InterpError",
    "parse",
    "TypeSpec",
    "StTypeError",
    "parse_literal",
    "format_value",
]
