(*
【必留：需求原文】
Design a PLC function block in Structured Text (ST) that parses a dotted-decimal IPv4 string into a 32-bit unsigned integer.

1. ipText must contain four nonempty decimal-digit segments separated by periods. Each segment must have a value from 0 through 255.
2. Assemble the address in network byte order: the first segment occupies the most significant 8 bits and the fourth occupies the least significant 8 bits. Write the result to ipValue.
3. Set ipValue to 0 for malformed input, a nondigit segment, an incorrect segment count or any out-of-range segment. The valid address 0.0.0.0 also produces 0.

中文摘要：IPv4 点分十进制解析：校验四段、纯数字与 0—255 范围，按网络字节序组装为 32 位无符号整数，非法输入输出 0。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P14",
  "title": "IPv4 Parsing with Format and Range Checks",
  "io_table": [
    {
      "direction": "IN",
      "name": "ipText",
      "data_type": "STRING(254)",
      "description": "IPv4 text to parse, with a capacity of 254 characters. A valid dotted-decimal address requires at most 15 characters."
    },
    {
      "direction": "OUT",
      "name": "ipValue",
      "data_type": "UDINT",
      "description": "32-bit address in network byte order; zero for invalid input."
    }
  ],
  "initial_state": "ipValue = 0；解析状态机处于等待第 1 段。",
  "constraints": [
    "K1 输入必须是四段、段间以点分隔、每段非空且全部为十进制数字。",
    "K2 每段数值必须在 0—255 之间（含端点）。",
    "K3 按网络字节序组装：第 1 段占最高 8 位，第 4 段占最低 8 位。",
    "K4 段数不对、含非数字字符、任一段越界时一律输出 ipValue = 0；合法地址 0.0.0.0 也输出 0，本接口不要求区分两种情况。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P14
# meta: medium / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
#
# note: 本题是纯组合逻辑（输入字符串 → 输出整数），不含状态与时序。规约层只能约束值域与上电初值；分段合法性、越界判定等语义正确性由 tests/cases/P14.csv 逐条覆盖，不强行凑成恒真条款。

C2: G(ipValue <= 16#FFFFFFFF)    -- 输出必须落在 32 位无符号整数域内（不得溢出）（K3）
C10: G[0,0](ipValue == 0)    -- 上电当拍输出 0（初态）

实现说明与冲突报告：
1. C10 要求首次扫描输出 0，而纯组合解析要求首次扫描也输出
   当前输入的解析值；当首次输入为合法非零地址时，两者冲突。
   本实现优先满足明确的 C10：首次调用输出 0，从第二次调用开始，
   每次调用均完整解析当前输入，不跨扫描保存解析进度。
2. 接口说明中的“合法地址最多 15 字符”未覆盖带前导零的表示。
   K1、K2 未限制每段字符数，因此本实现允许前导零，不以 15 字符
   为拒绝条件；只检查四段、数字字符、非空和数值范围。
3. 每次扫描先清零输出，只有全部检查成功才提交网络字节序结果。
   段值超过 255 时立即终止，避免长数字串造成算术溢出。
4. 当前对话未提供可执行的测试环境、编译 profile 或测试命令，
   未运行编译或逐周期测试，不声称已验证编译或功能正确。
*)

FUNCTION_BLOCK FB_P14
VAR_INPUT
    ipText : STRING(254);
END_VAR
VAR_OUTPUT
    ipValue : UDINT := UDINT#0;
END_VAR
VAR
    firstScan : BOOL := TRUE;
    textLength : INT := 0;
    position : INT := 0;
    character : STRING(1) := '';
    digitPosition : INT := 0;
    digitValue : UDINT := UDINT#0;
    segmentNumber : INT := 1;
    segmentValue : UDINT := UDINT#0;
    segmentHasDigit : BOOL := FALSE;
    assembledValue : UDINT := UDINT#0;
    validInput : BOOL := FALSE;
END_VAR

(* 每拍从等待第 1 段开始，不使用上一拍的解析结果。 *)
ipValue := UDINT#0;
textLength := 0;
position := 0;
character := '';
digitPosition := 0;
digitValue := UDINT#0;
segmentNumber := 1;
segmentValue := UDINT#0;
segmentHasDigit := FALSE;
assembledValue := UDINT#0;
validInput := FALSE;

IF firstScan THEN
    (* 上电当拍满足 C10。 *)
    firstScan := FALSE;
ELSE
    textLength := LEN(ipText);
    validInput := textLength > 0;

    IF validInput THEN
        FOR position := 1 TO textLength DO
            character := MID(ipText, 1, position);

            IF character = '.' THEN
                IF (NOT segmentHasDigit) OR (segmentNumber >= 4) THEN
                    validInput := FALSE;
                    EXIT;
                END_IF;

                assembledValue :=
                    assembledValue * UDINT#256 + segmentValue;
                segmentNumber := segmentNumber + 1;
                segmentValue := UDINT#0;
                segmentHasDigit := FALSE;
            ELSE
                (* FIND 返回 1 至 10 表示数字，0 表示非数字。 *)
                digitPosition := FIND('0123456789', character);

                IF digitPosition = 0 THEN
                    validInput := FALSE;
                    EXIT;
                END_IF;

                digitValue := INT_TO_UDINT(digitPosition - 1);
                segmentValue :=
                    segmentValue * UDINT#10 + digitValue;
                segmentHasDigit := TRUE;

                IF segmentValue > UDINT#255 THEN
                    validInput := FALSE;
                    EXIT;
                END_IF;
            END_IF;
        END_FOR;
    END_IF;

    IF validInput AND (segmentNumber = 4) AND segmentHasDigit THEN
        (* 此处最多为 16#FFFFFFFF，不发生 UDINT 溢出。 *)
        ipValue := assembledValue * UDINT#256 + segmentValue;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
