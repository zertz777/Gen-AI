TYPE ST_AnalogChannel :
STRUCT
    enable : BOOL;
    hiLIM : REAL;
    loLIM : REAL;
    bipolar : BOOL;
    measuringMode : INT;
    retVal : WORD;
    outputValue : REAL;
END_STRUCT
END_TYPE

FUNCTION_BLOCK FB_P08
VAR_INPUT
    count : DINT;
END_VAR
VAR_IN_OUT
    analogValues : ARRAY[*] OF INT;
    channels : ARRAY[*] OF ST_AnalogChannel;
END_VAR
VAR
    i : DINT;
    n : DINT;
    aLo : DINT;
    aHi : DINT;
    cLo : DINT;
    cHi : DINT;
    aLen : DINT;
    cLen : DINT;
    chIdx : DINT;
    avIdx : DINT;
    rawReal : REAL;
    tmpOut : REAL;
    zeroOut : BOOL;
    firstScan : BOOL := TRUE;
END_VAR

(* K1: 以两个数组各自的下界为基准，确定本次可处理通道数 *)
aLo := LOWER_BOUND(analogValues, 1);
aHi := UPPER_BOUND(analogValues, 1);
cLo := LOWER_BOUND(channels, 1);
cHi := UPPER_BOUND(channels, 1);

aLen := aHi - aLo + 1;
cLen := cHi - cLo + 1;

IF aLen < cLen THEN
    n := aLen;
ELSE
    n := cLen;
END_IF;

IF count < n THEN
    n := count;
END_IF;

IF n < 0 THEN
    n := 0;
END_IF;

(* C10: 上电当拍不输出工程量 *)
IF firstScan THEN
    zeroOut := TRUE;
    firstScan := FALSE;
ELSE
    zeroOut := FALSE;
END_IF;

FOR i := 0 TO n - 1 DO
    chIdx := cLo + i;
    avIdx := aLo + i;

    tmpOut := 0.0;

    IF NOT channels[chIdx].enable THEN
        (* C1: 未使能通道安全默认，不输出非零工程量 *)
        channels[chIdx].retVal := 16#0000;
    ELSIF (channels[chIdx].measuringMode < 0) OR (channels[chIdx].measuringMode > 2) THEN
        (* K5 / 条款6: 非法模式仅跳过当前通道 *)
        channels[chIdx].retVal := 16#8001;
    ELSIF channels[chIdx].hiLIM <= channels[chIdx].loLIM THEN
        (* K5 / 条款7: 上下限错误仅跳过当前通道 *)
        channels[chIdx].retVal := 16#8002;
    ELSE
        rawReal := INT_TO_REAL(analogValues[avIdx]);

        CASE channels[chIdx].measuringMode OF
            0:
                (* K3: 非温度线性标定 *)
                IF channels[chIdx].bipolar THEN
                    tmpOut := ((rawReal + 27648.0) / 55296.0)
                              * (channels[chIdx].hiLIM - channels[chIdx].loLIM)
                              + channels[chIdx].loLIM;
                ELSE
                    tmpOut := (rawReal / 27648.0)
                              * (channels[chIdx].hiLIM - channels[chIdx].loLIM)
                              + channels[chIdx].loLIM;
                END_IF;
            1:
                (* K4: 标准温度，1/10 *)
                tmpOut := rawReal / 10.0;
            2:
                (* K4: 气候温度，1/100 *)
                tmpOut := rawReal / 100.0;
        ELSE
            tmpOut := 0.0;
        END_CASE;

        channels[chIdx].retVal := 16#0000;
    END_IF;

    (* C6 / C10: 出错通道或上电当拍输出 0 *)
    IF zeroOut THEN
        channels[chIdx].outputValue := 0.0;
    ELSIF (channels[chIdx].retVal = 16#8001) OR (channels[chIdx].retVal = 16#8002) THEN
        channels[chIdx].outputValue := 0.0;
    ELSE
        channels[chIdx].outputValue := tmpOut;
    END_IF;
END_FOR;

END_FUNCTION_BLOCK
