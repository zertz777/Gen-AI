# 群聊消息（精简版，复制即用）

发送顺序：**先成员2**（关键路径），再成员1（冻结前），成员3/5 可以一起发。

---

## 给成员2（接口已接好）

> @成员2 你们的 `tools.test` 协议我按 `docs/toolchain.md` §4 接好了：把 `组员4/tests/` 整个拷进你包根目录，`tools.test` 填：
>
> `"command": ["python","tests/tester_cli.py","--source","{source}","--task-card","{task_card}","--cases-dir","{cases_dir}","--result","{result}"]`
>
> 有 actual 就直接判；没有 actual 时用 `--runner-cmd`（或环境变量 `PLC_RUNNER_CMD`）接你的 CODESYS 跑批命令，runner 读 `inputs.csv` 逐拍跑、写 `outputs.csv`。
> 两者都没有就返回 `skipped`，不会伪造 pass。示例包：`组员4/examples/actual_package.zip`。

---

## 给成员1（冻结前 4 条）

> @成员1 冻结前有 4 条要改：
> ① `P13.ltl` C2 的 `!= 4` 应为 `!= 3`（夜间模式是 3）；
> ② `S11.ltl` C2/C4 和 K3 的“恢复后 3 s 才退出降级”矛盾；
> ③ `P01.ltl` C2 和需求“泵 continues to work”冲突；
> ④ `P17` 的 K3 只写 8001，需求正文是 8001/8004/8005。
> 另外确认一句：用例 `spec_refs` 用 `K3;K4;C7`（K 为主）可以吗？

---

## 给成员3（分母与字段）

> @成员3 题量按 34 走：主轮 136 跑、复跑 48、合计 184，`176` 那个数要改。
> `summary` 用五列分开：`test_passed/failed/timeout/error/missing`，`missing` 和 `error` 不进失败率。
> 对账一条命令：`python tests/gen/check_alignment.py --ours ... --theirs ... --setting E3`。

---

## 给成员5（合并路径）

> @成员5 两处合并：
> `组员4/tests/` → `<repo>/tests/`（`run_tests.py` 不许改名）；
> `组员4/docs/qa/member4.md` → `<repo>/docs/qa/`。
> 合完回一句“路径已通”，D4.1/D4.3 的验收路径靠它。

---

## 21:00 站会只问三句

> 1. actual 到哪了？几个 run、落在哪个路径？
> 2. 4 条规约改了没（P13 / S11 / P01 / P17）？
> 3. 分母改 34 / 136 了没？

---

## 如果 18:00 还没有 actual（群里发这条）

> @全体 actual 18:00 还没到的话，D2-6 全量第一轮顺延到 D3 上午；
> 我今晚用 3 题抽样把缺陷单和复现流程走通，交接里如实标 `blocked`，不拿抽样数当 136 跑的分母。
> 成员3 的统计排期请按这个调整。
