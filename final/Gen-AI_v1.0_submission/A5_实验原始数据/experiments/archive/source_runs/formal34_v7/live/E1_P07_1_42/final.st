TYPE ST_Pump :
STRUCT
    priority : INT;
    selection : BOOL;
    RunComd : BOOL;
END_STRUCT
END_TYPE
FUNCTION_BLOCK FB_P07
VAR_INPUT
    mode : BOOL;
    start : BOOL;
    stop : BOOL;
END_VAR
VAR_IN_OUT
    pumpGroup : ARRAY[1..5] OF ST_Pump;
END_VAR
VAR
    autoRun : BOOL;
    runMem : ARRAY[1..5] OF BOOL;
    selected : ARRAY[1..5] OF BOOL;
    i : INT;
    j : INT;
    betterCnt : INT;
END_VAR
(*
    语义冲突报告（保留，不自行消解）：
    - K2/K3：自动模式下同时运行泵数恰为 3，且按优先级（同优先级按泵号升序）确定运行组。
      但逐周期测试（P07-01 cycle5）要求自动模式在未投运（未施加 start）时三台泵均不上电，
      即自动组需 start 许可；这与“自动模式恒运行 3 台”不能同时严格成立。
      本实现保留 start 许可，并采用锁存 autoRun 以满足 C6“保持到 stop”。
    - K2/K3 要求自动下优先级变化时即时按新优先级重选 3 台；C6
      G(RunComd -> (RunComd W stop)) 要求已置位的 RunComd 保持到 stop 出现；
      当自动运行期间优先级变化时，二者不能同时严格成立。本实现保留 K2/K3 语义。
    - C10: G[0,1](!RunComd) 要求上电前两个扫描周期无运行命令；
      但逐周期测试在首个扫描周期即要求 RunComd 动作，二者不能同时严格成立。
      本实现以首个周期即参与计算为准。
    - C4 的 !(start && stop) 为外部/测试输入约束；若二者同时为 TRUE，本块按 stop 优先执行。
    - 手动模式：逐周期测试（P07-05：选择开关变化后输出仍保持先前的泵）表明，手动应由 start
      触发锁存选中泵（runMem）并保持到 stop，而非直接跟随 selection 电平；
      且未施加 start 时不投运（P07-01 cycle1 期望全停）。故手动采用 runMem 锁存语义。
    以上仅为逐周期测试可判定行为，编译通过不代表功能正确。
*)

IF stop THEN
    (* C1/C2/K4: 停止请求优先，当周期清除全部运行命令并复位各锁存 *)
    FOR i := 1 TO 5 DO
        pumpGroup[i].RunComd := FALSE;
        runMem[i] := FALSE;
    END_FOR;
    autoRun := FALSE;
ELSIF mode THEN
    (* 自动模式（K1）：以 start 作为自动组投运许可，锁存至 stop（C6） *)
    IF start THEN
        autoRun := TRUE;
    END_IF;
    IF autoRun THEN
        (* 按优先级选出 3 台运行（K2/K3），同优先级按泵号升序保证结果确定 *)
        FOR i := 1 TO 5 DO
            selected[i] := FALSE;
        END_FOR;
        FOR i := 1 TO 5 DO
            betterCnt := 0;
            FOR j := 1 TO 5 DO
                IF j <> i THEN
                    IF (pumpGroup[j].priority > pumpGroup[i].priority) OR
                       ((pumpGroup[j].priority = pumpGroup[i].priority) AND (j < i)) THEN
                        betterCnt := betterCnt + 1;
                    END_IF;
                END_IF;
            END_FOR;
            IF betterCnt < 3 THEN
                selected[i] := TRUE;
            END_IF;
        END_FOR;
        FOR i := 1 TO 5 DO
            pumpGroup[i].RunComd := selected[i];
        END_FOR;
    ELSE
        FOR i := 1 TO 5 DO
            pumpGroup[i].RunComd := FALSE;
        END_FOR;
    END_IF;
ELSE
    (* 手动模式（K1）：start 触发锁存被选中的单泵，保持到 stop；选择开关变化不改变在运泵 *)
    FOR i := 1 TO 5 DO
        IF start AND pumpGroup[i].selection THEN
            runMem[i] := TRUE;
        END_IF;
        pumpGroup[i].RunComd := runMem[i];
    END_FOR;
END_IF;

END_FUNCTION_BLOCK
