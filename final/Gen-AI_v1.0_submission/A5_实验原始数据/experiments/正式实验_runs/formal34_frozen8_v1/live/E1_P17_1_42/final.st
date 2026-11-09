TYPE ST_Recipe :
STRUCT
    recipeID : INT;
    ingredientType : INT;
    ingredientRatio : REAL;
    productionTemperature : REAL;
END_STRUCT
END_TYPE
FUNCTION_BLOCK FB_P17
VAR_INPUT
    addRecipe : BOOL;
    deleteRecipe : BOOL;
    modifyRecipe : BOOL;
    queryRecipe : BOOL;
    recipeIn : ST_Recipe;
END_VAR
VAR_OUTPUT
    recipeAdded : BOOL;
    recipeDeleted : BOOL;
    recipeModified : BOOL;
    recipeQueryResult : ST_Recipe;
    error : BOOL;
    status : WORD;
END_VAR
VAR_IN_OUT
    recipe : ARRAY[1..10] OF ST_Recipe;
END_VAR
VAR
    i : INT;
    found : BOOL;
    slot : INT;
END_VAR

(* Success indicators are single-cycle pulses; error/status are held until the next request. *)
recipeAdded := FALSE;
recipeDeleted := FALSE;
recipeModified := FALSE;

(* Add: duplicate id -> 16#8002; full -> 16#8003; else write smallest empty slot. *)
IF addRecipe THEN
    error := FALSE;
    status := 16#0000;
    found := FALSE;
    FOR i := 1 TO 10 DO
        IF (recipe[i].recipeID <> 0) AND (recipe[i].recipeID = recipeIn.recipeID) THEN
            found := TRUE;
        END_IF
    END_FOR
    IF found THEN
        error := TRUE;
        status := 16#8002;
    ELSE
        slot := 0;
        FOR i := 1 TO 10 DO
            IF (recipe[i].recipeID = 0) AND (slot = 0) THEN
                slot := i;
            END_IF
        END_FOR
        IF slot = 0 THEN
            error := TRUE;
            status := 16#8003;
        ELSE
            recipe[slot] := recipeIn;
            recipeAdded := TRUE;
        END_IF
    END_IF

(* Delete: clear matching slot; not found -> 16#8004. *)
ELSIF deleteRecipe THEN
    error := FALSE;
    status := 16#0000;
    found := FALSE;
    FOR i := 1 TO 10 DO
        IF (recipe[i].recipeID <> 0) AND (recipe[i].recipeID = recipeIn.recipeID) THEN
            found := TRUE;
            recipe[i].recipeID := 0;
        END_IF
    END_FOR
    IF found THEN
        recipeDeleted := TRUE;
    ELSE
        error := TRUE;
        status := 16#8004;
    END_IF

(* Modify: replace matching slot; not found -> 16#8005. *)
ELSIF modifyRecipe THEN
    error := FALSE;
    status := 16#0000;
    found := FALSE;
    FOR i := 1 TO 10 DO
        IF (recipe[i].recipeID <> 0) AND (recipe[i].recipeID = recipeIn.recipeID) THEN
            found := TRUE;
            recipe[i] := recipeIn;
        END_IF
    END_FOR
    IF found THEN
        recipeModified := TRUE;
    ELSE
        error := TRUE;
        status := 16#8005;
    END_IF

(* Query: output matching recipe; not found -> 16#8001. *)
ELSIF queryRecipe THEN
    error := FALSE;
    status := 16#0000;
    found := FALSE;
    FOR i := 1 TO 10 DO
        IF (recipe[i].recipeID <> 0) AND (recipe[i].recipeID = recipeIn.recipeID) THEN
            found := TRUE;
            recipeQueryResult := recipe[i];
        END_IF
    END_FOR
    IF NOT found THEN
        error := TRUE;
        status := 16#8001;
    END_IF
END_IF

END_FUNCTION_BLOCK
