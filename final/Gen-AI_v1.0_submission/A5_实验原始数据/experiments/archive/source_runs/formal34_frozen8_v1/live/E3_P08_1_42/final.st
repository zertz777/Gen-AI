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
    firstScan : BOOL := TRUE;
    i : DINT;
    n : DINT;
    nA : DINT;
    nC : DINT;
    maxCount : DINT;
    lowerA : DINT;
    lowerC : DINT;
    idxA : DINT;
    idxC : DINT;
    raw : INT;
    tempOut : REAL;
    mode : INT;
    hi : REAL;
    lo : REAL;
    bip : BOOL;
    en : BOOL;
END_VAR

(* Conflict note: C10 requires first-scan outputValue = 0.0, while the initial-state text
   says retVal/outputValue are recomputed from current inputs on every call.  This
   implementation satisfies C10 by forcing outputValue to 0.0 on the first call only;
   retVal is still computed according to the current inputs. *)

lowerA := LOWER_BOUND(analogValues, 1);
lowerC := LOWER_BOUND(channels, 1);
nA := UPPER_BOUND(analogValues, 1) - lowerA + 1;
nC := UPPER_BOUND(channels, 1) - lowerC + 1;

maxCount := nA;
IF nC < maxCount THEN
    maxCount := nC;
END_IF;

IF count < 0 THEN
    n := 0;
ELSIF count > maxCount THEN
    n := maxCount;
ELSE
    n := count;
END_IF;

FOR i := 0 TO n - 1 DO
    idxA := lowerA + i;
    idxC := lowerC + i;

    en := channels[idxC].enable;
    IF NOT en THEN
        channels[idxC].retVal := 0;
        tempOut := 0.0;
    ELSE
        mode := channels[idxC].measuringMode;
        IF (mode <> 0) AND (mode <> 1) AND (mode <> 2) THEN
            channels[idxC].retVal := 16#8001;
            tempOut := 0.0;
        ELSE
            hi := channels[idxC].hiLIM;
            lo := channels[idxC].loLIM;
            IF hi <= lo THEN
                channels[idxC].retVal := 16#8002;
                tempOut := 0.0;
            ELSE
                channels[idxC].retVal := 0;
                raw := analogValues[idxA];
                CASE mode OF
                    0:
                        bip := channels[idxC].bipolar;
                        IF bip THEN
                            tempOut := lo + (INT_TO_REAL(raw) + 27648.0) * (hi - lo) / 55296.0;
                        ELSE
                            tempOut := lo + INT_TO_REAL(raw) * (hi - lo) / 27648.0;
                        END_IF;
                    1:
                        tempOut := INT_TO_REAL(raw) / 10.0;
                    2:
                        tempOut := INT_TO_REAL(raw) / 100.0;
                END_CASE;
            END_IF;
        END_IF;
    END_IF;

    IF firstScan THEN
        tempOut := 0.0;
    END_IF;

    channels[idxC].outputValue := tempOut;
END_FOR;

firstScan := FALSE;

END_FUNCTION_BLOCK
