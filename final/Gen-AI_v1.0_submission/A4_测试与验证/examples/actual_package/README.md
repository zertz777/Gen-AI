# actual 示例包（给成员2）

一个**完整 run 的目录形状**，照着填就行。示例里的 actual 是用 P03 用例的期望值生成的，
只演示格式，**不是任何程序的真实结果**。

## 目录

```
E3_P03_r1_s42/
├── source/
│   └── final.st              # 被测程序（现在是占位，换成你生成的）
├── task_card.json            # 成员2 的任务卡（测试器用它还原 I/O 方向与类型）
└── test/
    ├── actual/
    │   ├── P03-01.csv        # 一条用例一份，逐拍实际输出
    │   └── … P03-06.csv
    ├── status.json.example   # 整题超时怎么写（正常跑完不要放 status.json）
    ├── cases_result.jsonl    # 逐条用例判定（我这边生成，你不用产出）
    └── result.demo.json      # 用 tester_cli 跑出来的协议 JSON（示例）
```

## 你只需要产出三样

1. `source/final.st`：被测程序；
2. `test/actual/<case_id>.csv`：每条用例一份，逐拍实际输出；
3. 整题编译超时/跑崩时，写 `test/status.json`（正常跑完**不要**放这个文件）。

## 接 `test.command`（推荐）

把 `组员4/tests/` 拷进你包根目录，`tools.test` 填：

```json
"test": {
  "command": ["python", "tests/tester_cli.py",
              "--source", "{source}", "--task-card", "{task_card}",
              "--cases-dir", "{cases_dir}", "--result", "{result}"],
  "timeout_s": 90,
  "cases_dir": "tests/cases"
}
```

`tester_cli.py` 会输出你 `tools.py` 要的 JSON（`status/total/passed/passed_ids/failures`），
退出码 `pass=0 / fail=1 / tool_error=2`。没有 actual 时可用 `--runner-cmd`（或环境变量
`PLC_RUNNER_CMD`）接你自己的逐拍执行命令；两者都没有就返回 `skipped`，不会伪造 pass。

用示例包自检：

```bash
python tests/tester_cli.py \
  --source examples/actual_package/E3_P03_r1_s42/source/final.st \
  --task-card examples/actual_package/E3_P03_r1_s42/task_card.json \
  --cases-dir tests/cases \
  --result examples/actual_package/E3_P03_r1_s42/test/result.demo.json
```

预期：`exit=0`，JSON 里 `"status":"pass","total":6,"passed":6`。

## actual CSV 规则

| 规则 | 说明 |
| --- | --- |
| 表头 | `case_id,cycle,<输出列…>`，输出列名与 `tests/cases/_fixtures/<题号>.io.json` 的 OUT 列**逐字一致** |
| cycle | 从 **1** 起、连续；可以带 `cycle=0` 初态行（我读取时忽略） |
| 拍数 | 必须等于用例拍数（少一拍/多一拍都判 error） |
| BOOL | `TRUE` / `FALSE`，不要写 1/0 |
| WORD/DWORD | `16#8001`、`16#0000` |
| TIME/LTIME | `T#500ms`、`T#2s` |
| REAL | `12.5`（不要带单位） |
| ARRAY | `[1,2,3,4,5]`，元素按上面各类型写 |
| `X` | **不要写**。`X` 只出现在期望侧，actual 必须是实际值 |

## status.json

```json
{"status": "timeout", "reason": "compile timeout 90s"}
```

`status` 只能是 `pass / fail / timeout / error`。写 `timeout` 时整题判超时，
我不会去读 actual——这样编译超时不会算成模型写错。

## 自检（在你的仓库根目录跑）

```bash
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out examples/actual_package/E3_P03_r1_s42/test/cases_result.jsonl \
  --backend replay \
  --actual examples/actual_package/E3_P03_r1_s42/test/actual \
  --run-dir examples/actual_package/E3_P03_r1_s42
```

预期输出：`P03: pass=6 fail=0 timeout=0 error=0`。
出现 `error` 说明格式不对（缺列/拍号/类型），不是程序写错。

## 五个最常见的错误

| 现象 | 原因 | 怎么改 |
| --- | --- | --- |
| `缺输出列：status` | 少写了一列 | 对着 fixture 的 OUT 列补齐 |
| `拍号不对` | cycle 从 0 开始、跳号、少拍 | 从 1 起连续写，拍数对齐用例 |
| `BOOL 列出现 '1'` | 用 1/0 代替 TRUE/FALSE | 改成 `TRUE` / `FALSE` |
| `TIME 解析失败` | 写成 `500` 或 `0.5s` | 改成 `T#500ms` |
| 整题判 timeout 但你没超时 | 误放了 `status.json` | 正常跑完删掉它，模板改名 `status.json.example` |

## 批量

```bash
python tests/run_batch.py --runs experiments/runs/E3 \
  --out tests/results/batch/E3 --framework self --model <模型名>
```

目录名按 `<组别>/<题号>_r<次>_s<种子>/`，例如 `E3/P07_r1_s42/`。
