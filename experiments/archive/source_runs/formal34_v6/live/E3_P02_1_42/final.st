FUNCTION_BLOCK FB_P02
VAR_INPUT
    value : DWORD;
END_VAR
VAR_OUTPUT
    hasChanged : BOOL := FALSE;
    hasRisingEdges : BOOL := FALSE;
    risingBits : DWORD := 16#00000000;
    noOfRisingBits : USINT := 0;
    hasFallingEdges : BOOL := FALSE;
    fallingBits : DWORD := 16#00000000;
    noOfFallingBits : USINT := 0;
END_VAR
VAR
    lastValue : DWORD := 16#00000000;
    initialized : BOOL := FALSE;
    tempR : DWORD;
    tempF : DWORD;
    i : INT;
END_VAR

(*
    NOTE: LTL clause C7 as given appears overly restrictive:
    G(!hasChanged -> X(!hasRisingEdges && !hasFallingEdges))
    would forbid any edge detection immediately after a no-change cycle,
    which conflicts with standard edge detection behavior.
    This implementation follows the I/O semantics and K1-K4.
    The conflict is preserved and reported here as required.
*)

IF NOT initialized THEN
    (* First scan cycle: no previous value to compare. K4, C10. *)
    lastValue := value;
    initialized := TRUE;
    hasChanged := FALSE;
    hasRisingEdges := FALSE;
    risingBits := 16#00000000;
    noOfRisingBits := 0;
    hasFallingEdges := FALSE;
    fallingBits := 16#00000000;
    noOfFallingBits := 0;
ELSE
    (* Compute edges: rising = current 1 where previous 0; falling = current 0 where previous 1. K1, K2. *)
    risingBits := value AND NOT lastValue;
    fallingBits := (NOT value) AND lastValue;

    hasRisingEdges := (risingBits <> 16#00000000);
    hasFallingEdges := (fallingBits <> 16#00000000);
    hasChanged := hasRisingEdges OR hasFallingEdges;

    (* Count set bits in risingBits and fallingBits. K3. *)
    noOfRisingBits := 0;
    noOfFallingBits := 0;
    tempR := risingBits;
    tempF := fallingBits;
    FOR i := 0 TO 31 DO
        IF (tempR AND 16#00000001) <> 0 THEN
            noOfRisingBits := noOfRisingBits + 1;
        END_IF;
        IF (tempF AND 16#00000001) <> 0 THEN
            noOfFallingBits := noOfFallingBits + 1;
        END_IF;
        tempR := SHR(tempR, 1);
        tempF := SHR(tempF, 1);
    END_FOR;

    (* Update lastValue for next cycle. *)
    lastValue := value;
END_IF;

END_FUNCTION_BLOCK
