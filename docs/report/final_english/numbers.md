# Numerical Evidence Register

This file records every measured value used in the final English report. Section, table, figure, citation, and standards-year labels are identifiers rather than measured outcomes.

## Primary recomputation commands

```powershell
python tools/stats.py
python experiments/verify_package.py
```

## Environment and resource values

| Fact | Value | Source |
| --- | ---: | --- |
| Operating-system build | 10.0.26200 | `docs/env.md` |
| Architecture label | 64-bit | `docs/env.md` |
| Python validation version | 3.12.14 | `docs/env.md` |
| Python minimum version | 3.10 | `docs/env.md` |
| CODESYS version | 3.5.22.40 | `docs/env.md` |
| CODESYS profile | V3.5 SP22 Patch 4 | `docs/env.md` |
| CODESYS scripting engine | 4.2.0.0 | `docs/env.md` |
| Embedded IronPython version | 2.7 | `docs/env.md` |
| Standard library version | 3.5.22.0 | `docs/env.md` |
| IoStandard library version | 3.5.22.0 | `docs/env.md` |
| Scan cycle | 20 ms | `docs/env.md`; `data/tasks/*.yaml` |
| Aider baseline version | 0.86.2 | `docs/env.md` |
| Model A | deepseek-v4.1-flash | `docs/env.md` |
| Model B | gpt-6.1-sol | `docs/env.md` |
| Single-task hard timeout | 900 s | `docs/env.md` |
| Authoritative compile timeout | 90 s | `docs/env.md` |
| Fast-check target | 3 s | `docs/env.md` |
| Context budget preset | 6000 token (local estimate) | `agent/configs/default.yaml`; `docs/framework.md` |
| Local cumulative token threshold | 100000 | `agent/configs/default.yaml`; `docs/framework.md` |
| Default candidate count | 3 | `agent/configs/default.yaml` |
| Maximum candidate count | 5 | `agent/configs/default.yaml` |
| Maximum repair rounds | 5 | `agent/configs/default.yaml` |
| No-improvement stop threshold | 2 rounds | `agent/configs/default.yaml` |
| Concurrency slots | 2 | `docs/env.md` |
| Local seed identifier | 42 | `docs/env.md` |
| CODESYS diagnostic probes | 6 | `docs/env.md` |
| CODESYS declaration skeletons passed | 33 of 34 | `docs/env.md` |
| CODESYS environment-check duration | 121.4 s | `docs/report/ch3.md` |
| Correct-example dual-channel duration | 33.8 s | `docs/report/ch3.md` |
| Error-example dual-channel duration | 32.2 s | `docs/report/ch3.md` |
| MATIEC skeleton passes | 27 of 34 | `docs/report/ch3.md` |
| MATIEC skeleton dialect failures | 4 | `docs/report/ch3.md` |
| MATIEC skeleton timeouts | 3 | `docs/report/ch3.md` |

## Dataset and test suite

| Fact | Value | Source |
| --- | ---: | --- |
| Tasks | 34 | `data/tasks/*.yaml`; `python experiments/verify_package.py` |
| Public tasks | 20 | `data/tasks/P*.yaml` |
| Self-built tasks | 14 | `data/tasks/S*.yaml` |
| I/O points | 316 | `data/tasks/*.yaml` |
| Constraints | 144 | `data/tasks/*.yaml` |
| LTL clauses | 177 | `data/specs/*.ltl` |
| Easy tasks | 9 | `data/tasks/*.yaml` |
| Medium tasks | 14 | `data/tasks/*.yaml` |
| Hard tasks | 11 | `data/tasks/*.yaml` |
| Category A tasks | 6 | `data/tasks/*.yaml` |
| Category B tasks | 11 | `data/tasks/*.yaml` |
| Category C tasks | 11 | `data/tasks/*.yaml` |
| Category D tasks | 6 | `data/tasks/*.yaml` |
| Test files | 34 | `tests/cases/*.csv` |
| Test cases | 214 | `tests/cases/*.csv` |
| CSV rows | 22636 | `tests/cases/*.csv` |
| Executed scan steps | 22422 | `tests/cases/*.csv` |
| Normal cases | 68 | `tests/cases/*.csv` |
| Boundary cases | 38 | `tests/cases/*.csv` |
| Abnormal cases | 48 | `tests/cases/*.csv` |
| Safety cases | 60 | `tests/cases/*.csv` |
| Covered constraint rows | 143 | `tests/coverage.csv` |
| Tasks whose experiment case copies differ from the frozen set | 5 | `docs/判据与用例版本核对.md` |
| Disputed tasks | 3 | `docs/判据待核查.md` |
| Shared result fields | 22 | `docs/framework.md`; `experiments/per_task.csv` |
| P03-01 example values | 0; 10; 3; 12; 9; 7; 2; 6 | `tests/cases/P03.csv` |

## Experiment matrix

| Fact | Value | Source |
| --- | ---: | --- |
| Final runs | 136 | `experiments/per_task.csv`; `python experiments/verify_package.py` |
| Revised replacement runs | 32 | `experiments/per_task.csv`; `python experiments/verify_package.py` |
| Original retained runs | 104 | `experiments/per_task.csv`; `python experiments/verify_package.py` |
| Runs per setting | 34 | `experiments/per_task.csv` |
| Experiment settings | 4 | `experiments/configs/E1.yaml` to `E4.yaml` |
| E1 full-task passes | 18 of 34 | `experiments/summary.csv` |
| E1 full-task pass rate | 52.94% | `experiments/summary.csv` |
| E1 compile passes | 32 of 34 | `experiments/summary.csv` |
| E1 compile rate | 94.12% | `experiments/summary.csv` |
| E1 functional cases passed | 155 of 197 | `experiments/summary.csv` |
| E1 functional-case pass rate | 78.68% | `experiments/summary.csv` |
| E1 median latency | 553.0 s | `experiments/summary.csv` |
| E1 p95 latency | 830.4 s | `experiments/summary.csv` |
| E1 known input tokens | 537,229 | `experiments/summary.csv` |
| E1 known output tokens | 987,897 | `experiments/summary.csv` |
| E1 known-token total | 1,525,126 | `experiments/summary.csv` |
| E1 runs with unknown usage | 8 | `experiments/summary.csv` |
| E1 mean repair rounds | 0.00 | `experiments/summary.csv` |
| E2 full-task passes | 16 of 34 | `experiments/summary.csv` |
| E2 full-task pass rate | 47.06% | `experiments/summary.csv` |
| E2 compile passes | 32 of 34 | `experiments/summary.csv` |
| E2 compile rate | 94.12% | `experiments/summary.csv` |
| E2 functional cases passed | 147 of 203 | `experiments/summary.csv` |
| E2 functional-case pass rate | 72.41% | `experiments/summary.csv` |
| E2 median latency | 299.7 s | `experiments/summary.csv` |
| E2 p95 latency | 594.7 s | `experiments/summary.csv` |
| E2 known input tokens | 1,026,727 | `experiments/summary.csv` |
| E2 known output tokens | 180,806 | `experiments/summary.csv` |
| E2 known-token total | 1,207,533 | `experiments/summary.csv` |
| E2 runs with unknown usage | 1 | `experiments/summary.csv` |
| E2 mean repair rounds | 0.00 | `experiments/summary.csv` |
| E3 full-task passes | 8 of 34 | `experiments/summary.csv` |
| E3 full-task pass rate | 23.53% | `experiments/summary.csv` |
| E3 compile passes | 28 of 34 | `experiments/summary.csv` |
| E3 compile rate | 82.35% | `experiments/summary.csv` |
| E3 functional cases passed | 72 of 175 | `experiments/summary.csv` |
| E3 functional-case pass rate | 41.14% | `experiments/summary.csv` |
| E3 median latency | 357.1 s | `experiments/summary.csv` |
| E3 p95 latency | 540.5 s | `experiments/summary.csv` |
| E3 known input tokens | 103,954 | `experiments/summary.csv` |
| E3 known output tokens | 943,390 | `experiments/summary.csv` |
| E3 known-token total | 1,047,344 | `experiments/summary.csv` |
| E3 runs with unknown usage | 0 | `experiments/summary.csv` |
| E3 mean repair rounds | 0.00 | `experiments/summary.csv` |
| E4 full-task passes | 7 of 34 | `experiments/summary.csv` |
| E4 full-task pass rate | 20.59% | `experiments/summary.csv` |
| E4 compile passes | 33 of 34 | `experiments/summary.csv` |
| E4 compile rate | 97.06% | `experiments/summary.csv` |
| E4 functional cases passed | 94 of 209 | `experiments/summary.csv` |
| E4 functional-case pass rate | 44.98% | `experiments/summary.csv` |
| E4 median latency | 268.8 s | `experiments/summary.csv` |
| E4 p95 latency | 636.4 s | `experiments/summary.csv` |
| E4 known input tokens | 211,195 | `experiments/summary.csv` |
| E4 known output tokens | 121,692 | `experiments/summary.csv` |
| E4 known-token total | 332,887 | `experiments/summary.csv` |
| E4 runs with unknown usage | 1 | `experiments/summary.csv` |
| E4 mean repair rounds | 1.56 | `experiments/summary.csv` |
| Known token total across four settings | 4,112,890 | `experiments/summary.csv` |
| Figure 5 rounded labels | E1 1.53M; E2 1.21M; E3 1.05M; E4 0.33M | `experiments/summary.csv` |
| Runs with unknown usage | 10 of 136 | `experiments/summary.csv` |
| E3 budget terminations | 24 | `experiments/summary.csv`; `experiments/per_task.csv` |
| E3 budget terminations with a compilable artifact | 19 | `experiments/per_task.csv` |
| E3 budget terminations without a compilable artifact | 5 | `experiments/per_task.csv` |
| E3 mean repair rounds | 0.00 | `experiments/summary.csv` |
| E4 mean repair rounds | 1.56 | `experiments/summary.csv` |

## Difficulty and paired outcomes

| Fact | Value | Source |
| --- | ---: | --- |
| E1 easy / medium / hard passes | 6 of 9 / 8 of 14 / 4 of 11 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| Figure 4 displayed E1 percentages | 67; 57; 36 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| E2 easy / medium / hard passes | 7 of 9 / 6 of 14 / 3 of 11 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| Figure 4 displayed E2 percentages | 78; 43; 27 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| E3 easy / medium / hard passes | 5 of 9 / 2 of 14 / 1 of 11 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| Figure 4 displayed E3 percentages | 56; 14; 9 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| E4 easy / medium / hard passes | 4 of 9 / 2 of 14 / 1 of 11 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| Figure 4 displayed E4 percentages | 44; 14; 9 | `experiments/34_task_matrix.csv`; `data/tasks/*.yaml` |
| DeepSeek: baseline-only / shared / harness-only passes | 10 / 8 / 0 | `experiments/34_task_matrix.csv` |
| GPT: baseline-only / shared / harness-only passes | 9 / 7 / 0 | `experiments/34_task_matrix.csv` |
| Aider: shared / first-model-only / second-model-only passes | 15 / 3 / 1 | `experiments/34_task_matrix.csv` |
| harness: shared / first-model-only / second-model-only passes | 6 / 2 / 1 | `experiments/34_task_matrix.csv` |

## Audit and verification status

| Fact | Value | Source |
| --- | ---: | --- |
| Formal-verification runs marked skipped | 136 of 136 | `experiments/runs/E*/**/result.json` |
| Independent replay runs with source | 132 | `experiments/reproduction/summary.jsonl` |
| Independent replay completed | 72 | `experiments/reproduction/summary.jsonl` |
| Independent replay interpreter errors | 60 | `experiments/reproduction/summary.jsonl` |
| Independent replay without source | 4 | `experiments/reproduction/summary.jsonl` |

## Status decompositions

| Setting | Terminal status counts | Source |
| --- | --- | --- |
| E1 | abandoned:timeout: 2; best-effort:test_fail: 13; best-effort:tool_error: 1; passed: 18 | `experiments/per_task.csv` |
| E2 | abandoned:compile_fail: 1; abandoned:timeout: 1; best-effort:test_fail: 16; passed: 16 | `experiments/per_task.csv` |
| E3 | abandoned:budget: 5; abandoned:timeout: 1; best-effort:budget: 19; best-effort:timeout: 1; passed: 8 | `experiments/per_task.csv` |
| E4 | abandoned:compile_fail: 1; best-effort:test_fail: 25; best-effort:timeout: 1; passed: 7 | `experiments/per_task.csv` |

The report does not convert unknown token usage to zero and does not claim a price total.

## Per-task appendix counts

| Task | I/O | Constraints | LTL | K covered | Source |
| --- | ---: | ---: | ---: | ---: | --- |
| P01 | 11 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P02 | 8 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P03 | 8 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P04 | 7 | 5 | 5 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P05 | 5 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P06 | 4 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P07 | 7 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P08 | 10 | 5 | 5 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P09 | 9 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P10 | 7 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P11 | 12 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P12 | 9 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P13 | 5 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P14 | 2 | 4 | 2 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P15 | 16 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P16 | 13 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P17 | 16 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P18 | 7 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P19 | 24 | 5 | 6 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| P20 | 17 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S01 | 8 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S02 | 8 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S03 | 9 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S04 | 7 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S05 | 8 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S06 | 9 | 4 | 6 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S07 | 12 | 5 | 6 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S08 | 9 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S09 | 9 | 5 | 5 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S10 | 6 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S11 | 7 | 5 | 4 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S12 | 8 | 4 | 5 | 4 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S13 | 11 | 5 | 6 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
| S14 | 8 | 5 | 6 | 5 | `data/tasks/*.yaml`; `data/specs/*.ltl`; `tests/coverage.csv` |
