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
    analogLower : DINT;
    channelLower : DINT;
    analogLength : LINT;
    channelLength : LINT;
    processCount : LINT;
    ordinal : LINT;
    analogIndex : DINT;
    channelIndex : DINT;
    rawValue : REAL;
    fraction : REAL;
END_VAR

(*
    Requires a compilation profile supporting ARRAY[*] in VAR_IN_OUT,
    LOWER_BOUND, UPPER_BOUND and LINT arithmetic.
    Compilation and scan-by-scan behavior have not been verified.

    Unresolved specification conflict:
    C10 requires zero output on the first scan, whereas the stated initial
    behavior requires conversion from current inputs on every invocation.
    Also, count = 0 forbids channel processing, so zeroing all channels to
    enforce globally quantified C1/C6/C10 would violate K1.
    This implementation follows current-input recomputation for the selected
    prefix only. It does not add an unspecified startup suppression scan;
    unconditional C10 and guarantees for unprocessed channels require review.
*)

analogLower := LOWER_BOUND(analogValues, 1);
channelLower := LOWER_BOUND(channels, 1);

analogLength :=
    DINT_TO_LINT(UPPER_BOUND(analogValues, 1))
    - DINT_TO_LINT(analogLower) + LINT#1;
channelLength :=
    DINT_TO_LINT(UPPER_BOUND(channels, 1))
    - DINT_TO_LINT(channelLower) + LINT#1;

(* Defensive bounds handling; valid callers already satisfy these bounds. *)
processCount := DINT_TO_LINT(count);
IF processCount < LINT#0 THEN
    processCount := LINT#0;
END_IF;
IF processCount > analogLength THEN
    processCount := analogLength;
END_IF;
IF processCount > channelLength THEN
    processCount := channelLength;
END_IF;

ordinal := LINT#0;
WHILE ordinal < processCount DO
    analogIndex :=
        LINT_TO_DINT(DINT_TO_LINT(analogLower) + ordinal);
    channelIndex :=
        LINT_TO_DINT(DINT_TO_LINT(channelLower) + ordinal);

    channels[channelIndex].retVal := WORD#16#0000;
    channels[channelIndex].outputValue := REAL#0.0;

    IF channels[channelIndex].enable THEN
        (* Invalid mode takes precedence if both configuration errors exist. *)
        IF (channels[channelIndex].measuringMode < INT#0)
            OR (channels[channelIndex].measuringMode > INT#2) THEN
            channels[channelIndex].retVal := WORD#16#8001;

        ELSIF channels[channelIndex].hiLIM
            <= channels[channelIndex].loLIM THEN
            channels[channelIndex].retVal := WORD#16#8002;

        ELSE
            rawValue := INT_TO_REAL(analogValues[analogIndex]);

            CASE channels[channelIndex].measuringMode OF
                0:
                    IF channels[channelIndex].bipolar THEN
                        fraction :=
                            (rawValue + REAL#27648.0) / REAL#55296.0;
                    ELSE
                        fraction := rawValue / REAL#27648.0;
                    END_IF;

                    (* No raw-value clamping is specified. *)
                    channels[channelIndex].outputValue :=
                        channels[channelIndex].loLIM
                        + fraction
                        * (channels[channelIndex].hiLIM
                           - channels[channelIndex].loLIM);

                1:
                    channels[channelIndex].outputValue :=
                        rawValue / REAL#10.0;

                2:
                    channels[channelIndex].outputValue :=
                        rawValue / REAL#100.0;
            END_CASE;
        END_IF;
    END_IF;

    ordinal := ordinal + LINT#1;
END_WHILE;

END_FUNCTION_BLOCK
