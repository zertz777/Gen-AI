FUNCTION_BLOCK FB_P14
VAR_INPUT
    ipText : STRING(254);
END_VAR
VAR_OUTPUT
    ipValue : UDINT;
END_VAR
VAR
    (* 内部中间量：全部显式声明，无动态内存、无文件/网络操作 *)
    i      : INT;       (* 字符下标（本运行环境为 0 基） *)
    c      : BYTE;      (* 当前字符编码 *)
    dig    : UDINT;     (* 当前字符对应的数字值 *)
    segIdx : INT;       (* 当前段序号 1..4 *)
    segVal : UDINT;     (* 当前段累计值 *)
    segLen : INT;       (* 当前段已读数字个数 *)
    tmp    : UDINT;     (* 越界保护用临时值 *)
    ok     : BOOL;      (* 合法性标志 *)
    part   : ARRAY[1..4] OF UDINT; (* 四段数值暂存 *)
END_VAR

(* ==================================================================
   纯组合逻辑：每个 20ms 扫描周期都从初值重新解析 ipText，
   不保留跨周期状态，故上电当拍 ipValue 为 0（C10）。
   不调用任何字符串库函数（LEN/MID/FIND 在本工程未定义）。
   注意：本运行环境的 STRING 下标为 0 基，故循环自 0 起。
   ================================================================== *)

ipValue := 0;

part[1] := 0;
part[2] := 0;
part[3] := 0;
part[4] := 0;

segIdx := 1;
segVal := 0;
segLen := 0;
ok     := TRUE;

FOR i := 0 TO 253 DO
    c := ipText[i];

    IF c = 0 THEN
        (* 字符串结束符；短于容量的位置均为 0 *)
        EXIT;
    END_IF;

    IF c = 46 THEN
        (* '.' 段分隔：校验前段非空并保存该段 *)
        IF segLen = 0 THEN
            ok := FALSE;              (* 空段 *)
        END_IF;

        IF segIdx <= 4 THEN
            part[segIdx] := segVal;
        ELSE
            ok := FALSE;              (* 段数超过 4 *)
        END_IF;

        segIdx := segIdx + 1;
        segVal := 0;
        segLen := 0;

    ELSIF (c >= 48) AND (c <= 57) THEN
        (* '0'..'9' *)
        segLen := segLen + 1;

        dig := BYTE_TO_UDINT(c) - 48;
        tmp := segVal * 10 + dig;

        IF tmp > 255 THEN
            ok := FALSE;              (* 段值越界；不再累加以避免溢出 *)
        ELSE
            segVal := tmp;
        END_IF;

    ELSE
        ok := FALSE;                  (* 含非数字字符 *)
    END_IF;
END_FOR;

(* 收尾：处理最后一段并校验段数恰为 4 *)
IF segLen = 0 THEN
    ok := FALSE;                      (* 末段为空或输入为空串 *)
END_IF;

IF segIdx <= 4 THEN
    part[segIdx] := segVal;
ELSE
    ok := FALSE;
END_IF;

IF segIdx <> 4 THEN
    ok := FALSE;                      (* 段数不等于 4 *)
END_IF;

(* 组装：网络字节序，第 1 段最高 8 位、第 4 段最低 8 位 *)
IF ok THEN
    ipValue := part[1] * 16777216
             + part[2] * 65536
             + part[3] * 256
             + part[4];
ELSE
    ipValue := 0;
END_IF;

END_FUNCTION_BLOCK
