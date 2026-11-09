FUNCTION_BLOCK FB_P14
VAR_INPUT
    ipText : STRING(254);
END_VAR
VAR_OUTPUT
    ipValue : UDINT := UDINT#0;
END_VAR
VAR
    firstScan : BOOL := TRUE;
    valid : BOOL;
    textLength : INT;
    index : INT;
    segmentCount : INT;
    digitCount : INT;
    digitPosition : INT;
    character : STRING(1);
    segmentValue : UDINT;
    assembledValue : UDINT;
END_VAR

(* C10 requires zero on the first scan, including for a valid input.
   Parsing is combinational on every subsequent scan. *)
ipValue := UDINT#0;

IF firstScan THEN
    firstScan := FALSE;
ELSE
    valid := TRUE;
    textLength := LEN(ipText);
    segmentCount := 1;
    digitCount := 0;
    segmentValue := UDINT#0;
    assembledValue := UDINT#0;

    IF textLength = 0 THEN
        valid := FALSE;
    END_IF;

    (* Do not impose a 15-character limit: the stated segment rules
       permit leading zeros, within the input string capacity. *)
    FOR index := 1 TO textLength DO
        IF valid THEN
            character := MID(ipText, 1, index);

            IF character = '.' THEN
                IF (digitCount = 0) OR (segmentCount >= 4) THEN
                    valid := FALSE;
                ELSE
                    assembledValue :=
                        assembledValue * UDINT#256 + segmentValue;
                    segmentCount := segmentCount + 1;
                    digitCount := 0;
                    segmentValue := UDINT#0;
                END_IF;
            ELSE
                IF character = '0' THEN
                    digitPosition := 1;
                ELSIF character = '1' THEN
                    digitPosition := 2;
                ELSIF character = '2' THEN
                    digitPosition := 3;
                ELSIF character = '3' THEN
                    digitPosition := 4;
                ELSIF character = '4' THEN
                    digitPosition := 5;
                ELSIF character = '5' THEN
                    digitPosition := 6;
                ELSIF character = '6' THEN
                    digitPosition := 7;
                ELSIF character = '7' THEN
                    digitPosition := 8;
                ELSIF character = '8' THEN
                    digitPosition := 9;
                ELSIF character = '9' THEN
                    digitPosition := 10;
                ELSE
                    digitPosition := 0;
                END_IF;

                IF digitPosition = 0 THEN
                    valid := FALSE;
                ELSE
                    (* The prior value is at most 255, so this
                       intermediate calculation cannot overflow. *)
                    segmentValue :=
                        segmentValue * UDINT#10
                        + INT_TO_UDINT(digitPosition - 1);
                    digitCount := digitCount + 1;

                    IF segmentValue > UDINT#255 THEN
                        valid := FALSE;
                    END_IF;
                END_IF;
            END_IF;
        END_IF;
    END_FOR;

    IF valid AND (segmentCount = 4) AND (digitCount > 0) THEN
        (* Three previously assembled bytes plus the final byte
           produce at most UDINT#16#FFFFFFFF. *)
        ipValue := assembledValue * UDINT#256 + segmentValue;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
