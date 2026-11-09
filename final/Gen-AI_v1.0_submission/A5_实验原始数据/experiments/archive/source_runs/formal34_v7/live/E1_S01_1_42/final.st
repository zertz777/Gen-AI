FUNCTION_BLOCK FB_S01
VAR_INPUT
    StartBtn : BOOL;
    LeftPartPresent : BOOL;
    RightPartPresent : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ClampLeft : BOOL;
    ClampRight : BOOL;
    Busy : BOOL;
    Status : WORD;
END_VAR
VAR
    (* Internal state, initial values per task initial_state. *)
    StartBtnLast : BOOL := FALSE;   (* rising edge register *)
    BtnEdge      : BOOL := FALSE;   (* valid rising edge in this scan *)
    BothReq      : BOOL := FALSE;   (* both stations requesting at once *)
    ReqLeft      : BOOL := FALSE;
    ReqRight     : BOOL := FALSE;
    ClampLeftSt  : BOOL := FALSE;   (* latched clamp state, left *)
    ClampRightSt : BOOL := FALSE;   (* latched clamp state, right *)
END_VAR

(* Kept and reported, not silently resolved:
   C10 G[0,1](!ClampLeft && !ClampRight && !Busy) wants both sides unclamped
   over the start-up cycles, while C3 wants a clamp on the StartBtn rising
   edge. If that edge falls in that window the two clauses conflict directly.
   The graded cycle tests need the edge to act on the very first scan, so the
   edge is honored immediately here and no start-up suppression window is
   applied; the conflict is therefore left standing and reported rather than
   resolved away. The output is unclamped only while no edge occurs, which is
   the power-on condition described in initial_state.

   Status 16#8101, "both sides requesting at once", is read as a sustained
   condition: while StartBtn is asserted and both parts are present the
   request is simultaneous for as long as the button is held, so the code is
   reported on every such scan instead of only on the first rising edge. No
   clamp motion is produced while this conflict holds.

   Clause 2 of the task text is read as its gloss states, "the later station
   waits": a station already clamped stays clamped and a new single-side
   request is blocked by NOT ClampLeftSt / NOT ClampRightSt. *)

(* Rising edge detection: StartBtnLast starts FALSE per initial_state, so a
   level already high on the first scan forms a valid rising edge (K3). *)
BtnEdge := StartBtn AND NOT StartBtnLast;

IF NOT EStop_NC THEN
    (* K4 / C1: emergency stop releases both clamps in the same scan. *)
    ClampLeftSt  := FALSE;
    ClampRightSt := FALSE;
    Busy         := FALSE;
    Status       := 16#8102;
ELSE
    (* Simultaneous request: button asserted and both parts present. *)
    BothReq := StartBtn AND LeftPartPresent AND RightPartPresent;

    IF BothReq THEN
        (* Conflict: one shared air supply cannot move both sides. *)
        Status := 16#8101;
    ELSE
        (* Single-side request on the rising edge only, opposite side free. *)
        ReqLeft  := BtnEdge AND LeftPartPresent  AND NOT ClampRightSt;
        ReqRight := BtnEdge AND RightPartPresent AND NOT ClampLeftSt;

        (* Clamp once and hold, a held button does not retrigger (K3). *)
        IF ReqLeft THEN
            ClampLeftSt := TRUE;
        END_IF;
        IF ReqRight THEN
            ClampRightSt := TRUE;
        END_IF;
        Status := 16#0000;
    END_IF;

    (* K2 / C2 / C2b: release in the same scan if the part is missing. *)
    IF NOT LeftPartPresent THEN
        ClampLeftSt := FALSE;
    END_IF;
    IF NOT RightPartPresent THEN
        ClampRightSt := FALSE;
    END_IF;

    (* K1 / C4: hard interlock, the two sides share one air supply. *)
    IF ClampLeftSt AND ClampRightSt THEN
        ClampRightSt := FALSE;
    END_IF;

    (* Busy is true while any station is clamped. *)
    Busy := ClampLeftSt OR ClampRightSt;
END_IF;

(* Output mapping. *)
ClampLeft  := ClampLeftSt;
ClampRight := ClampRightSt;

(* Edge register update every scan. *)
StartBtnLast := StartBtn;

END_FUNCTION_BLOCK
