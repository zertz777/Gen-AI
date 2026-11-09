FUNCTION_BLOCK FB_S08
VAR_INPUT
    RecipeSelect : INT;
    ChangeoverReq : BOOL;
    PartHeight : REAL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ActiveRecipe : INT;
    SortLeft : BOOL;
    SortRight : BOOL;
    Busy : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(*  *)
