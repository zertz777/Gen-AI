FUNCTION_BLOCK FB_P14
VAR_INPUT
    ipText : STRING(254);
END_VAR
VAR_OUTPUT
    ipValue : UDINT;
END_VAR
VAR
    i : INT;
    len : INT;
    ch : STRING(1);
    valid : BOOL;
    segIndex : INT;
    digitCount : INT;
    segValue : UDINT;
    seg0 : UDINT;
    seg1 : UDINT;
    seg2 : UDINT;
    seg3 : UDINT;
    digit : UDINT;
    result : UDINT;
END_VAR

ipValue := UDINT#0;
valid := TRUE;
segIndex := 0;
digitCount := 0;
segValue := UDINT#0;
seg0 := UDINT#0;
seg1 := UDINT#0;
seg2 := UDINT#0;
seg3 := UDINT#0;
result := UDINT#0;

len := LEN(ipText);
i := 1;

WHILE (i <= len) AND valid DO
    ch := MID(ipText, 1, i);

    IF (ch = '0') OR (ch = '1') OR (ch = '2') OR (ch = '3') OR (ch = '4') OR
       (ch = '5') OR (ch = '6') OR (ch = '7') OR (ch = '8') OR (ch = '9') THEN
        digitCount := digitCount + 1;

        IF ch = '0' THEN
            digit := UDINT#0;
        ELSIF ch = '1' THEN
            digit := UDINT#1;
        ELSIF ch = '2' THEN
            digit := UDINT#2;
        ELSIF ch = '3' THEN
            digit := UDINT#3;
        ELSIF ch = '4' THEN
            digit := UDINT#4;
        ELSIF ch = '5' THEN
            digit := UDINT#5;
        ELSIF ch = '6' THEN
            digit := UDINT#6;
        ELSIF ch = '7' THEN
            digit := UDINT#7;
        ELSIF ch = '8' THEN
            digit := UDINT#8;
        ELSE
            digit := UDINT#9;
        END_IF;

        segValue := segValue * UDINT#10 + digit;
        IF segValue > UDINT#255 THEN
            valid := FALSE;
        END_IF;

    ELSIF ch = '.' THEN
        IF (digitCount = 0) OR (segIndex >= 3) THEN
            valid := FALSE;
        ELSE
            CASE segIndex OF
                0: seg0 := segValue;
                1: seg1 := segValue;
                2: seg2 := segValue;
            END_CASE;
            segIndex := segIndex + 1;
            segValue := UDINT#0;
            digitCount := 0;
        END_IF;

    ELSE
        valid := FALSE;
    END_IF;

    i := i + 1;
END_WHILE;

IF valid THEN
    IF (digitCount = 0) OR (segIndex <> 3) THEN
        valid := FALSE;
    ELSE
        seg3 := segValue;
        result := seg0 * UDINT#16777216 +
                  seg1 * UDINT#65536 +
                  seg2 * UDINT#256 +
                  seg3;
    END_IF;
END_IF;

IF valid THEN
    ipValue := result;
ELSE
    ipValue := UDINT#0;
END_IF;

END_FUNCTION_BLOCK
